"""Phase 2: Accident history extraction module."""

import logging
from typing import Any, Dict, List

from cartrust.constants import (
    CLAIM_SERVICE_MATCH_WINDOW_DAYS,
    EXTRACTION_CONFIDENCE,
    MAJOR_CLAIM_THRESHOLD_INR,
    SOURCE_CONFIDENCE,
)
from cartrust.schemas import EvidencePacket, Fact, Signal
from cartrust.utils import find_service_entry_near_date, parse_date

logger = logging.getLogger(__name__)


def extract_accident(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    """Extract accident and insurance claim evidence. Never raises to caller."""
    try:
        return _extract_accident(raw_inputs)
    except Exception as e:
        logger.error(f"Accident extraction failed: {e}", exc_info=True)
        return EvidencePacket(
            dimension="accident",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=["An error occurred during accident data extraction."],
            data_available=False,
            notes=[f"Internal error: {type(e).__name__}: {str(e)}"],
        )


def _extract_accident(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    facts: List[Fact] = []
    signals: List[Signal] = []
    observations: List[str] = []

    insurance = raw_inputs.get("insurance")
    service_log = raw_inputs.get("service_log") or []
    seller_claims = raw_inputs.get("seller_claims") or {}

    if not insurance:
        return EvidencePacket(
            dimension="accident",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=["Insurance data was not provided."],
            data_available=False,
        )

    claims = insurance.get("claims") or []

    for claim in claims:
        amount = claim.get("amount", 0)
        date = claim.get("date")
        facts.append(Fact(
            value=amount,
            field="insurance_claim_amount",
            unit="INR",
            source_type="insurance_record",
            source_detail=f"claim_{claim.get('id', 'unknown')}",
            source_confidence=SOURCE_CONFIDENCE["insurance_record"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            timestamp=parse_date(date),
            raw_excerpt=f"Claim of Rs.{amount:,} on {date}",
        ))
        observations.append(f"Insurance claim: Rs.{amount:,} on {date}.")

    seller_accident_text = seller_claims.get("accidents") or ""
    facts.append(Fact(
        value=seller_accident_text or "not stated",
        field="seller_accident_disclosure",
        source_type="seller_claim",
        source_detail="listing_description",
        source_confidence=SOURCE_CONFIDENCE["seller_claim"],
        extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
        raw_excerpt=f"Seller stated about accidents: '{seller_accident_text or 'nothing'}'",
    ))
    observations.append(f"Seller's accident disclosure: '{seller_accident_text or 'not stated'}'.")

    # Signal: total claim count
    signals.append(Signal(
        name="total_claim_count",
        value=len(claims),
        unit="count",
        confidence=0.90,
        basis=f"{len(claims)} claims found in insurance records.",
    ))

    # Signal: max single claim amount
    if claims:
        max_claim = max(c.get("amount", 0) for c in claims)
        signals.append(Signal(
            name="max_claim_amount",
            value=max_claim,
            unit="INR",
            confidence=0.90,
            basis=f"Largest single claim: Rs.{max_claim:,}.",
        ))
        observations.append(f"Largest single claim: Rs.{max_claim:,}.")

    # Signal: major claims count
    major_count = sum(1 for c in claims if c.get("amount", 0) >= MAJOR_CLAIM_THRESHOLD_INR)
    signals.append(Signal(
        name="major_claims_count",
        value=major_count,
        unit="count",
        confidence=0.90,
        basis=f"{major_count} claims above Rs.{MAJOR_CLAIM_THRESHOLD_INR:,} threshold.",
    ))
    if major_count > 0:
        observations.append(f"{major_count} claim(s) above Rs.{MAJOR_CLAIM_THRESHOLD_INR:,}.")

    # Signal: claim-service match for each major claim
    for claim in claims:
        if claim.get("amount", 0) >= MAJOR_CLAIM_THRESHOLD_INR:
            claim_date = claim.get("date")
            match = find_service_entry_near_date(
                service_log, claim_date, CLAIM_SERVICE_MATCH_WINDOW_DAYS
            )
            signals.append(Signal(
                name="claim_service_match",
                value={
                    "claim_date": claim_date,
                    "claim_amount": claim.get("amount"),
                    "service_entry_found": match is not None,
                    "matching_service_date": match.get("date") if match else None,
                },
                confidence=0.85,
                basis=(
                    f"Checked for service entry within {CLAIM_SERVICE_MATCH_WINDOW_DAYS} days "
                    f"of Rs.{claim.get('amount', 0):,} claim on {claim_date}. "
                    f"{'Match found.' if match else 'No match found.'}"
                ),
            ))
            observations.append(
                f"Claim on {claim_date} (Rs.{claim.get('amount', 0):,}): "
                f"{'corresponding service entry found' if match else 'no corresponding service entry found'}."
            )

    # Signal: seller denial vs claims
    seller_denied = str(seller_accident_text).lower() in ("none", "no", "no accidents")
    signals.append(Signal(
        name="seller_denial_vs_claims",
        value={
            "seller_denied_accidents": seller_denied,
            "claims_exist": len(claims) > 0,
            "major_claims_exist": major_count > 0,
        },
        confidence=0.90,
        basis=(
            f"Seller {'denied' if seller_denied else 'did not deny'} accidents. "
            f"{len(claims)} claim(s) on record, {major_count} major."
        ),
    ))

    return EvidencePacket(
        dimension="accident",
        facts=facts,
        signals=signals,
        coverage=1.0,
        observations=observations,
        data_available=True,
    )
