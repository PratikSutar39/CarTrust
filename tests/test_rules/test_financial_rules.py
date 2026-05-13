"""Tests for the financial dimension rule engine."""

import pytest
from cartrust.reasoning.rules.financial import assess_financial


class TestFinancialClean:
    def test_state_is_verified_clean(self, financial_clean):
        result = assess_financial(financial_clean)
        assert result.state == "verified_clean"

    def test_score_is_high(self, financial_clean):
        result = assess_financial(financial_clean)
        assert result.score >= 0.90

    def test_no_flags(self, financial_clean):
        result = assess_financial(financial_clean)
        assert result.flags == []


class TestFinancialCriticalUndisclosed:
    def test_state_is_critical(self, financial_critical_undisclosed):
        result = assess_financial(financial_critical_undisclosed)
        assert result.state == "critical"

    def test_score_is_zero(self, financial_critical_undisclosed):
        result = assess_financial(financial_critical_undisclosed)
        assert result.score == 0.0

    def test_flag_is_undisclosed_loan(self, financial_critical_undisclosed):
        result = assess_financial(financial_critical_undisclosed)
        flag_ids = [f.flag_id for f in result.flags]
        assert "FIN_UNDISCLOSED_LOAN" in flag_ids

    def test_flag_severity_is_critical(self, financial_critical_undisclosed):
        result = assess_financial(financial_critical_undisclosed)
        for flag in result.flags:
            if flag.flag_id == "FIN_UNDISCLOSED_LOAN":
                assert flag.severity == "critical"


class TestFinancialActiveResolvable:
    def test_state_is_active_resolvable(self, financial_active_resolvable):
        result = assess_financial(financial_active_resolvable)
        assert result.state == "active_resolvable"

    def test_score_is_partial(self, financial_active_resolvable):
        result = assess_financial(financial_active_resolvable)
        assert 0.0 < result.score <= 0.60

    def test_flag_is_active_resolvable(self, financial_active_resolvable):
        result = assess_financial(financial_active_resolvable)
        flag_ids = [f.flag_id for f in result.flags]
        assert "FIN_ACTIVE_RESOLVABLE" in flag_ids

    def test_flag_severity_is_medium(self, financial_active_resolvable):
        result = assess_financial(financial_active_resolvable)
        for flag in result.flags:
            if flag.flag_id == "FIN_ACTIVE_RESOLVABLE":
                assert flag.severity == "medium"


class TestFinancialMissing:
    def test_state_when_no_data(self, financial_missing):
        result = assess_financial(financial_missing)
        # Missing RC data → rule returns unverifiable state with critical flag
        assert result.state in ("unverifiable", "critical")

    def test_score_is_zero_when_no_data(self, financial_missing):
        result = assess_financial(financial_missing)
        assert result.score == 0.0

    def test_unverifiable_critical_gap_flag(self, financial_missing):
        result = assess_financial(financial_missing)
        flag_ids = [f.flag_id for f in result.flags]
        assert "FIN_UNVERIFIABLE_CRITICAL_GAP" in flag_ids
