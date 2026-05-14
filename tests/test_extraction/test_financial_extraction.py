"""Tests for the financial evidence extraction module."""

import pytest
from cartrust.extraction.financial import extract_financial


class TestFinancialExtractionClean:
    def test_no_hypothecation(self):
        raw = {
            "rc": {
                "registration_number": "MH12AB1234",
                "owner_name": "Rakesh Sharma",
                "hypothecation": {"active": False, "lender": None},
            },
            "seller_claims": {"loan_status": "free of dues"},
        }
        packet = extract_financial(raw)
        assert packet.data_available is True
        hyp_signal = next((s for s in packet.signals if s.name == "hypothecation_active"), None)
        assert hyp_signal is not None
        assert hyp_signal.value is False

    def test_coverage_is_nonzero(self):
        raw = {"rc": {"hypothecation": {"active": False, "lender": None}}}
        packet = extract_financial(raw)
        assert packet.coverage > 0.0


class TestFinancialExtractionActiveHypothecation:
    def test_hypothecation_active(self):
        raw = {
            "rc": {
                "hypothecation": {"active": True, "lender": "Bajaj Finance Limited"},
            },
            "seller_claims": {"loan_status": "free of dues"},
        }
        packet = extract_financial(raw)
        hyp_signal = next((s for s in packet.signals if s.name == "hypothecation_active"), None)
        assert hyp_signal is not None
        assert hyp_signal.value is True

    def test_lender_fact_extracted(self):
        raw = {
            "rc": {
                "hypothecation": {"active": True, "lender": "Bajaj Finance Limited"},
            }
        }
        packet = extract_financial(raw)
        # The extractor stores the lender with field="lender_name"
        lender_facts = [f for f in packet.facts if f.field == "lender_name"]
        assert len(lender_facts) > 0
        assert lender_facts[0].value == "Bajaj Finance Limited"

    def test_seller_denial_detected(self):
        raw = {
            "rc": {
                "hypothecation": {"active": True, "lender": "Bajaj Finance"},
            },
            "seller_claims": {"loan_status": "free of dues"},
        }
        packet = extract_financial(raw)
        disc_signal = next((s for s in packet.signals if s.name == "seller_loan_disclosure_status"), None)
        assert disc_signal is not None
        # "free of dues" maps to denied=True
        assert isinstance(disc_signal.value, dict)
        assert disc_signal.value.get("denied") is True


class TestFinancialExtractionMissing:
    def test_empty_inputs_returns_packet(self):
        packet = extract_financial({})
        assert packet.dimension == "financial"
        assert packet.data_available is False

    def test_no_rc_data(self):
        packet = extract_financial({"listing": {}})
        assert packet.dimension == "financial"
        assert packet.coverage == 0.0
