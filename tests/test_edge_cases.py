"""Edge case tests: never-fail guarantees, scoring bounds, verdict correctness."""

import pytest
from datetime import datetime

from cartrust.schemas import VehicleEvidence, VehicleMetadata, EvidencePacket
from cartrust.reasoning.scoring import compute_trust_score, compute_coverage
from cartrust.reasoning.verdict import determine_verdict, generate_action_checklist
from cartrust.reasoning.schemas import DimensionAssessment, Flag


def _empty_packet(dimension):
    return EvidencePacket(
        dimension=dimension,
        facts=[],
        signals=[],
        coverage=0.0,
        observations=[],
        data_available=False,
    )


def _make_assessment(dimension, state, score, flags=None):
    return DimensionAssessment(
        dimension=dimension,
        state=state,
        flags=flags or [],
        score=score,
        summary="",
        reasoning="",
    )


def _make_flag(flag_id, severity, suggested_actions=None):
    return Flag(
        flag_id=flag_id,
        severity=severity,
        evidence_summary="test",
        suggested_actions=suggested_actions or [],
    )


# ── Score bounds ───────────────────────────────────────────────────────────────

class TestScoringBounds:
    def test_all_clean_score_is_high(self):
        assessments = [
            _make_assessment("financial", "verified_clean", 0.95),
            _make_assessment("odometer", "verified_clean", 0.95),
            _make_assessment("accident", "verified_clean", 0.95),
            _make_assessment("ownership", "verified_clean", 0.90),
            _make_assessment("service", "verified_clean", 0.90),
        ]
        score, hard_stop, _ = compute_trust_score(assessments)
        assert score >= 0.80
        assert hard_stop is False

    def test_critical_dimension_forces_score_to_zero(self):
        assessments = [
            _make_assessment("financial", "critical", 0.0),
            _make_assessment("odometer", "verified_clean", 0.95),
            _make_assessment("accident", "verified_clean", 0.95),
            _make_assessment("ownership", "verified_clean", 0.90),
            _make_assessment("service", "verified_clean", 0.90),
        ]
        score, hard_stop, _ = compute_trust_score(assessments)
        assert score == 0.0
        assert hard_stop is True

    def test_score_never_exceeds_one(self):
        assessments = [
            _make_assessment("financial", "verified_clean", 1.0),
            _make_assessment("odometer", "verified_clean", 1.0),
            _make_assessment("accident", "verified_clean", 1.0),
            _make_assessment("ownership", "verified_clean", 1.0),
            _make_assessment("service", "verified_clean", 1.0),
        ]
        score, _, _ = compute_trust_score(assessments)
        assert score <= 1.0

    def test_score_never_negative(self):
        assessments = [
            _make_assessment("financial", "verified_flagged", 0.0),
            _make_assessment("odometer", "verified_flagged", 0.0),
            _make_assessment("accident", "verified_flagged", 0.0),
            _make_assessment("ownership", "verified_flagged", 0.0),
            _make_assessment("service", "verified_flagged", 0.0),
        ]
        score, _, _ = compute_trust_score(assessments)
        assert score >= 0.0


# ── Verdict correctness ────────────────────────────────────────────────────────

class TestVerdictCorrectness:
    def test_high_score_returns_buy(self):
        assessments = [_make_assessment("financial", "verified_clean", 0.95)]
        verdict = determine_verdict(0.85, False, assessments)
        assert verdict == "BUY"

    def test_hard_stop_returns_walk_away(self):
        assessments = [_make_assessment("financial", "critical", 0.0)]
        verdict = determine_verdict(0.0, True, assessments)
        assert verdict == "WALK_AWAY"

    def test_active_resolvable_returns_negotiate_with_safeguards(self):
        assessments = [_make_assessment("financial", "active_resolvable", 0.50)]
        verdict = determine_verdict(0.50, False, assessments)
        assert verdict == "NEGOTIATE_WITH_SAFEGUARDS"

    def test_mid_score_returns_negotiate(self):
        assessments = [_make_assessment("financial", "verified_clean", 0.70)]
        verdict = determine_verdict(0.65, False, assessments)
        assert verdict == "NEGOTIATE"

    def test_low_score_returns_walk_away(self):
        assessments = [_make_assessment("financial", "verified_flagged", 0.20)]
        verdict = determine_verdict(0.30, False, assessments)
        assert verdict == "WALK_AWAY"


# ── Action checklist deduplication ────────────────────────────────────────────

class TestActionChecklist:
    def test_deduplicates_repeated_actions(self):
        repeated_action = "Verify loan closure NOC from lender"
        flag1 = _make_flag("FIN_UNDISCLOSED_LOAN", "critical", [repeated_action])
        flag2 = _make_flag("FIN_ACTIVE_RESOLVABLE", "medium", [repeated_action])
        assessments = [
            _make_assessment("financial", "critical", 0.0, [flag1]),
            _make_assessment("odometer", "verified_flagged", 0.70, [flag2]),
        ]
        checklist = generate_action_checklist(assessments, [])
        assert checklist.count(repeated_action) == 1

    def test_critical_flags_come_first(self):
        critical_action = "Critical: do not proceed"
        low_action = "Low priority check"
        flag_critical = _make_flag("F1", "critical", [critical_action])
        flag_low = _make_flag("F2", "low", [low_action])
        assessments = [
            _make_assessment("service", "verified_flagged", 0.80, [flag_low]),
            _make_assessment("financial", "critical", 0.0, [flag_critical]),
        ]
        checklist = generate_action_checklist(assessments, [])
        assert checklist.index(critical_action) < checklist.index(low_action)

    def test_empty_assessments_returns_empty_list(self):
        checklist = generate_action_checklist([], [])
        assert checklist == []


# ── Coverage ──────────────────────────────────────────────────────────────────

class TestCoverage:
    def test_full_data_coverage_is_one(self):
        assessments = [
            _make_assessment("financial", "verified_clean", 0.95),
            _make_assessment("odometer", "verified_clean", 0.95),
            _make_assessment("accident", "verified_clean", 0.95),
            _make_assessment("ownership", "verified_clean", 0.90),
            _make_assessment("service", "verified_clean", 0.90),
        ]
        cov = compute_coverage(assessments)
        assert cov == 1.0

    def test_all_unverifiable_coverage_is_zero(self):
        assessments = [
            _make_assessment("financial", "unverifiable", 0.0),
            _make_assessment("odometer", "unverifiable", 0.0),
            _make_assessment("accident", "unverifiable", 0.0),
            _make_assessment("ownership", "unverifiable", 0.0),
            _make_assessment("service", "unverifiable", 0.0),
        ]
        cov = compute_coverage(assessments)
        assert cov == 0.0


# ── Never-fail guarantees ──────────────────────────────────────────────────────

class TestNeverFail:
    def test_extraction_never_raises_on_none_inputs(self):
        """All extraction modules must handle None gracefully."""
        from cartrust.extraction.ownership import extract_ownership
        from cartrust.extraction.odometer import extract_odometer
        from cartrust.extraction.accident import extract_accident
        from cartrust.extraction.financial import extract_financial
        from cartrust.extraction.service import extract_service

        for fn, dim in [
            (extract_ownership, "ownership"),
            (extract_odometer, "odometer"),
            (extract_accident, "accident"),
            (extract_financial, "financial"),
            (extract_service, "service"),
        ]:
            packet = fn({})
            assert packet.dimension == dim, f"{dim} extractor returned wrong dimension"

    def test_rule_engine_never_raises_on_empty_evidence(self):
        """Rule engine must handle empty EvidencePackets."""
        from cartrust.reasoning.rules.financial import assess_financial
        from cartrust.reasoning.rules.odometer import assess_odometer
        from cartrust.reasoning.rules.accident import assess_accident
        from cartrust.reasoning.rules.ownership import assess_ownership
        from cartrust.reasoning.rules.service import assess_service

        for fn, dim in [
            (assess_financial, "financial"),
            (assess_odometer, "odometer"),
            (assess_accident, "accident"),
            (assess_ownership, "ownership"),
            (assess_service, "service"),
        ]:
            result = fn(_empty_packet(dim))
            assert result is not None, f"{dim} rule engine returned None"
