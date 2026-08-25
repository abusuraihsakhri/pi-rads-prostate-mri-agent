"""
Tests for PI-RADS v2.1 prostate MRI scoring engine.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pi_rads_prostate_mri_agent.models import (
    ProstateZone, ProstateLesion, PIRADSResult, PIRADSAssessment,
)
from pi_rads_prostate_mri_agent.engine import (
    score_lesion, score_peripheral_zone, score_transition_zone, assess_patient,
)
from cli import main as cli_main


# ── Peripheral Zone Tests ───────────────────────────────────────────

class TestPeripheralZone:
    def test_pz_dwi_1_is_pirads_1(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=2, dwi_score=1)
        r = score_peripheral_zone(lesion)
        assert r.pirads_score == 1

    def test_pz_dwi_2_is_pirads_2(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=3, dwi_score=2)
        r = score_peripheral_zone(lesion)
        assert r.pirads_score == 2

    def test_pz_dwi_3_dce_neg_is_pirads_3(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=3, dwi_score=3, dce_positive=False)
        r = score_peripheral_zone(lesion)
        assert r.pirads_score == 3
        assert not r.dce_upgrade_applied

    def test_pz_dwi_3_dce_pos_upgrades_to_4(self):
        """DCE positivity upgrades PZ score 3 to 4."""
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=3, dwi_score=3, dce_positive=True)
        r = score_peripheral_zone(lesion)
        assert r.pirads_score == 4
        assert r.dce_upgrade_applied

    def test_pz_dwi_4_is_pirads_4(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=4, dwi_score=4)
        r = score_peripheral_zone(lesion)
        assert r.pirads_score == 4

    def test_pz_dwi_5_is_pirads_5(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=5, dwi_score=5)
        r = score_peripheral_zone(lesion)
        assert r.pirads_score == 5

    def test_pz_primary_is_dwi(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=2, dwi_score=4)
        r = score_peripheral_zone(lesion)
        assert r.primary_sequence == "DWI"
        assert r.secondary_sequence == "DCE"

    def test_pz_dwi_4_dce_pos_stays_4(self):
        """DCE upgrade only applies to score 3, not 4."""
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=4, dwi_score=4, dce_positive=True)
        r = score_peripheral_zone(lesion)
        assert r.pirads_score == 4
        assert not r.dce_upgrade_applied


# ── Transition Zone Tests ───────────────────────────────────────────

class TestTransitionZone:
    def test_tz_t2w_1_is_pirads_1(self):
        lesion = ProstateLesion("L1", ProstateZone.TRANSITION, t2w_score=1, dwi_score=3)
        r = score_transition_zone(lesion)
        assert r.pirads_score == 1

    def test_tz_t2w_2_is_pirads_2(self):
        lesion = ProstateLesion("L1", ProstateZone.TRANSITION, t2w_score=2, dwi_score=4)
        r = score_transition_zone(lesion)
        assert r.pirads_score == 2

    def test_tz_t2w_3_dwi_3_is_pirads_3(self):
        lesion = ProstateLesion("L1", ProstateZone.TRANSITION, t2w_score=3, dwi_score=3)
        r = score_transition_zone(lesion)
        assert r.pirads_score == 3

    def test_tz_t2w_3_dwi_4_upgrades_to_4(self):
        """DWI score 4 upgrades TZ T2W score 3 to 4."""
        lesion = ProstateLesion("L1", ProstateZone.TRANSITION, t2w_score=3, dwi_score=4)
        r = score_transition_zone(lesion)
        assert r.pirads_score == 4

    def test_tz_t2w_3_dwi_5_upgrades_to_4(self):
        """DWI score 5 upgrades TZ T2W score 3 to 4."""
        lesion = ProstateLesion("L1", ProstateZone.TRANSITION, t2w_score=3, dwi_score=5)
        r = score_transition_zone(lesion)
        assert r.pirads_score == 4

    def test_tz_t2w_4_is_pirads_4(self):
        lesion = ProstateLesion("L1", ProstateZone.TRANSITION, t2w_score=4, dwi_score=2)
        r = score_transition_zone(lesion)
        assert r.pirads_score == 4

    def test_tz_t2w_5_is_pirads_5(self):
        lesion = ProstateLesion("L1", ProstateZone.TRANSITION, t2w_score=5, dwi_score=5)
        r = score_transition_zone(lesion)
        assert r.pirads_score == 5

    def test_tz_primary_is_t2w(self):
        lesion = ProstateLesion("L1", ProstateZone.TRANSITION, t2w_score=3, dwi_score=2)
        r = score_transition_zone(lesion)
        assert r.primary_sequence == "T2W"
        assert r.secondary_sequence == "DWI"


# ── Biopsy Recommendation Tests ─────────────────────────────────────

class TestBiopsyRecommendation:
    def test_pirads_1_no_biopsy(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=1, dwi_score=1)
        r = score_lesion(lesion)
        assert not r.biopsy_recommended

    def test_pirads_2_no_biopsy(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=2, dwi_score=2)
        r = score_lesion(lesion)
        assert not r.biopsy_recommended

    def test_pirads_3_biopsy_recommended(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=3, dwi_score=3)
        r = score_lesion(lesion)
        assert r.biopsy_recommended

    def test_pirads_4_biopsy_recommended(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=4, dwi_score=4)
        r = score_lesion(lesion)
        assert r.biopsy_recommended

    def test_pirads_5_biopsy_recommended(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=5, dwi_score=5)
        r = score_lesion(lesion)
        assert r.biopsy_recommended


# ── Zone Routing Tests ──────────────────────────────────────────────

class TestZoneRouting:
    def test_anterior_fibromuscular_uses_tz_rules(self):
        lesion = ProstateLesion("L1", ProstateZone.ANTERIOR_FIBROMUSCULAR, t2w_score=3, dwi_score=4)
        r = score_lesion(lesion)
        assert r.primary_sequence == "T2W"
        assert r.pirads_score == 4

    def test_central_zone_uses_tz_rules(self):
        lesion = ProstateLesion("L1", ProstateZone.CENTRAL, t2w_score=3, dwi_score=5)
        r = score_lesion(lesion)
        assert r.primary_sequence == "T2W"
        assert r.pirads_score == 4


# ── Validation Tests ────────────────────────────────────────────────

class TestValidation:
    def test_invalid_t2w_score(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=6, dwi_score=3)
        with pytest.raises(ValueError):
            score_lesion(lesion)

    def test_invalid_dwi_score(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=3, dwi_score=0)
        with pytest.raises(ValueError):
            score_lesion(lesion)


# ── Patient Assessment Tests ────────────────────────────────────────

class TestPatientAssessment:
    def test_multiple_lesions(self):
        lesions = [
            ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=2, dwi_score=2),
            ProstateLesion("L2", ProstateZone.TRANSITION, t2w_score=4, dwi_score=3),
        ]
        assessment = assess_patient(lesions)
        assert len(assessment.lesions) == 2
        assert assessment.max_pirads_score == 4
        assert assessment.has_actionable_lesion

    def test_no_lesions(self):
        assessment = assess_patient([])
        assert assessment.max_pirads_score == 0
        assert not assessment.has_actionable_lesion

    def test_assessment_to_dict(self):
        lesions = [ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=3, dwi_score=3)]
        assessment = assess_patient(lesions)
        d = assessment.to_dict()
        assert "lesions" in d
        assert "max_pirads_score" in d


# ── Result Model Tests ──────────────────────────────────────────────

class TestResultModel:
    def test_result_to_dict(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=3, dwi_score=4, dce_positive=True, size_mm=12)
        r = score_lesion(lesion)
        d = r.to_dict()
        assert d["pirads_score"] == 4
        assert d["zone"] == "peripheral"
        assert d["size_mm"] == 12

    def test_clinical_significance_populated(self):
        lesion = ProstateLesion("L1", ProstateZone.PERIPHERAL, t2w_score=4, dwi_score=4)
        r = score_lesion(lesion)
        assert "likely" in r.clinical_significance.lower()


# ── CLI Tests ───────────────────────────────────────────────────────

class TestCLI:
    def test_score_command(self, capsys):
        ret = cli_main(["score", "--zone", "peripheral", "--t2w", "3", "--dwi", "4", "--dce-positive"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "PI-RADS" in out

    def test_score_json(self, capsys):
        ret = cli_main(["score", "--zone", "peripheral", "--t2w", "3", "--dwi", "4", "--json"])
        assert ret == 0
        import json
        data = json.loads(capsys.readouterr().out)
        assert data["pirads_score"] == 4

    def test_assess_command(self, capsys):
        ret = cli_main(["assess", "-l", "peripheral:3:4:dce:12", "-l", "transition:2:2:0:8"])
        assert ret == 0

    def test_info_command(self, capsys):
        ret = cli_main(["info"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "PI-RADS" in out

    def test_info_specific_score(self, capsys):
        ret = cli_main(["info", "4"])
        assert ret == 0
        out = capsys.readouterr().out
        assert "likely" in out.lower()
