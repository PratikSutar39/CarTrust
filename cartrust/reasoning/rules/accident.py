"""Phase 3 Rule Engine: Accident history assessor."""

import logging

from cartrust.constants import MAJOR_CLAIM_THRESHOLD_INR
from cartrust.reasoning.rules.helpers import find_signal
from cartrust.reasoning.schemas import DimensionAssessment, Flag
from cartrust.schemas import EvidencePacket

logger = logging.getLogger(__name__)


def assess_accident(evidence: EvidencePacket) -> DimensionAssessment:
    """Pure Python. Checks insurance claims against seller disclosure."""
    try:
        return _assess_accident(evidence)
    except Exception as e:
        logger.error(f"Accident rule engine failed: {e}", exc_info=True)
        return DimensionAssessment(dimension="accident", state="unverifiable", score=0.0)


def _assess_accident(evidence: EvidencePacket) -> DimensionAssessment:
    if not evidence.data_available:
        return DimensionAssessment(dimension="accident", state="unverifiable", score=0.0)

    major_claims_signal = find_signal(evidence, "major_claims_count")
    seller_denial_signal = find_signal(evidence, "seller_denial_vs_claims")
    claim_match_signals = [s for s in evidence.signals if s.name == "claim_service_match"]
    max_claim_signal = find_signal(evidence, "max_claim_amount")

    major_count = major_claims_signal.value if major_claims_signal else 0

    if major_count == 0:
        return DimensionAssessment(
            dimension="accident",
            state="verified_clean",
            flags=[],
            score=0.95,
        )

    # Major claims exist — check seller disclosure
    seller_denied = False
    if seller_denial_signal and isinstance(seller_denial_signal.value, dict):
        seller_denied = seller_denial_signal.value.get("seller_denied_accidents", False)

    max_amount = max_claim_signal.value if max_claim_signal else 0

    flags = []

    if seller_denied:
        evidence_parts = [
            "Seller denied any accidents.",
            f"{major_count} major claim(s) above Rs.{MAJOR_CLAIM_THRESHOLD_INR:,} found in insurance records.",
            f"Largest claim: Rs.{max_amount:,}.",
        ]
        for match_signal in claim_match_signals:
            if isinstance(match_signal.value, dict):
                claim_date = match_signal.value.get("claim_date", "unknown")
                service_found = match_signal.value.get("service_entry_found", False)
                amount = match_signal.value.get("claim_amount", 0)
                if not service_found:
                    evidence_parts.append(
                        f"Claim of Rs.{amount:,} on {claim_date}: no corresponding service record found."
                    )
        flags.append(Flag(
            flag_id="ACC_UNDISCLOSED_MAJOR_CLAIM",
            severity="high",
            evidence_summary=" ".join(evidence_parts),
            suggested_actions=[
                "Ask the seller about the insurance claim(s) — date, amount, and nature of incident.",
                "Request the claim settlement document from the insurer.",
                "Get an independent structural inspection focused on frame alignment and undercarriage.",
                "Verify repair quality at an authorized service center.",
            ],
        ))
        score = 0.20
    else:
        flags.append(Flag(
            flag_id="ACC_MAJOR_CLAIM_DISCLOSED",
            severity="medium",
            evidence_summary=(
                f"{major_count} major insurance claim(s) on record. "
                f"Largest: Rs.{max_amount:,}. "
                f"Seller disclosure appears consistent."
            ),
            suggested_actions=[
                "Request details of the nature of each incident and repairs done.",
                "Get an independent inspection to verify repair quality.",
            ],
        ))
        score = 0.65

    return DimensionAssessment(
        dimension="accident",
        state="verified_flagged",
        flags=flags,
        score=round(score, 2),
    )
