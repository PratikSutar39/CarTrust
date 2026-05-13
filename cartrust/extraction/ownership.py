"""Phase 2: Ownership extraction module."""

import logging
from typing import Any, Dict, List

from cartrust.constants import EXTRACTION_CONFIDENCE, SOURCE_CONFIDENCE
from cartrust.schemas import EvidencePacket, Fact, Signal
from cartrust.utils import normalize, parse_date, today, years_between

logger = logging.getLogger(__name__)


def extract_ownership(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    """Extract ownership facts and signals. Never raises to caller."""
    try:
        return _extract_ownership(raw_inputs)
    except Exception as e:
        logger.error(f"Ownership extraction failed: {e}", exc_info=True)
        return EvidencePacket(
            dimension="ownership",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=["An error occurred during ownership data extraction."],
            data_available=False,
            notes=[f"Internal error: {type(e).__name__}: {str(e)}"],
        )


def _extract_ownership(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    facts: List[Fact] = []
    signals: List[Signal] = []
    observations: List[str] = []

    rc = raw_inputs.get("rc")
    listing = raw_inputs.get("listing") or {}
    seller_claims = raw_inputs.get("seller_claims") or {}

    if not rc:
        return EvidencePacket(
            dimension="ownership",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=["RC document was not provided."],
            data_available=False,
        )

    rc_owner_name = rc.get("owner_name")
    rc_owner_count = rc.get("owners_count")
    rc_first_reg = rc.get("first_registration_date")

    if rc_owner_name:
        facts.append(Fact(
            value=rc_owner_name,
            field="rc_owner_name",
            source_type="rc_document",
            source_detail="rc_main_record",
            source_confidence=SOURCE_CONFIDENCE["rc_document"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"Owner: {rc_owner_name}",
        ))
        observations.append(f"RC registered owner: {rc_owner_name}.")

    if rc_owner_count is not None:
        facts.append(Fact(
            value=rc_owner_count,
            field="rc_owner_count",
            source_type="rc_document",
            source_detail="rc_main_record",
            source_confidence=SOURCE_CONFIDENCE["rc_document"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"Number of owners: {rc_owner_count}",
        ))
        observations.append(f"RC shows {rc_owner_count} owner(s).")

    if rc_first_reg:
        facts.append(Fact(
            value=rc_first_reg,
            field="first_registration_date",
            source_type="rc_document",
            source_detail="rc_main_record",
            source_confidence=SOURCE_CONFIDENCE["rc_document"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"First registered: {rc_first_reg}",
        ))

    seller_name = listing.get("seller_name") or seller_claims.get("seller_name")
    seller_claimed_owners = seller_claims.get("owner_count")

    if seller_name:
        facts.append(Fact(
            value=seller_name,
            field="seller_name",
            source_type="listing",
            source_detail="listing_seller_info",
            source_confidence=SOURCE_CONFIDENCE["listing"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"Seller: {seller_name}",
        ))
        observations.append(f"Listing seller name: {seller_name}.")

    if seller_claimed_owners is not None:
        facts.append(Fact(
            value=seller_claimed_owners,
            field="seller_claimed_owner_count",
            source_type="seller_claim",
            source_detail="listing_description",
            source_confidence=SOURCE_CONFIDENCE["seller_claim"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"Seller claims: {seller_claimed_owners} owner(s)",
        ))
        observations.append(f"Seller claims {seller_claimed_owners} owner(s).")

    # Signal: name match
    if seller_name and rc_owner_name:
        names_match = normalize(seller_name) == normalize(rc_owner_name)
        signals.append(Signal(
            name="owner_name_match",
            value=names_match,
            confidence=0.90,
            basis=f"Compared normalized seller name '{seller_name}' to RC owner '{rc_owner_name}'.",
            source_facts=[f for f in facts if f.field in ("rc_owner_name", "seller_name")],
        ))
        observations.append(
            f"Seller name {'matches' if names_match else 'does not match'} RC owner name."
        )

    # Signal: owner count match
    if seller_claimed_owners is not None and rc_owner_count is not None:
        count_match = (seller_claimed_owners == rc_owner_count)
        signals.append(Signal(
            name="owner_count_match",
            value=count_match,
            confidence=0.90,
            basis=f"Seller claims {seller_claimed_owners}, RC shows {rc_owner_count}.",
            source_facts=[f for f in facts if "owner_count" in f.field],
        ))
        if not count_match:
            observations.append(
                f"Seller claims {seller_claimed_owners} owner(s), RC shows {rc_owner_count}."
            )

    # Signal: ownership velocity (owners per year)
    if rc_owner_count and rc_first_reg:
        years_since = years_between(rc_first_reg, today())
        if years_since > 0:
            velocity = rc_owner_count / years_since
            signals.append(Signal(
                name="ownership_velocity",
                value=round(velocity, 2),
                unit="owners_per_year",
                confidence=0.85,
                basis=f"{rc_owner_count} owners over {years_since:.1f} years = {velocity:.2f} owners/year.",
                source_facts=[f for f in facts if f.field in ("rc_owner_count", "first_registration_date")],
            ))
            observations.append(
                f"Ownership velocity: {velocity:.2f} owners/year ({rc_owner_count} in {years_since:.1f} years)."
            )

    coverage = (
        (0.50 * bool(rc))
        + (0.25 * bool(seller_name))
        + (0.25 * (seller_claimed_owners is not None))
    )

    return EvidencePacket(
        dimension="ownership",
        facts=facts,
        signals=signals,
        coverage=coverage,
        observations=observations,
        data_available=True,
    )
