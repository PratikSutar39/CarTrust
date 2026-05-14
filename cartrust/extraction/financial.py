"""Phase 2: Financial encumbrance extraction module."""

import logging
from typing import Any, Dict, List

from cartrust.constants import EXTRACTION_CONFIDENCE, SOURCE_CONFIDENCE
from cartrust.schemas import EvidencePacket, Fact, Signal

logger = logging.getLogger(__name__)


def extract_financial(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    """Extract hypothecation/loan status evidence. Never raises to caller."""
    try:
        return _extract_financial(raw_inputs)
    except Exception as e:
        logger.error(f"Financial extraction failed: {e}", exc_info=True)
        return EvidencePacket(
            dimension="financial",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=["An error occurred during financial data extraction."],
            data_available=False,
            notes=[f"Internal error: {type(e).__name__}: {str(e)}"],
        )


def _extract_financial(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    facts: List[Fact] = []
    signals: List[Signal] = []
    observations: List[str] = []

    rc = raw_inputs.get("rc")
    listing = raw_inputs.get("listing") or {}
    seller_claims = raw_inputs.get("seller_claims") or {}

    if not rc:
        return EvidencePacket(
            dimension="financial",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=[
                "RC document was not provided. "
                "Hypothecation/loan status cannot be determined."
            ],
            data_available=False,
        )

    hypothecation = rc.get("hypothecation") or {}
    is_active = hypothecation.get("active", False)
    lender_name = hypothecation.get("lender")

    facts.append(Fact(
        value=is_active,
        field="hypothecation_active",
        source_type="rc_document",
        source_detail="rc_hypothecation_field",
        source_confidence=SOURCE_CONFIDENCE["rc_document"],
        extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
        raw_excerpt=f"Hypothecation: {'Active' if is_active else 'None'}",
    ))
    observations.append(
        f"RC hypothecation status: {'Active' if is_active else 'No hypothecation'}."
    )

    if lender_name:
        facts.append(Fact(
            value=lender_name,
            field="lender_name",
            source_type="rc_document",
            source_detail="rc_hypothecation_field",
            source_confidence=SOURCE_CONFIDENCE["rc_document"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"Lender: {lender_name}",
        ))
        observations.append(f"Lender on RC: {lender_name}.")

    seller_loan_status = seller_claims.get("loan_status")
    listing_description = listing.get("description", "")

    facts.append(Fact(
        value=seller_loan_status or "not stated",
        field="seller_loan_disclosure",
        source_type="seller_claim",
        source_detail="listing_description",
        source_confidence=SOURCE_CONFIDENCE["seller_claim"],
        extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
        raw_excerpt=f"Seller stated: '{seller_loan_status or 'nothing about loan status'}'",
    ))
    observations.append(f"Seller's loan disclosure: '{seller_loan_status or 'not stated'}'.")

    if listing_description:
        facts.append(Fact(
            value=listing_description,
            field="listing_description_text",
            source_type="listing",
            source_detail="listing_description",
            source_confidence=SOURCE_CONFIDENCE["listing"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=listing_description[:200],
        ))

    closure_plan = seller_claims.get("closure_plan")
    if closure_plan:
        facts.append(Fact(
            value=closure_plan,
            field="seller_closure_plan",
            source_type="seller_claim",
            source_detail="seller_communication",
            source_confidence=SOURCE_CONFIDENCE["seller_claim"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"Closure plan: {closure_plan}",
        ))
        observations.append(f"Seller proposed closure plan: {closure_plan}.")

    # Signal: hypothecation active boolean
    signals.append(Signal(
        name="hypothecation_active",
        value=is_active,
        confidence=0.95,
        basis=f"RC shows hypothecation {'active' if is_active else 'not active'}.",
    ))

    # Signal: seller disclosure status
    seller_denied = str(seller_loan_status or "").lower() in ("free of dues", "no loan", "no dues")
    seller_acknowledged = str(seller_loan_status or "").lower() == "active loan"
    signals.append(Signal(
        name="seller_loan_disclosure_status",
        value={
            "denied": seller_denied,
            "acknowledged": seller_acknowledged,
            "silent": not seller_denied and not seller_acknowledged,
            "closure_plan_provided": closure_plan is not None,
        },
        confidence=0.90,
        basis=(
            f"Seller {'denied loan' if seller_denied else 'acknowledged loan' if seller_acknowledged else 'was silent about loan'}. "
            f"Closure plan {'provided' if closure_plan else 'not provided'}."
        ),
    ))

    return EvidencePacket(
        dimension="financial",
        facts=facts,
        signals=signals,
        coverage=1.0,
        observations=observations,
        data_available=True,
    )
