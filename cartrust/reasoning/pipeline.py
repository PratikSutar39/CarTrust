"""
Phase 3 Pipeline: Orchestrates all three reasoning layers into a TrustReport.

Layer 1: Deterministic rule engine (5 dimension assessors + contradictions)
Layer 2: RAG knowledge retrieval (selective — odometer, service, cost)
Layer 3: LLM explanation (explain_assessment, explain_contradiction, cost estimate)
"""

import logging
from typing import Any, Optional

from cartrust.schemas import VehicleEvidence
from cartrust.reasoning.schemas import TrustReport, DimensionAssessment
from cartrust.reasoning.rules.ownership import assess_ownership
from cartrust.reasoning.rules.odometer import assess_odometer
from cartrust.reasoning.rules.accident import assess_accident
from cartrust.reasoning.rules.financial import assess_financial
from cartrust.reasoning.rules.service import assess_service
from cartrust.reasoning.rules.contradictions import detect_contradictions
from cartrust.reasoning.scoring import compute_trust_score, compute_coverage
from cartrust.reasoning.verdict import determine_verdict, generate_action_checklist
from cartrust.reasoning.explainer import explain_assessment, explain_contradiction
from cartrust.reasoning.cost import generate_cost_estimate

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

    # ── Layer 1: Deterministic rule engine ─────────────────────────────────

    ownership_assessment = _safe_assess(assess_ownership, vehicle_evidence.ownership, "ownership")
    odometer_assessment = _safe_assess(assess_odometer, vehicle_evidence.odometer, "odometer")
    accident_assessment = _safe_assess(assess_accident, vehicle_evidence.accident, "accident")
    financial_assessment = _safe_assess(assess_financial, vehicle_evidence.financial, "financial")
    service_assessment = _safe_assess(assess_service, vehicle_evidence.service, "service")

    assessments = [
        ownership_assessment,
        odometer_assessment,
        accident_assessment,
        financial_assessment,
        service_assessment,
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

    # ── Layer 2: Selective RAG retrieval ───────────────────────────────────

    rag_contexts = {}
    for assessment in assessments:
        if assessment.dimension in _RAG_DIMENSIONS:
            rag_contexts[assessment.dimension] = _retrieve_rag_context(
                assessment.dimension, vehicle_evidence, knowledge_collection
            )

    # ── Layer 3: LLM explanations ──────────────────────────────────────────
    # Note: llm=None is valid — explainer falls back to evidence summaries.
    # Only auto-detect LLM if caller did not explicitly pass None.

    explained_assessments = []
    for assessment in assessments:
        try:
            rag_ctx = rag_contexts.get(assessment.dimension, "")
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


def _safe_assess(assess_fn, vehicle_evidence: VehicleEvidence, dimension: str) -> DimensionAssessment:
    """Call an assess_*() function; return a safe fallback on any exception."""
    try:
        return assess_fn(vehicle_evidence)
    except Exception as e:
        logger.error(f"Rule engine failed for {dimension}: {e}")
        return DimensionAssessment(
            dimension=dimension,
            state="unverifiable",
            flags=[],
            score=0.0,
            summary=f"{dimension.title()}: Assessment failed due to an internal error.",
            reasoning="The rule engine encountered an unexpected error for this dimension.",
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
