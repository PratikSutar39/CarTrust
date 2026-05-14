"""Phase 3 Rule Engine: Service history assessor."""

import logging

from cartrust.constants import SERVICE_GAP_THRESHOLD_MONTHS, SERVICE_STALE_THRESHOLD_MONTHS
from cartrust.reasoning.rules.helpers import find_signal
from cartrust.reasoning.schemas import DimensionAssessment, Flag
from cartrust.schemas import EvidencePacket

logger = logging.getLogger(__name__)


def assess_service(evidence: EvidencePacket) -> DimensionAssessment:
    """Pure Python. Evaluates service regularity and gaps."""
    try:
        return _assess_service(evidence)
    except Exception as e:
        logger.error(f"Service rule engine failed: {e}", exc_info=True)
        return DimensionAssessment(dimension="service", state="unverifiable", score=0.0)


def _assess_service(evidence: EvidencePacket) -> DimensionAssessment:
    if not evidence.data_available:
        return DimensionAssessment(
            dimension="service",
            state="unverifiable",
            flags=[Flag(
                flag_id="SVC_NO_RECORDS",
                severity="medium",
                evidence_summary="No service records provided.",
                suggested_actions=[
                    "Ask the seller for all service receipts.",
                    "Request contact details of the service center used.",
                    "Factor higher maintenance risk into price negotiation.",
                ],
            )],
            score=0.0,
        )

    flags = []
    score = 1.0

    # Rule 1: Long service gaps
    long_gaps_signal = find_signal(evidence, "long_service_gaps")
    if long_gaps_signal and long_gaps_signal.value:
        gap_count = len(long_gaps_signal.value)
        gap_details = "; ".join(
            f"{g['from']} to {g['to']} ({g['months']} months)"
            for g in long_gaps_signal.value
        )
        flags.append(Flag(
            flag_id="SVC_GAP_OVER_12_MONTHS",
            severity="medium",
            evidence_summary=(
                f"{gap_count} service gap(s) exceeding {SERVICE_GAP_THRESHOLD_MONTHS} months: "
                f"{gap_details}."
            ),
            suggested_actions=[
                "Ask the seller about maintenance during the gap periods.",
                "Get an inspection focusing on components that degrade without maintenance (engine oil, coolant, belts).",
            ],
        ))
        score -= 0.20 * gap_count

    # Rule 2: Stale records
    stale_signal = find_signal(evidence, "months_since_last_service")
    if stale_signal and stale_signal.value > SERVICE_STALE_THRESHOLD_MONTHS:
        flags.append(Flag(
            flag_id="SVC_STALE",
            severity="low",
            evidence_summary=f"Last recorded service was {stale_signal.value:.1f} months ago.",
            suggested_actions=[
                "Ask the seller why service was discontinued.",
                "Plan for a comprehensive service immediately after purchase.",
            ],
        ))
        score -= 0.10

    # Rule 3: Switch from authorized to local garage
    centers_signal = find_signal(evidence, "service_centers_used")
    if centers_signal and isinstance(centers_signal.value, list):
        centers = centers_signal.value
        authorized_keywords = ("authorized", "maruti", "honda", "hyundai", "toyota", "tata", "ford", "volkswagen")
        has_authorized = any(
            any(kw in c.lower() for kw in authorized_keywords)
            for c in centers
        )
        has_local = any("local" in c.lower() or "garage" in c.lower() for c in centers)
        if has_authorized and has_local and len(centers) >= 2:
            flags.append(Flag(
                flag_id="SVC_CENTER_CHANGE",
                severity="low",
                evidence_summary=(
                    f"Service switched from authorized center to local garage. "
                    f"Centers used: {', '.join(centers)}."
                ),
                suggested_actions=[
                    "Verify that critical maintenance milestones were performed at authorized centers.",
                ],
            ))
            score -= 0.05

    score = max(0.0, score)
    state = "verified_clean" if not flags else "verified_flagged"

    return DimensionAssessment(
        dimension="service",
        state=state,
        flags=flags,
        score=round(score, 2),
    )
