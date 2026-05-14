"""Phase 3 Rule Engine: Financial encumbrance assessor (3-state)."""

import logging

from cartrust.reasoning.rules.helpers import find_signal
from cartrust.reasoning.schemas import DimensionAssessment, Flag
from cartrust.schemas import EvidencePacket

logger = logging.getLogger(__name__)


def assess_financial(evidence: EvidencePacket) -> DimensionAssessment:
    """
    Pure Python. 3-state financial classification.
    Missing data is itself a critical gap because financial risk is existential.
    """
    try:
        return _assess_financial(evidence)
    except Exception as e:
        logger.error(f"Financial rule engine failed: {e}", exc_info=True)
        return DimensionAssessment(dimension="financial", state="unverifiable", score=0.0)


def _assess_financial(evidence: EvidencePacket) -> DimensionAssessment:
    if not evidence.data_available:
        return DimensionAssessment(
            dimension="financial",
            state="unverifiable",
            flags=[Flag(
                flag_id="FIN_UNVERIFIABLE_CRITICAL_GAP",
                severity="critical",
                evidence_summary="RC document not provided. Hypothecation status unknown.",
                suggested_actions=[
                    "Demand the original RC from the seller before any negotiation.",
                    "Independently verify hypothecation status via VAHAN portal or RTO.",
                ],
            )],
            score=0.0,
        )

    hyp_signal = find_signal(evidence, "hypothecation_active")
    disclosure_signal = find_signal(evidence, "seller_loan_disclosure_status")

    if not hyp_signal:
        return DimensionAssessment(
            dimension="financial",
            state="unverifiable",
            flags=[Flag(
                flag_id="FIN_UNVERIFIABLE_CRITICAL_GAP",
                severity="critical",
                evidence_summary="Hypothecation status could not be determined from available data.",
                suggested_actions=[
                    "Verify hypothecation status via VAHAN portal before proceeding.",
                ],
            )],
            score=0.0,
        )

    is_active = hyp_signal.value

    # State 1: Clean — no active hypothecation
    if not is_active:
        return DimensionAssessment(
            dimension="financial",
            state="verified_clean",
            flags=[],
            score=0.95,
        )

    # Hypothecation IS active — classify further
    seller_denied = False
    seller_acknowledged = False
    closure_plan = False

    if disclosure_signal and isinstance(disclosure_signal.value, dict):
        seller_denied = disclosure_signal.value.get("denied", False)
        seller_acknowledged = disclosure_signal.value.get("acknowledged", False)
        closure_plan = disclosure_signal.value.get("closure_plan_provided", False)

    lender_fact = next((f for f in evidence.facts if f.field == "lender_name"), None)
    lender_name = lender_fact.value if lender_fact else "an unknown lender"

    # State 2: Critical — seller denied or no clear resolution path
    if seller_denied:
        return DimensionAssessment(
            dimension="financial",
            state="critical",
            flags=[Flag(
                flag_id="FIN_UNDISCLOSED_LOAN",
                severity="critical",
                evidence_summary=(
                    f"RC shows active hypothecation with {lender_name}. "
                    f"Seller claimed vehicle was 'free of dues.' "
                    f"The seller is being dishonest about a legal encumbrance."
                ),
                suggested_actions=[
                    "Do not proceed with this transaction.",
                    "If the seller is willing to clear the loan and provide an NOC before any payment, re-evaluate.",
                    "Consider reporting the misleading listing to the marketplace.",
                ],
            )],
            score=0.0,
        )

    # State 3: Active-resolvable — disclosed with closure plan
    if seller_acknowledged and closure_plan:
        return DimensionAssessment(
            dimension="financial",
            state="active_resolvable",
            flags=[Flag(
                flag_id="FIN_ACTIVE_RESOLVABLE",
                severity="medium",
                evidence_summary=(
                    f"Active hypothecation with {lender_name}. "
                    f"Seller disclosed the loan and proposed a closure plan."
                ),
                suggested_actions=[
                    f"Use payment escrow — pay the loan amount directly to {lender_name}, not to the seller.",
                    f"Obtain the NOC from {lender_name} before paying the seller the balance.",
                    "Confirm lien removal on VAHAN within 7 days of NOC issuance.",
                    "Hold RC transfer until lien removal is confirmed.",
                    "Get all of the above in writing as part of the sale agreement.",
                ],
            )],
            score=0.50,
        )

    # Default: active but seller not clearly disclosing — treat as critical
    return DimensionAssessment(
        dimension="financial",
        state="critical",
        flags=[Flag(
            flag_id="FIN_UNDISCLOSED_LOAN",
            severity="critical",
            evidence_summary=(
                f"Active hypothecation with {lender_name}. "
                f"Seller has not adequately disclosed or addressed it."
            ),
            suggested_actions=[
                "Ask the seller directly about the loan and their proposed closure plan.",
                "Do not transfer payment until a written closure plan exists with lender confirmation.",
            ],
        )],
        score=0.0,
    )
