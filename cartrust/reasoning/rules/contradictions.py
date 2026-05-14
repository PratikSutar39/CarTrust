"""Phase 3 Rule Engine: Cross-dimension contradiction detector."""

import logging
from typing import List

from cartrust.constants import CLAIM_SERVICE_MATCH_WINDOW_DAYS, MAJOR_CLAIM_THRESHOLD_INR
from cartrust.reasoning.rules.helpers import find_signal
from cartrust.reasoning.schemas import Contradiction
from cartrust.schemas import VehicleEvidence

logger = logging.getLogger(__name__)


def detect_contradictions(evidence: VehicleEvidence) -> List[Contradiction]:
    """
    Pure Python. Examines evidence across all five dimensions to find
    cross-dimensional conflicts. Returns Contradiction objects without
    descriptions — the LLM explanation layer fills those in later.
    """
    try:
        return _detect_contradictions(evidence)
    except Exception as e:
        logger.error(f"Contradiction detection failed: {e}", exc_info=True)
        return []


def _detect_contradictions(evidence: VehicleEvidence) -> List[Contradiction]:
    contradictions = []

    # ── Contradiction 1: Seller credibility collapse ──
    if evidence.financial.data_available:
        hyp_signal = find_signal(evidence.financial, "hypothecation_active")
        disclosure = find_signal(evidence.financial, "seller_loan_disclosure_status")
        if (
            hyp_signal and hyp_signal.value is True
            and disclosure and isinstance(disclosure.value, dict)
            and disclosure.value.get("denied", False)
        ):
            contradictions.append(Contradiction(
                contradiction_id="CROSS_SELLER_CREDIBILITY_COLLAPSE",
                dimensions_involved=["financial", "ownership", "accident"],
                severity="critical",
                evidence_summary=(
                    "Seller denied having a loan, but RC shows active hypothecation. "
                    "The seller is demonstrably dishonest. All other seller claims "
                    "(about accidents, ownership, service) should be treated as unreliable."
                ),
            ))

    # ── Contradiction 2: Seller denied accidents vs insurance claims ──
    if evidence.accident.data_available:
        denial_signal = find_signal(evidence.accident, "seller_denial_vs_claims")
        major_claims = find_signal(evidence.accident, "major_claims_count")

        if (
            denial_signal and isinstance(denial_signal.value, dict)
            and denial_signal.value.get("seller_denied_accidents", False)
            and major_claims and major_claims.value > 0
        ):
            contradictions.append(Contradiction(
                contradiction_id="CROSS_SELLER_VS_INSURANCE",
                dimensions_involved=["accident"],
                severity="high",
                evidence_summary=(
                    f"Seller denied any accidents. Insurance records show "
                    f"{major_claims.value} major claim(s) above Rs.{MAJOR_CLAIM_THRESHOLD_INR:,}."
                ),
            ))

    # ── Contradiction 3: Insurance claim with no service record ──
    if evidence.accident.data_available and evidence.service.data_available:
        claim_matches = [s for s in evidence.accident.signals if s.name == "claim_service_match"]
        for match_signal in claim_matches:
            if isinstance(match_signal.value, dict):
                if not match_signal.value.get("service_entry_found", True):
                    claim_date = match_signal.value.get("claim_date", "unknown")
                    amount = match_signal.value.get("claim_amount", 0)
                    contradictions.append(Contradiction(
                        contradiction_id="CROSS_CLAIM_NO_SERVICE_ENTRY",
                        dimensions_involved=["accident", "service"],
                        severity="high",
                        evidence_summary=(
                            f"Insurance claim of Rs.{amount:,} filed on {claim_date}, "
                            f"but no service record found within {CLAIM_SERVICE_MATCH_WINDOW_DAYS} days. "
                            f"Repair was likely done outside authorized channels."
                        ),
                    ))

    # ── Contradiction 4: Odometer vs service frequency ──
    if evidence.odometer.data_available and evidence.service.data_available:
        stated_odo = next(
            (f for f in evidence.odometer.facts if f.field == "stated_odometer"), None
        )
        entry_count_fact = next(
            (f for f in evidence.service.facts if f.field == "service_entry_count"), None
        )
        span_signal = find_signal(evidence.service, "service_log_span_months")

        if stated_odo and entry_count_fact and span_signal:
            stated_km = stated_odo.value
            entries = entry_count_fact.value
            span_months = span_signal.value

            if span_months > 0:
                expected_entries = span_months / 6
                if entries > expected_entries * 1.5 and stated_km < 50000:
                    contradictions.append(Contradiction(
                        contradiction_id="CROSS_ODO_VS_SERVICE_FREQUENCY",
                        dimensions_involved=["odometer", "service"],
                        severity="medium",
                        evidence_summary=(
                            f"Odometer reads {stated_km:,} km over {span_months:.0f} months, "
                            f"but {entries} service entries suggest higher usage than "
                            f"the odometer indicates."
                        ),
                    ))

    return contradictions
