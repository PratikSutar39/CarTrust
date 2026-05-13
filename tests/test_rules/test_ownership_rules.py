"""Tests for the ownership dimension rule engine."""

import pytest
from cartrust.reasoning.rules.ownership import assess_ownership


class TestOwnershipClean:
    def test_state_is_verified_clean(self, ownership_clean):
        result = assess_ownership(ownership_clean)
        assert result.state == "verified_clean"

    def test_score_is_high(self, ownership_clean):
        result = assess_ownership(ownership_clean)
        assert result.score >= 0.85

    def test_no_flags(self, ownership_clean):
        result = assess_ownership(ownership_clean)
        assert result.flags == []


class TestOwnershipNameMismatch:
    def test_flag_is_name_mismatch(self, ownership_name_mismatch):
        result = assess_ownership(ownership_name_mismatch)
        flag_ids = [f.flag_id for f in result.flags]
        assert "OWN_OWNER_NAME_MISMATCH" in flag_ids

    def test_severity_is_high(self, ownership_name_mismatch):
        result = assess_ownership(ownership_name_mismatch)
        for f in result.flags:
            if f.flag_id == "OWN_OWNER_NAME_MISMATCH":
                assert f.severity == "high"

    def test_score_is_penalised(self, ownership_name_mismatch):
        result = assess_ownership(ownership_name_mismatch)
        assert result.score <= 0.70


class TestOwnershipRapidFlip:
    def test_flag_is_rapid_flipping(self, ownership_rapid_flip):
        result = assess_ownership(ownership_rapid_flip)
        flag_ids = [f.flag_id for f in result.flags]
        assert "OWN_RAPID_FLIPPING" in flag_ids

    def test_severity_is_medium(self, ownership_rapid_flip):
        result = assess_ownership(ownership_rapid_flip)
        for f in result.flags:
            if f.flag_id == "OWN_RAPID_FLIPPING":
                assert f.severity == "medium"

    def test_score_is_penalised(self, ownership_rapid_flip):
        result = assess_ownership(ownership_rapid_flip)
        assert result.score <= 0.85
