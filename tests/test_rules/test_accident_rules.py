"""Tests for the accident dimension rule engine."""

import pytest
from cartrust.reasoning.rules.accident import assess_accident


class TestAccidentClean:
    def test_state_is_verified_clean(self, accident_clean):
        result = assess_accident(accident_clean)
        assert result.state == "verified_clean"

    def test_score_is_high(self, accident_clean):
        result = assess_accident(accident_clean)
        assert result.score >= 0.90

    def test_no_flags(self, accident_clean):
        result = assess_accident(accident_clean)
        assert result.flags == []


class TestAccidentUndisclosed:
    def test_state_is_verified_flagged(self, accident_undisclosed_major):
        result = assess_accident(accident_undisclosed_major)
        assert result.state == "verified_flagged"

    def test_score_is_low(self, accident_undisclosed_major):
        result = assess_accident(accident_undisclosed_major)
        assert result.score <= 0.30

    def test_undisclosed_major_claim_flag(self, accident_undisclosed_major):
        result = assess_accident(accident_undisclosed_major)
        flag_ids = [f.flag_id for f in result.flags]
        assert "ACC_UNDISCLOSED_MAJOR_CLAIM" in flag_ids

    def test_flag_severity_is_high(self, accident_undisclosed_major):
        result = assess_accident(accident_undisclosed_major)
        for f in result.flags:
            if f.flag_id == "ACC_UNDISCLOSED_MAJOR_CLAIM":
                assert f.severity == "high"


class TestAccidentDisclosed:
    def test_state_is_verified_flagged(self, accident_disclosed_major):
        result = assess_accident(accident_disclosed_major)
        assert result.state == "verified_flagged"

    def test_score_is_moderate(self, accident_disclosed_major):
        result = assess_accident(accident_disclosed_major)
        assert result.score >= 0.50

    def test_flag_is_major_claim_disclosed(self, accident_disclosed_major):
        result = assess_accident(accident_disclosed_major)
        flag_ids = [f.flag_id for f in result.flags]
        assert "ACC_MAJOR_CLAIM_DISCLOSED" in flag_ids

    def test_flag_severity_is_medium(self, accident_disclosed_major):
        result = assess_accident(accident_disclosed_major)
        for f in result.flags:
            if f.flag_id == "ACC_MAJOR_CLAIM_DISCLOSED":
                assert f.severity == "medium"
