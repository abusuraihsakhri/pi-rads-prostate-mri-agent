"""Regression test for CSV boolean parsing and batch output."""
import csv
from pi_rads_prostate_mri_agent.cli import main, _parse_bool
import pytest

@pytest.mark.parametrize("raw,expected", [
    ("True", True), ("FALSE", False), ("0", False),
    ("1", True), ("no", False), ("yes", True), ("", False),
])
def test_explicit_csv_booleans(raw, expected):
    assert _parse_bool(raw) is expected

def test_unknown_boolean_is_rejected():
    with pytest.raises(ValueError, match="Invalid boolean"):
        _parse_bool("sometimes")

def test_batch_false_flag_does_not_generate_stat_alert(tmp_path):
    source = tmp_path / "input.csv"
    target = tmp_path / "output.csv"
    source.write_text(
        "case_id,patient_synthetic_id,metric_primary,metric_secondary,is_stat,status_flag\n"
        "CASE-1,SYNTH-1,10,2,False,NORMAL\n", encoding="utf-8"
    )
    assert main(["batch", "-i", str(source), "-o", str(target)]) == 0
    with target.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1
    assert rows[0]["total_alerts"] == "0"
    assert rows[0]["stat_critical_alerts"] == "0"
