"""Tests for the service dimension rule engine."""

import pytest
from cartrust.reasoning.rules.service import assess_service


class TestServiceClean:
    def test_state_is_verified_clean(self, service_clean):
        result = assess_service(service_clean)
        assert result.state == "verified_clean"

    def test_score_is_high(self, service_clean):
        result = assess_service(service_clean)
        assert result.score >= 0.80

    def test_no_flags(self, service_clean):
        result = assess_service(service_clean)
        assert result.flags == []


class TestServiceNoRecords:
    def test_state_is_flagged_or_unverifiable(self, service_no_records):
        result = assess_service(service_no_records)
        assert result.state in ("verified_flagged", "unverifiable")

    def test_flag_is_no_records(self, service_no_records):
        result = assess_service(service_no_records)
        flag_ids = [f.flag_id for f in result.flags]
        assert "SVC_NO_RECORDS" in flag_ids

    def test_severity_is_medium(self, service_no_records):
        result = assess_service(service_no_records)
        for f in result.flags:
            if f.flag_id == "SVC_NO_RECORDS":
                assert f.severity == "medium"


class TestServiceGap:
    def test_flag_is_gap_over_12_months(self, service_gap):
        result = assess_service(service_gap)
        flag_ids = [f.flag_id for f in result.flags]
        assert "SVC_GAP_OVER_12_MONTHS" in flag_ids

    def test_severity_is_medium(self, service_gap):
        result = assess_service(service_gap)
        for f in result.flags:
            if f.flag_id == "SVC_GAP_OVER_12_MONTHS":
                assert f.severity == "medium"

    def test_score_is_penalised(self, service_gap):
        result = assess_service(service_gap)
        assert result.score <= 0.85
