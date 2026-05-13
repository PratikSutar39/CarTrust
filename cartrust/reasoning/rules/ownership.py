"""Phase 3 Rule Engine: Ownership assessor."""

import logging

from cartrust.constants import RAPID_FLIP_OWNER_THRESHOLD, RAPID_FLIP_YEARS_THRESHOLD
from cartrust.reasoning.rules.helpers import find_signal
from cartrust.reasoning.schemas import DimensionAssessment, Flag
from cartrust.schemas import EvidencePacket

logger = logging.getLogger(__name__)


def assess_ownership(evidence: EvidencePacket) -> DimensionAssessment:
    """Pure Python. No LLM. Reads ownership signals and applies deterministic rules."""
    try:
        return _assess_ownership(evidence)
    except Exception as e:
        logger.error(f"Ownership rule engine failed: {e}", exc_info=True)
        return DimensionAssessment(dimension="ownership", state="unverifiable", score=0.0)


def _assess_ownership(evidence: EvidencePacket) -> DimensionAssessment:
    if not evidence.data_available:
        return DimensionAssessment(dimension="ownership", state="unverifiable", score=0.0)

    flags = []
    score = 1.0

    # Rule 1: Owner name match
    name_match_signal = find_signal(evidence, "owner_name_match")
    if name_match_signal and name_match_signal.value is False:
        flags.append(Flag(
            flag_id="OWN_OWNER_NAME_MISMATCH",
            severity="high",
            evidence_summary=(
                f"Seller name does not match RC registered owner. "
                f"{name_match_signal.basis}"
            ),
            suggested_actions=[
                "Ask the seller to provide identification matching the RC owner name.",
                "If the seller is acting on behalf of the owner, request a notarized Power of Attorney.",
                "Do not transfer payment until the seller's authority to sell is verified.",
            ],
        ))
        score -= 0.40

    # Rule 2: Owner count match
    count_match_signal = find_signal(evidence, "owner_count_match")
    if count_match_signal and count_match_signal.value is False:
        flags.append(Flag(
            flag_id="OWN_OWNER_COUNT_UNDERSTATED",
            severity="medium",
            evidence_summary=(
                f"Seller's claimed owner count does not match RC. "
                f"{count_match_signal.basis}"
            ),
            suggested_actions=[
                "Ask the seller to clarify the ownership history.",
                "Verify RC details independently via the VAHAN portal.",
            ],
        ))
        score -= 0.20

    # Rule 3: Rapid flipping
    velocity_signal = find_signal(evidence, "ownership_velocity")
    if velocity_signal:
        velocity = velocity_signal.value
        rapid_flip_threshold = RAPID_FLIP_OWNER_THRESHOLD / RAPID_FLIP_YEARS_THRESHOLD
        if velocity >= rapid_flip_threshold:
            flags.append(Flag(
                flag_id="OWN_RAPID_FLIPPING",
                severity="medium",
                evidence_summary=(
                    f"Ownership velocity: {velocity} owners/year. "
                    f"{velocity_signal.basis}"
                ),
                suggested_actions=[
                    "Ask the current seller why they are selling so soon after purchase.",
                    "Get a thorough independent inspection — rapid turnover often hides issues.",
                ],
            ))
            score -= 0.20

    score = max(0.0, score)
    state = "verified_clean" if not flags else "verified_flagged"

    return DimensionAssessment(
        dimension="ownership",
        state=state,
        flags=flags,
        score=round(score, 2),
    )
