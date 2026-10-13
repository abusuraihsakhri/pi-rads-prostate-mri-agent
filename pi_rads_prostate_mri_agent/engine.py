"""
PI-RADS v2.1 Engine: Prostate Imaging Reporting and Data System scoring.

Implements PI-RADS v2.1 assessment for multiparametric prostate MRI.

Scoring per zone:
  - Peripheral Zone (PZ): DWI is primary, DCE is secondary
  - Transition Zone (TZ): T2W is primary, DWI is secondary

Score interpretation:
  1: Very low (clinically significant cancer highly unlikely)
  2: Low (clinically significant cancer unlikely)
  3: Intermediate (clinically significant cancer equivocal)
  4: High (clinically significant cancer likely)
  5: Very high (clinically significant cancer highly likely)

Key rules:
  - PZ: DWI score determines PI-RADS. DCE positivity upgrades score 3 to 4.
  - TZ: T2W 2 + DWI 4-5 becomes 3; T2W 3 + DWI 5 becomes 4.
  - PI-RADS does not independently determine biopsy management.

Reference: ACR PI-RADS v2.1
"""
from typing import Any, Dict, List, Optional
from .models import (
    ProstateZone, ProstateLesion, PIRADSResult, PIRADSAssessment,
    PIRADSScore,
)

# Clinical significance descriptions per score
_SCORE_DESCRIPTIONS = {
    1: "Very low - clinically significant cancer is highly unlikely",
    2: "Low - clinically significant cancer is unlikely",
    3: "Intermediate - clinically significant cancer is equivocal",
    4: "High - clinically significant cancer is likely",
    5: "Very high - clinically significant cancer is highly likely",
}


def _clamp_score(score: int) -> int:
    """Clamp a score to 1-5 range."""
    return max(1, min(5, score))


def score_peripheral_zone(lesion: ProstateLesion) -> PIRADSResult:
    """
    Score a lesion in the Peripheral Zone using PI-RADS v2.1 rules.

    In PZ: DWI is the primary determining sequence.
    DCE is secondary: positive DCE upgrades PI-RADS 3 to 4.
    """
    if lesion.zone != ProstateZone.PERIPHERAL:
        raise ValueError("Peripheral-zone scoring requires a peripheral-zone lesion")
    errors = lesion.validate()
    if errors:
        raise ValueError(f"Invalid lesion data: {'; '.join(errors)}")

    dwi = _clamp_score(lesion.dwi_score)
    t2w = _clamp_score(lesion.t2w_score)
    dce_pos = lesion.dce_positive
    notes: List[str] = []

    # Primary: DWI score determines PI-RADS
    pirads = dwi
    dce_upgrade = False

    # DCE upgrade rule: DCE positivity upgrades score 3 to 4
    if pirads == 3 and dce_pos:
        pirads = 4
        dce_upgrade = True
        notes.append("DCE positivity upgraded PI-RADS from 3 to 4.")

    # Special case: DWI score 3 with DCE negative stays 3
    if dwi == 3 and not dce_pos:
        notes.append("DWI score 3 with DCE negative: PI-RADS remains 3.")

    # Legacy boolean reports when biopsy should be considered, not a directive.
    # PI-RADS 3 decisions depend on clinical context and are not automatic.
    biopsy_rec = pirads >= 4
    if pirads >= 3:
        notes.append("Biopsy decisions require clinical risk assessment; PI-RADS alone is not a management recommendation.")

    return PIRADSResult(
        lesion_id=lesion.lesion_id,
        zone=lesion.zone,
        t2w_score=t2w,
        dwi_score=dwi,
        dce_positive=dce_pos,
        pirads_score=pirads,
        primary_sequence="DWI",
        secondary_sequence="DCE",
        dce_upgrade_applied=dce_upgrade,
        size_mm=lesion.size_mm,
        location=lesion.location,
        biopsy_recommended=biopsy_rec,
        clinical_significance=_SCORE_DESCRIPTIONS.get(pirads, ""),
        notes=notes,
    )


def score_transition_zone(lesion: ProstateLesion) -> PIRADSResult:
    """
    Score a lesion in the Transition Zone using PI-RADS v2.1 rules.

    In TZ: T2W is the primary determining sequence.
    T2W 2 with DWI 4-5 becomes PI-RADS 3.
    T2W 3 with DWI 5 becomes PI-RADS 4; DWI 4 stays PI-RADS 3.
    """
    if lesion.zone != ProstateZone.TRANSITION:
        raise ValueError("Transition-zone scoring requires a transition-zone lesion")
    errors = lesion.validate()
    if errors:
        raise ValueError(f"Invalid lesion data: {'; '.join(errors)}")

    t2w = _clamp_score(lesion.t2w_score)
    dwi = _clamp_score(lesion.dwi_score)
    notes: List[str] = []

    # Primary: T2W score determines PI-RADS
    pirads = t2w
    dce_upgrade = False

    if t2w == 2 and dwi >= 4:
        pirads = 3
        notes.append(f"DWI score {dwi} upgraded T2W 2 to PI-RADS 3.")
    elif t2w == 3 and dwi == 5:
        pirads = 4
        notes.append("DWI score 5 upgraded T2W 3 to PI-RADS 4.")

    # Clinical management is not prescribed by PI-RADS.
    biopsy_rec = pirads >= 4
    if pirads >= 3:
        notes.append("Biopsy decisions require clinical risk assessment; PI-RADS alone is not a management recommendation.")

    return PIRADSResult(
        lesion_id=lesion.lesion_id,
        zone=lesion.zone,
        t2w_score=t2w,
        dwi_score=dwi,
        dce_positive=lesion.dce_positive,
        pirads_score=pirads,
        primary_sequence="T2W",
        secondary_sequence="DWI",
        dce_upgrade_applied=dce_upgrade,
        size_mm=lesion.size_mm,
        location=lesion.location,
        biopsy_recommended=biopsy_rec,
        clinical_significance=_SCORE_DESCRIPTIONS.get(pirads, ""),
        notes=notes,
    )


def score_lesion(lesion: ProstateLesion) -> PIRADSResult:
    """
    Score a prostate lesion based on its zone.

    Routes to PZ or TZ scoring based on lesion.zone.
    Non-PZ/TZ regions require expert interpretation; TZ rules must not be
    silently extrapolated to the central zone or anterior fibromuscular stroma.
    """
    if lesion.zone in (ProstateZone.PERIPHERAL,):
        return score_peripheral_zone(lesion)
    elif lesion.zone == ProstateZone.TRANSITION:
        return score_transition_zone(lesion)
    raise ValueError(f"Automated PI-RADS combination is supported for peripheral and transition zones only; got {lesion.zone}")


def assess_patient(lesions: List[ProstateLesion]) -> PIRADSAssessment:
    """
    Perform a complete PI-RADS assessment for a patient.

    Evaluates each lesion individually and returns the overall assessment
    with the highest PI-RADS score and biopsy recommendations.
    """
    results: List[PIRADSResult] = []
    overall_notes: List[str] = []

    for lesion in lesions:
        result = score_lesion(lesion)
        results.append(result)

    if not results:
        overall_notes.append("No lesions identified.")

    return PIRADSAssessment(
        lesions=results,
        overall_notes=overall_notes,
    )


# ── Clinical Domain Engine ─────────────────────────────────────────

class ClinicalDomainEngine:
    """
    Clinical domain evaluation engine for agent-based case assessment.

    Provides evaluation methods for primary metrics, secondary kinetics,
    and biomarker concordance checks.
    """

    @staticmethod
    def evaluate_primary_index(metric: float) -> Optional[Dict[str, str]]:
        """Evaluate primary metric against clinical thresholds."""
        if metric > 25.0:
            return {
                "title": "Primary Metric Threshold Exceeded",
                "finding": f"Primary measurement ({metric:.2f}) exceeds upper reference limit (25.00).",
                "recommendation": "Review this nonvalidated demonstration threshold; do not use it for clinical management.",
            }
        return None

    @staticmethod
    def evaluate_secondary_kinetics(metric: float, is_stat: bool) -> Optional[Dict[str, str]]:
        """Evaluate secondary metric with STAT priority awareness."""
        if is_stat or metric > 12.0:
            return {
                "title": "Secondary Kinetics Escalation",
                "finding": f"CriticalFlag={is_stat} with secondary index {metric:.2f}.",
                "recommendation": "This is a demonstration-only flag, not an evidence-based clinical escalation.",
            }
        return None

    @staticmethod
    def evaluate_biomarker_concordance(status_flag: str, biomarkers: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check biomarker concordance and status flag for discordance."""
        flag_upper = str(status_flag).upper()
        if "DISCORDANT" in flag_upper or "SUSPICIOUS" in flag_upper:
            return {
                "title": "Biomarker Discordance Detected",
                "finding": f"Status flag '{status_flag}' indicates discordance with expected protocol.",
                "recommendation": "Check the demonstration input descriptor; no clinical inference is established.",
            }
        return None
