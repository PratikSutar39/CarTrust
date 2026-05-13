"""Tests for cross-dimension contradiction detection."""

import pytest
from cartrust.reasoning.rules.contradictions import detect_contradictions


def _make_evidence(ownership=None, odometer=None, accident=None, financial=None, service=None):
    from datetime import datetime
    from cartrust.schemas import VehicleEvidence, VehicleMetadata
    from tests.conftest import _empty_packet

    return VehicleEvidence(
        metadata=VehicleMetadata(make="Test", model="Car", year=2020),
        ownership=ownership or _empty_packet("ownership"),
        odometer=odometer or _empty_packet("odometer"),
        accident=accident or _empty_packet("accident"),
        financial=financial or _empty_packet("financial"),
        service=service or _empty_packet("service"),
        extraction_timestamp=datetime(2024, 1, 1),
    )


class TestNoContradictions:
    def test_clean_vehicle_has_no_contradictions(
        self, ownership_clean, odometer_clean, accident_clean, financial_clean, service_clean
    ):
        ev = _make_evidence(ownership_clean, odometer_clean, accident_clean, financial_clean, service_clean)
        result = detect_contradictions(ev)
        assert result == []


class TestSellerCredibilityCollapse:
    def test_undisclosed_loan_triggers_contradiction(
        self, ownership_clean, odometer_clean, accident_clean, financial_critical_undisclosed, service_clean
    ):
        ev = _make_evidence(ownership_clean, odometer_clean, accident_clean, financial_critical_undisclosed, service_clean)
        result = detect_contradictions(ev)
        c_ids = [c.contradiction_id for c in result]
        assert "CROSS_SELLER_CREDIBILITY_COLLAPSE" in c_ids

    def test_contradiction_is_critical(
        self, ownership_clean, odometer_clean, accident_clean, financial_critical_undisclosed, service_clean
    ):
        ev = _make_evidence(ownership_clean, odometer_clean, accident_clean, financial_critical_undisclosed, service_clean)
        result = detect_contradictions(ev)
        for c in result:
            if c.contradiction_id == "CROSS_SELLER_CREDIBILITY_COLLAPSE":
                assert c.severity == "critical"


class TestSellerVsInsurance:
    def test_undisclosed_accident_triggers_contradiction(
        self, ownership_clean, odometer_clean, accident_undisclosed_major, financial_clean, service_clean
    ):
        ev = _make_evidence(ownership_clean, odometer_clean, accident_undisclosed_major, financial_clean, service_clean)
        result = detect_contradictions(ev)
        c_ids = [c.contradiction_id for c in result]
        assert "CROSS_SELLER_VS_INSURANCE" in c_ids

    def test_contradiction_severity_is_high(
        self, ownership_clean, odometer_clean, accident_undisclosed_major, financial_clean, service_clean
    ):
        ev = _make_evidence(ownership_clean, odometer_clean, accident_undisclosed_major, financial_clean, service_clean)
        result = detect_contradictions(ev)
        for c in result:
            if c.contradiction_id == "CROSS_SELLER_VS_INSURANCE":
                assert c.severity == "high"
