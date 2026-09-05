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
  - TZ: T2W score determines PI-RADS. DWI score 4-5 upgrades T2W score 3 to 4.
  - Biopsy recommended for PI-RADS >= 3.

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

    biopsy_rec = pirads >= 3

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
    DWI is secondary: DWI score 4-5 upgrades T2W score 3 to 4.
    """
    errors = lesion.validate()
    if errors:
        raise ValueError(f"Invalid lesion data: {'; '.join(errors)}")

    t2w = _clamp_score(lesion.t2w_score)
    dwi = _clamp_score(lesion.dwi_score)
    notes: List[str] = []

    # Primary: T2W score determines PI-RADS
    pirads = t2w
    dce_upgrade = False

    # DWI upgrade rule: DWI score 4 or 5 upgrades T2W score 3 to 4
    if pirads == 3 and dwi >= 4:
        pirads = 4
        notes.append(f"DWI score {dwi} upgraded PI-RADS from 3 to 4.")

    biopsy_rec = pirads >= 3

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
    Anterior fibromuscular and central zones use TZ rules.
    """
    if lesion.zone in (ProstateZone.PERIPHERAL,):
        return score_peripheral_zone(lesion)
    elif lesion.zone in (ProstateZone.TRANSITION, ProstateZone.ANTERIOR_FIBROMUSCULAR, ProstateZone.CENTRAL):
        return score_transition_zone(lesion)
    else:
        raise ValueError(f"Unknown zone: {lesion.zone}")


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
                "recommendation": "Initiate recalibration workflow and review secondary parameters.",
            }
        return None

    @staticmethod
    def evaluate_secondary_kinetics(metric: float, is_stat: bool) -> Optional[Dict[str, str]]:
        """Evaluate secondary metric with STAT priority awareness."""
        if is_stat or metric > 12.0:
            return {
                "title": "Secondary Kinetics Escalation",
                "finding": f"CriticalFlag={is_stat} with secondary index {metric:.2f}.",
                "recommendation": "Execute immediate closed-loop escalation and notify attending supervisor.",
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
                "recommendation": "Reconcile correlative findings with secondary confirmatory testing.",
            }
        return None
