"""The company brain is a gate too: skills well formed, named paths real, run records private and on schema."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("brain_check", ROOT / "brain" / "tools" / "brain_check.py")
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)


def test_every_skill_is_well_formed():
    assert bc.check_skills() == []


def test_every_path_the_brain_names_exists():
    assert bc.check_paths() == []


def test_run_records_fit_the_schema():
    assert bc.check_runs() == []


def test_a_run_record_with_personal_data_is_refused(tmp_path, monkeypatch):
    rec = {"at": "2026-11-09", "agent": "x", "skill": "none", "task": "t", "outcome": "success", "layer": "none",
           "finding": "mailed someone@example.com", "gates": [], "human_needed": False, "closed_by": None}
    f = tmp_path / "runs.jsonl"
    f.write_text(json.dumps(rec) + "\n")
    monkeypatch.setattr(bc, "RUNS", f)
    assert any("personal data" in b for b in bc.check_runs())


def test_the_sweep_runs_and_returns_findings():
    import datetime as dt
    assert isinstance(bc.sweep(dt.date(2026, 11, 9)), list)


def test_the_sweep_reads_every_waiver_review_wording():
    """2026-11-15: ROOTS 12 says "Review at first push, by 2026-10-13" and the sweep missed it."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("brain_check", ROOT / "brain" / "tools" / "brain_check.py")
    bc = importlib.util.module_from_spec(spec); spec.loader.exec_module(bc)
    assert bc.WAIVER_REVIEW.search("| 7 | x | no suspend endpoint. Review by 2026-10-18. |").group(1) == "2026-10-18"
    assert bc.WAIVER_REVIEW.search("| 12 | x | never run. Review at first push, by 2026-10-13. |").group(1) == "2026-10-13"
    assert bc.WAIVER_REVIEW.search("| 3 | x | reviewed and cleared |") is None
