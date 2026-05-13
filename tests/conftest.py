"""Shared pytest fixtures for CarTrust tests."""

from datetime import datetime
import pytest

from cartrust.schemas import (
    EvidencePacket,
    Fact,
    Signal,
    VehicleEvidence,
    VehicleMetadata,
)


# ── Fact/Signal helpers ────────────────────────────────────────────────────────

def make_fact(field, value, source_type="rc_document", source_confidence=0.90, extraction_confidence=0.95, raw_excerpt=""):
    return Fact(
        value=value,
        field=field,
        source_type=source_type,
        source_detail="test",
        source_confidence=source_confidence,
        extraction_confidence=extraction_confidence,
        raw_excerpt=raw_excerpt,
    )


def make_signal(name, value, unit=None, confidence=0.90, basis="test"):
    return Signal(name=name, value=value, unit=unit, confidence=confidence, basis=basis)


def _empty_packet(dimension):
    return EvidencePacket(
        dimension=dimension,
        facts=[],
        signals=[],
        coverage=0.0,
        observations=[],
        data_available=False,
    )


# ── Financial evidence builders ────────────────────────────────────────────────

@pytest.fixture
def financial_clean():
    """No hypothecation — verified clean."""
    return EvidencePacket(
        dimension="financial",
        facts=[
            make_fact("hypothecation_active", False, source_type="rc_document"),
            make_fact("lender", None, source_type="rc_document"),
        ],
        signals=[
            make_signal("hypothecation_active", False),
            make_signal("seller_loan_disclosure_status", "silent"),
        ],
        coverage=0.90,
        observations=["No hypothecation in RC"],
        data_available=True,
    )


@pytest.fixture
def financial_critical_undisclosed():
    """Active hypothecation; seller denied — critical."""
    return EvidencePacket(
        dimension="financial",
        facts=[
            make_fact("hypothecation_active", True, source_type="rc_document"),
            make_fact("lender_name", "Bajaj Finance", source_type="rc_document"),
            make_fact("seller_loan_disclosure", "denied", source_type="seller_claim", source_confidence=0.30),
        ],
        signals=[
            make_signal("hypothecation_active", True),
            make_signal("seller_loan_disclosure_status", {"denied": True, "acknowledged": False, "closure_plan_provided": False}),
        ],
        coverage=0.90,
        observations=["Hypothecation active; seller denied loan"],
        data_available=True,
    )


@pytest.fixture
def financial_active_resolvable():
    """Active hypothecation; seller acknowledged + closure plan — resolvable."""
    return EvidencePacket(
        dimension="financial",
        facts=[
            make_fact("hypothecation_active", True, source_type="rc_document"),
            make_fact("lender_name", "HDFC Bank", source_type="rc_document"),
            make_fact("seller_loan_disclosure", "acknowledged", source_type="seller_claim", source_confidence=0.30),
            make_fact("closure_plan", "NOC will be provided at registration", source_type="seller_claim", source_confidence=0.30),
        ],
        signals=[
            make_signal("hypothecation_active", True),
            make_signal("seller_loan_disclosure_status", {"denied": False, "acknowledged": True, "closure_plan_provided": True}),
        ],
        coverage=0.90,
        observations=["Hypothecation active; closure plan provided"],
        data_available=True,
    )


@pytest.fixture
def financial_missing():
    """No RC data available."""
    return _empty_packet("financial")


# ── Odometer evidence builders ─────────────────────────────────────────────────

@pytest.fixture
def odometer_clean():
    """Stated 38,000 km; two signals agree (within 5%)."""
    return EvidencePacket(
        dimension="odometer",
        facts=[
            make_fact("stated_odometer", 38000, source_type="rc_document"),
        ],
        signals=[
            make_signal("stated_odometer", 38000, unit="km"),
            make_signal("oil_change_implied_km", 37200, unit="km", confidence=0.80),
            make_signal("vehicle_age_implied_km", 36000, unit="km", confidence=0.50),
            make_signal("median_implied_km", 37200, unit="km", confidence=0.80),
            make_signal("agreement_count", 2),
        ],
        coverage=0.80,
        observations=["Oil change count implies ~37,200 km"],
        data_available=True,
    )


@pytest.fixture
def odometer_major_discrepancy():
    """Stated 32,000 km; signals imply ~62,000 km (>10% discrepancy, 2+ agreeing)."""
    return EvidencePacket(
        dimension="odometer",
        facts=[
            make_fact("stated_odometer", 32000, source_type="rc_document"),
        ],
        signals=[
            make_signal("stated_odometer", 32000, unit="km"),
            make_signal("oil_change_implied_km", 60500, unit="km", confidence=0.80),
            make_signal("tyre_replacement_implied_km", 64000, unit="km", confidence=0.70),
            make_signal("median_implied_km", 62000, unit="km", confidence=0.80),
            make_signal("agreement_count", 3),
        ],
        coverage=0.85,
        observations=["Service record implies ~62,000 km vs stated 32,000 km"],
        data_available=True,
    )


@pytest.fixture
def odometer_minor_discrepancy():
    """Stated 50,000 km; median 53,500 km (~7% discrepancy); 2 signals above 55k threshold."""
    return EvidencePacket(
        dimension="odometer",
        facts=[
            make_fact("stated_odometer", 50000, source_type="rc_document"),
        ],
        signals=[
            make_signal("stated_odometer", 50000, unit="km"),
            make_signal("oil_change_implied_km", 55500, unit="km", confidence=0.80),
            make_signal("vehicle_age_implied_km", 56000, unit="km", confidence=0.50),
            make_signal("median_implied_km", 53500, unit="km", confidence=0.75),
            make_signal("agreement_count", 2),
        ],
        coverage=0.75,
        observations=["Minor discrepancy between stated and implied mileage (7%)"],
        data_available=True,
    )


@pytest.fixture
def odometer_unverifiable():
    """Only one estimation signal — insufficient to assess."""
    return EvidencePacket(
        dimension="odometer",
        facts=[
            make_fact("stated_odometer", 38000, source_type="seller_claim", source_confidence=0.30),
        ],
        signals=[
            make_signal("stated_odometer", 38000, unit="km"),
            make_signal("oil_change_implied_km", 37000, unit="km", confidence=0.80),
            make_signal("agreement_count", 1),
        ],
        coverage=0.30,
        observations=["Only one estimation signal available"],
        data_available=True,
    )


# ── Accident evidence builders ─────────────────────────────────────────────────

@pytest.fixture
def accident_clean():
    """No claims."""
    return EvidencePacket(
        dimension="accident",
        facts=[make_fact("total_claim_count", 0, source_type="insurance_record")],
        signals=[
            make_signal("total_claim_count", 0),
            make_signal("major_claims_count", 0),
            make_signal("max_claim_amount", 0, unit="INR"),
        ],
        coverage=0.85,
        observations=["No insurance claims found"],
        data_available=True,
    )


@pytest.fixture
def accident_undisclosed_major():
    """Major claim Rs. 1,20,000; seller denied any accident."""
    return EvidencePacket(
        dimension="accident",
        facts=[
            make_fact("total_claim_count", 1, source_type="insurance_record"),
            make_fact("claim_amount", 120000, source_type="insurance_record"),
            make_fact("seller_accident_disclosure", "denied", source_type="seller_claim", source_confidence=0.30),
        ],
        signals=[
            make_signal("total_claim_count", 1),
            make_signal("major_claims_count", 1),
            make_signal("max_claim_amount", 120000, unit="INR"),
            make_signal("seller_denial_vs_claims", {"seller_denied_accidents": True}),
        ],
        coverage=0.90,
        observations=["Major claim Rs. 1,20,000; seller denied"],
        data_available=True,
    )


@pytest.fixture
def accident_disclosed_major():
    """Major claim Rs. 80,000; seller acknowledged."""
    return EvidencePacket(
        dimension="accident",
        facts=[
            make_fact("total_claim_count", 1, source_type="insurance_record"),
            make_fact("claim_amount", 80000, source_type="insurance_record"),
            make_fact("seller_accident_disclosure", "acknowledged", source_type="seller_claim", source_confidence=0.30),
        ],
        signals=[
            make_signal("total_claim_count", 1),
            make_signal("major_claims_count", 1),
            make_signal("max_claim_amount", 80000, unit="INR"),
            make_signal("seller_denial_vs_claims", {"seller_denied_accidents": False}),
        ],
        coverage=0.90,
        observations=["Major claim Rs. 80,000; seller acknowledged"],
        data_available=True,
    )


# ── Ownership evidence builders ────────────────────────────────────────────────

@pytest.fixture
def ownership_clean():
    """Names match, one owner, no rapid flipping."""
    return EvidencePacket(
        dimension="ownership",
        facts=[
            make_fact("rc_owner_name", "Rakesh Sharma", source_type="rc_document"),
            make_fact("seller_name", "Rakesh Sharma", source_type="seller_claim", source_confidence=0.30),
            make_fact("rc_owner_count", 1, source_type="rc_document"),
            make_fact("seller_claimed_owner_count", 1, source_type="seller_claim", source_confidence=0.30),
        ],
        signals=[
            make_signal("owner_name_match", True),
            make_signal("owner_count_match", True),
            make_signal("ownership_velocity", 0.2),
        ],
        coverage=0.90,
        observations=["Names match; single owner"],
        data_available=True,
    )


@pytest.fixture
def ownership_name_mismatch():
    """RC owner different from seller."""
    return EvidencePacket(
        dimension="ownership",
        facts=[
            make_fact("rc_owner_name", "Vikram Singh", source_type="rc_document"),
            make_fact("seller_name", "Suresh Kumar", source_type="seller_claim", source_confidence=0.30),
            make_fact("rc_owner_count", 1, source_type="rc_document"),
        ],
        signals=[
            make_signal("owner_name_match", False),
            make_signal("owner_count_match", True),
            make_signal("ownership_velocity", 0.2),
        ],
        coverage=0.90,
        observations=["Name mismatch between RC and seller"],
        data_available=True,
    )


@pytest.fixture
def ownership_rapid_flip():
    """3 owners in 3 years — rapid flipping."""
    return EvidencePacket(
        dimension="ownership",
        facts=[
            make_fact("rc_owner_count", 3, source_type="rc_document"),
            make_fact("seller_claimed_owner_count", 3, source_type="seller_claim", source_confidence=0.30),
            make_fact("first_registration_date", "2021-01-15", source_type="rc_document"),
        ],
        signals=[
            make_signal("owner_name_match", True),
            make_signal("owner_count_match", True),
            make_signal("ownership_velocity", 1.0),
        ],
        coverage=0.85,
        observations=["3 owners in ~3 years"],
        data_available=True,
    )


# ── Service evidence builders ──────────────────────────────────────────────────

@pytest.fixture
def service_clean():
    """Regular service history, no gaps."""
    return EvidencePacket(
        dimension="service",
        facts=[
            make_fact("service_entry_count", 5, source_type="service_log"),
        ],
        signals=[
            make_signal("service_entry_count", 5),
            make_signal("service_log_span_months", 48),
            make_signal("long_service_gaps", 0),
            make_signal("months_since_last_service", 4),
            make_signal("authorized_to_local_switch", False),
        ],
        coverage=0.85,
        observations=["5 service entries over 48 months"],
        data_available=True,
    )


@pytest.fixture
def service_no_records():
    """No service records at all."""
    return _empty_packet("service")


@pytest.fixture
def service_gap():
    """Has a 15-month service gap."""
    return EvidencePacket(
        dimension="service",
        facts=[
            make_fact("service_entry_count", 3, source_type="service_log"),
        ],
        signals=[
            make_signal("service_entry_count", 3),
            make_signal("service_log_span_months", 48),
            make_signal("long_service_gaps", [{"from": "2021-03", "to": "2022-06", "months": 15}]),
            make_signal("months_since_last_service", 5),
            make_signal("authorized_to_local_switch", False),
        ],
        coverage=0.70,
        observations=["One gap of 15 months between services"],
        data_available=True,
    )


# ── Full VehicleEvidence fixture ───────────────────────────────────────────────

@pytest.fixture
def vehicle_evidence_clean(ownership_clean, odometer_clean, accident_clean, financial_clean, service_clean):
    """Full VehicleEvidence with all clean dimensions."""
    return VehicleEvidence(
        metadata=VehicleMetadata(
            make="Honda",
            model="City",
            year=2018,
            registration_number="MH12AB1234",
            listing_price=650000,
        ),
        ownership=ownership_clean,
        odometer=odometer_clean,
        accident=accident_clean,
        financial=financial_clean,
        service=service_clean,
        extraction_timestamp=datetime(2024, 5, 1),
    )


@pytest.fixture
def vehicle_evidence_hard_stop(ownership_clean, odometer_clean, accident_clean, financial_critical_undisclosed, service_clean):
    """Full VehicleEvidence with critical financial issue."""
    return VehicleEvidence(
        metadata=VehicleMetadata(
            make="Hyundai",
            model="Creta",
            year=2020,
            registration_number="KA01XX9999",
            listing_price=900000,
        ),
        ownership=ownership_clean,
        odometer=odometer_clean,
        accident=accident_clean,
        financial=financial_critical_undisclosed,
        service=service_clean,
        extraction_timestamp=datetime(2024, 5, 1),
    )
