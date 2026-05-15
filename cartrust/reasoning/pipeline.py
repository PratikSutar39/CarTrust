"""
Phase 3 Pipeline: Orchestrates the reasoning layers into a TrustReport.

Layer 1+2: LLM-based dimension scoring (`llm_assessor`). The LLM reads the
           EvidencePacket from the extractors plus RAG snippets from the
           knowledge base (pricing, maintenance, insurance) and produces the
           DimensionAssessment (state, score, flags, summary, reasoning).
           Falls back to the deterministic rule engine when no LLM is
           available or a call fails.
Layer 3:   LLM explanation (only used when the rule fallback ran, since the
           LLM assessor already populates summary/reasoning).
Layer 4:   Contradiction detection (still rule-based) and cost estimation.
"""

import logging
from typing import Any, Optional

from cartrust.schemas import VehicleEvidence
from cartrust.reasoning.schemas import TrustReport
from cartrust.reasoning.rules.contradictions import detect_contradictions
from cartrust.reasoning.scoring import compute_trust_score, compute_coverage
from cartrust.reasoning.verdict import determine_verdict, generate_action_checklist
from cartrust.reasoning.explainer import explain_assessment, explain_contradiction, _get_llm
from cartrust.reasoning.cost import generate_cost_estimate
from cartrust.reasoning.llm_assessor import assess_dimension_with_llm

logger = logging.getLogger(__name__)

# Dimensions that benefit from RAG context
_RAG_DIMENSIONS = {"odometer", "service"}


def _retrieve_rag_context(dimension: str, vehicle_evidence: VehicleEvidence, knowledge_collection: Any) -> str:
    """Retrieve RAG knowledge for a specific dimension. Returns empty string if unavailable."""
    if knowledge_collection is None:
        return ""
    try:
        from cartrust.knowledge.rag import retrieve_knowledge
        meta = vehicle_evidence.metadata
        queries = {
            "odometer": f"{meta.year} {meta.make} {meta.model} odometer mileage reliability",
            "service": f"{meta.year} {meta.make} {meta.model} service maintenance schedule",
        }
        query = queries.get(dimension, "")
        if not query:
            return ""
        results = retrieve_knowledge(knowledge_collection, query=query, n_results=3)
        return "\n\n".join(r["text"] for r in results) if results else ""
    except Exception as e:
        logger.warning(f"RAG retrieval failed for {dimension}: {e}")
        return ""


def build_trust_report(
    vehicle_evidence: VehicleEvidence,
    llm: Any = None,
    knowledge_collection: Any = None,
) -> TrustReport:
    """
    Full reasoning pipeline: rules → RAG → LLM → TrustReport.

    Always returns a valid TrustReport — never raises.
    """
    meta = vehicle_evidence.metadata

    # Resolve LLM once — used for both dimension scoring AND explanation.
    if llm is None:
        llm = _get_llm()

    # ── Layer 1+2 combined: LLM scores each dimension using EvidencePackets
    #    + RAG context. Falls back to deterministic rules when LLM is
    #    unavailable or a call fails. ─────────────────────────────────────

    dimension_packets = [
        ("ownership", vehicle_evidence.ownership),
        ("odometer",  vehicle_evidence.odometer),
        ("accident",  vehicle_evidence.accident),
        ("financial", vehicle_evidence.financial),
        ("service",   vehicle_evidence.service),
    ]

    assessments = [
        assess_dimension_with_llm(
            dimension=dim,
            evidence_packet=packet,
            metadata=meta,
            knowledge_collection=knowledge_collection,
            llm=llm,
        )
        for dim, packet in dimension_packets
    ]

    contradictions = []
    try:
        contradictions = detect_contradictions(vehicle_evidence)
    except Exception as e:
        logger.warning(f"Contradiction detection failed: {e}")

    composite_score, has_hard_stop, confidence_level = compute_trust_score(assessments)
    coverage_ratio = compute_coverage(assessments)
    verdict = determine_verdict(composite_score, has_hard_stop, assessments)
    action_checklist = generate_action_checklist(assessments, contradictions)

    # ── Layer 3: LLM explanations ──────────────────────────────────────────
    # The LLM assessor (above) already populates summary, reasoning, and flag
    # descriptions. We only fall through to explain_assessment() when the
    # LLM was unavailable and the rule fallback ran — those assessments arrive
    # with empty summary text.

    explained_assessments = []
    for assessment in assessments:
        if assessment.summary and assessment.reasoning:
            # LLM already produced the explanation as part of scoring.
            explained_assessments.append(assessment)
            continue
        try:
            rag_ctx = _retrieve_rag_context(assessment.dimension, vehicle_evidence, knowledge_collection)
            explained = explain_assessment(assessment, rag_ctx, llm)
            explained_assessments.append(explained)
        except Exception as e:
            logger.warning(f"LLM explanation failed for {assessment.dimension}: {e}")
            explained_assessments.append(assessment)

    explained_contradictions = []
    for contradiction in contradictions:
        try:
            explained = explain_contradiction(contradiction, llm)
            explained_contradictions.append(explained)
        except Exception as e:
            logger.warning(f"LLM explanation failed for contradiction {contradiction.contradiction_id}: {e}")
            explained_contradictions.append(contradiction)

    # Cost estimate (RAG + LLM)
    assessed_mileage = None
    for p in vehicle_evidence.all_packets:
        if p.dimension == "odometer":
            for sig in p.signals:
                if sig.name == "median_implied_km":
                    assessed_mileage = int(sig.value)
                    break

    cost_estimate = None
    try:
        cost_estimate = generate_cost_estimate(vehicle_evidence, knowledge_collection, llm, assessed_mileage)
    except Exception as e:
        logger.warning(f"Cost estimate generation failed: {e}")

    # ── Assemble verdict explanation ───────────────────────────────────────

    verdict_explanation = _build_verdict_explanation(
        verdict, composite_score, has_hard_stop, explained_assessments, explained_contradictions
    )

    # ── Identify unverifiable dimensions ──────────────────────────────────

    unverifiable = [a.dimension for a in explained_assessments if a.state == "unverifiable"]
    unverifiable_explanation = (
        f"The following dimensions could not be verified due to missing data: {', '.join(unverifiable)}."
        if unverifiable else ""
    )

    return TrustReport(
        registration_number=meta.registration_number or "Unknown",
        make=meta.make,
        model=meta.model,
        year=meta.year,
        listing_price=meta.listing_price,
        assessments=explained_assessments,
        contradictions=explained_contradictions,
        composite_score=composite_score,
        coverage_ratio=coverage_ratio,
        confidence_level=confidence_level,
        verdict=verdict,
        verdict_explanation=verdict_explanation,
        action_checklist=action_checklist,
        cost_estimate=cost_estimate,
        unverifiable_dimensions=unverifiable,
        unverifiable_explanation=unverifiable_explanation,
    )


def _build_verdict_explanation(
    verdict: str,
    composite_score: float,
    has_hard_stop: bool,
    assessments: list,
    contradictions: list,
) -> str:
    """Build a 2-3 sentence verdict explanation from assessment results."""
    critical_dims = [a.dimension for a in assessments if a.state == "critical"]
    high_flags = [f for a in assessments for f in a.flags if f.severity in ("critical", "high")]

    if verdict == "WALK_AWAY":
        if critical_dims:
            dims_str = ", ".join(critical_dims)
            return (
                f"This vehicle has critical issues in: {dims_str}. "
                "These are deal-breaker problems that cannot be safely negotiated around. "
                "Do not proceed with this purchase."
            )
        return (
            f"The overall trust score of {composite_score:.0%} is too low to recommend this vehicle. "
            "Multiple significant issues were found across several dimensions. "
            "We strongly advise against purchasing this vehicle."
        )

    if verdict == "NEGOTIATE_WITH_SAFEGUARDS":
        return (
            f"This vehicle has an active financial encumbrance that must be resolved before purchase. "
            "Obtain a loan closure NOC and verify it with the lender directly before transferring ownership. "
            "Do not pay any money until the hypothecation is cleared."
        )

    if verdict == "NEGOTIATE":
        issues = [f.flag_id for f in high_flags[:3]]
        issues_str = ", ".join(issues) if issues else "some concerns"
        return (
            f"The vehicle scored {composite_score:.0%}, indicating it is potentially purchasable but has concerns ({issues_str}). "
            "Use the flagged issues to negotiate a price reduction. "
            "Ensure all action items in the checklist below are completed before finalising."
        )

    # BUY
    return (
        f"The vehicle scored {composite_score:.0%} with no critical issues found. "
        "Evidence across all verifiable dimensions is largely consistent. "
        "Proceed with standard due diligence before completing the purchase."
    )
