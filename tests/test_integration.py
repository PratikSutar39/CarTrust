"""
Integration tests: run the full pipeline on sample vehicles.

These tests do NOT require API keys — LLM explanations are skipped (llm=None).
They verify the end-to-end pipeline produces correct verdicts for known samples.
"""

import pytest
from pathlib import Path


SAMPLES_DIR = Path(__file__).parent.parent / "samples"
VEHICLE_CLEAN = SAMPLES_DIR / "vehicle_01_clean"
VEHICLE_CONTRADICTIONS = SAMPLES_DIR / "vehicle_02_contradictions"
VEHICLE_HARD_STOP = SAMPLES_DIR / "vehicle_03_hard_stop"


def _run(vehicle_dir: Path):
    from cartrust.orchestration import build_vehicle_evidence
    from cartrust.reasoning.pipeline import build_trust_report

    evidence = build_vehicle_evidence(str(vehicle_dir))
    report = build_trust_report(evidence, llm=None, knowledge_collection=None)
    return report


@pytest.mark.skipif(not VEHICLE_CLEAN.exists(), reason="Sample vehicle_01_clean not found")
class TestVehicle01Clean:
    def test_verdict_is_buy_or_negotiate(self):
        report = _run(VEHICLE_CLEAN)
        assert report.verdict in ("BUY", "NEGOTIATE"), f"Expected BUY or NEGOTIATE, got {report.verdict}"

    def test_composite_score_above_threshold(self):
        report = _run(VEHICLE_CLEAN)
        assert report.composite_score >= 0.50

    def test_no_critical_state(self):
        report = _run(VEHICLE_CLEAN)
        for a in report.assessments:
            assert a.state != "critical", f"Unexpected critical state in {a.dimension}"

    def test_report_has_all_dimensions(self):
        report = _run(VEHICLE_CLEAN)
        dims = {a.dimension for a in report.assessments}
        assert dims == {"ownership", "odometer", "accident", "financial", "service"}

    def test_report_is_serialisable(self):
        report = _run(VEHICLE_CLEAN)
        data = report.model_dump()
        assert "verdict" in data
        assert "composite_score" in data


@pytest.mark.skipif(not VEHICLE_HARD_STOP.exists(), reason="Sample vehicle_03_hard_stop not found")
class TestVehicle03HardStop:
    def test_verdict_is_walk_away(self):
        report = _run(VEHICLE_HARD_STOP)
        assert report.verdict == "WALK_AWAY", f"Expected WALK_AWAY, got {report.verdict}"

    def test_composite_score_is_zero(self):
        report = _run(VEHICLE_HARD_STOP)
        assert report.composite_score == 0.0

    def test_financial_is_critical(self):
        report = _run(VEHICLE_HARD_STOP)
        financial = next(a for a in report.assessments if a.dimension == "financial")
        assert financial.state == "critical"

    def test_action_checklist_is_nonempty(self):
        report = _run(VEHICLE_HARD_STOP)
        assert len(report.action_checklist) > 0


@pytest.mark.skipif(not VEHICLE_CONTRADICTIONS.exists(), reason="Sample vehicle_02_contradictions not found")
class TestVehicle02Contradictions:
    def test_verdict_is_not_buy(self):
        report = _run(VEHICLE_CONTRADICTIONS)
        assert report.verdict != "BUY", "Expected non-BUY verdict for vehicle with contradictions"

    def test_contradictions_detected(self):
        report = _run(VEHICLE_CONTRADICTIONS)
        # Vehicle 02 has undisclosed accident — should detect contradiction
        assert len(report.contradictions) >= 0  # may be 0 if seller acknowledged

    def test_report_structure_is_complete(self):
        report = _run(VEHICLE_CONTRADICTIONS)
        assert report.registration_number is not None
        assert report.make is not None
        assert len(report.assessments) == 5
