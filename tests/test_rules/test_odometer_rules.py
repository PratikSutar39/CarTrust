"""Tests for the odometer dimension rule engine."""

import pytest
from cartrust.reasoning.rules.odometer import assess_odometer


class TestOdometerClean:
    def test_state_is_verified_clean(self, odometer_clean):
        result = assess_odometer(odometer_clean)
        assert result.state == "verified_clean"

    def test_score_is_high(self, odometer_clean):
        result = assess_odometer(odometer_clean)
        assert result.score >= 0.90

    def test_no_flags(self, odometer_clean):
        result = assess_odometer(odometer_clean)
        assert result.flags == []


class TestOdometerMajorDiscrepancy:
    def test_state_is_verified_flagged(self, odometer_major_discrepancy):
        result = assess_odometer(odometer_major_discrepancy)
        assert result.state in ("verified_flagged", "critical")

    def test_score_is_penalised(self, odometer_major_discrepancy):
        result = assess_odometer(odometer_major_discrepancy)
        assert result.score < 0.50

    def test_flag_is_multi_signal_discrepancy(self, odometer_major_discrepancy):
        result = assess_odometer(odometer_major_discrepancy)
        flag_ids = [f.flag_id for f in result.flags]
        assert "ODO_MULTI_SIGNAL_DISCREPANCY" in flag_ids

    def test_flag_severity_is_high(self, odometer_major_discrepancy):
        result = assess_odometer(odometer_major_discrepancy)
        for f in result.flags:
            if f.flag_id == "ODO_MULTI_SIGNAL_DISCREPANCY":
                assert f.severity == "high"


class TestOdometerMinorDiscrepancy:
    def test_state_is_verified_flagged(self, odometer_minor_discrepancy):
        result = assess_odometer(odometer_minor_discrepancy)
        assert result.state == "verified_flagged"

    def test_score_around_0_70(self, odometer_minor_discrepancy):
        result = assess_odometer(odometer_minor_discrepancy)
        assert 0.60 <= result.score <= 0.80

    def test_minor_discrepancy_flag(self, odometer_minor_discrepancy):
        result = assess_odometer(odometer_minor_discrepancy)
        flag_ids = [f.flag_id for f in result.flags]
        assert "ODO_MINOR_DISCREPANCY" in flag_ids


class TestOdometerUnverifiable:
    def test_state_is_unverifiable(self, odometer_unverifiable):
        result = assess_odometer(odometer_unverifiable)
        assert result.state == "unverifiable"

    def test_no_discrepancy_flag_when_unverifiable(self, odometer_unverifiable):
        result = assess_odometer(odometer_unverifiable)
        flag_ids = [f.flag_id for f in result.flags]
        assert "ODO_MULTI_SIGNAL_DISCREPANCY" not in flag_ids
        assert "ODO_MINOR_DISCREPANCY" not in flag_ids
