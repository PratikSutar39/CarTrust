"""
LLM-based dimension assessor with RAG context.

Replaces the deterministic rule engine for per-dimension scoring.
The LLM receives:
  - The EvidencePacket (facts + signals computed by extractors)
  - Vehicle metadata (make/model/year/price)
  - RAG snippets from the knowledge base (pricing, maintenance, insurance)

…and produces the DimensionAssessment (state, score, flags, summary, reasoning).

Falls back to the deterministic rule assessor on any error so the pipeline
never raises and a report is always produced.
"""

import json
import logging
from typing import Any, Callable, Optional

from cartrust.schemas import EvidencePacket, VehicleMetadata
from cartrust.reasoning.schemas import DimensionAssessment, Flag
from cartrust.reasoning.explainer import _get_llm

logger = logging.getLogger(__name__)


# ── Per-dimension RAG query templates ────────────────────────────────────────

_RAG_QUERIES: dict[str, list[str]] = {
    "odometer": [
        "{year} {make} {model} expected average kilometers per year India",
        "odometer rollback detection multi-signal oil tyre brake",
    ],
    "service": [
        "{year} {make} {model} service schedule maintenance intervals",
        "general maintenance norms service gap stale records India",
    ],
    "accident": [
        "{year} {make} {model} insurance claim severity major repair benchmarks",
        "accident damage indicators flood frame structural India",
    ],
    "financial": [
        "{year} {make} {model} used car price India fair market value",
        "hypothecation loan transfer NOC bank closure used car",
    ],
    "ownership": [
        "{year} {make} {model} ownership history rapid flipping owner count",
    ],
}


# ── Per-dimension scoring guidance baked into the prompt ─────────────────────

_DIMENSION_GUIDANCE: dict[str, str] = {
    "odometer": (
        "Assess whether the stated odometer reading is truthful. Compare against "
        "implied-km signals from oil change cycles, tyre/brake replacement intervals, "
        "and vehicle age. Discrepancies >20% from the median implied reading suggest "
        "rollback (use 'critical' or 'verified_flagged'). 10–20% is suspicious "
        "('verified_flagged'). Below 10% with multiple signals is 'verified_clean'. "
        "If fewer than 2 signals exist → 'unverifiable'."
    ),
    "service": (
        "Assess service maintenance discipline. Long gaps (>12 months between "
        "consecutive services) or stale records (>18 months since the last service) "
        "lower the score. Authorised service centre records are stronger evidence "
        "than local garages. Consistent 6–12 month intervals at ASCs → 'verified_clean'. "
        "No service log → 'unverifiable'."
    ),
    "accident": (
        "Assess accident history risk. Insurance claims above Rs.50,000 indicate "
        "major incidents. Multiple claims compound severity. If the seller claims a "
        "clean history but a claim exists in the data → 'critical' (contradiction). "
        "Match claims against repair-cost benchmarks in the reference knowledge to "
        "judge whether damage was structural. No insurance data → 'unverifiable'."
    ),
    "financial": (
        "Assess financial encumbrance and pricing reasonableness. An active loan that "
        "the seller has NOT disclosed → 'critical' (undisclosed hypothecation). "
        "Active loan WITH a written closure plan → 'active_resolvable'. Seller denies "
        "loan and there is no contradicting evidence → 'verified_clean'. Use the "
        "pricing reference knowledge to flag if the asking price is >15% below fair "
        "market value (possible distress sale or hidden defect)."
    ),
    "ownership": (
        "Ownership cannot currently be verified without VAHAN/RC database access. "
        "Default to 'unverifiable' with score 0.5 unless the seller's own claim "
        "explicitly indicates more than 3 owners (then 'verified_flagged')."
    ),
}


# ── Allowed flag IDs per dimension (the LLM picks from these) ───────────────

_ALLOWED_FLAG_IDS: dict[str, list[str]] = {
    "odometer": [
        "ODO_MULTI_SIGNAL_DISCREPANCY",
        "ODO_MODERATE_DISCREPANCY",
        "ODO_LOW_USAGE_ANOMALY",
        "ODO_HIGH_USAGE_WEAR",
        "ODO_INSUFFICIENT_SIGNALS",
    ],
    "service": [
        "SVC_LONG_GAP",
        "SVC_STALE_RECORDS",
        "SVC_INCONSISTENT_CENTERS",
        "SVC_NO_RECORDS",
        "SVC_INCOMPLETE_HISTORY",
    ],
    "accident": [
        "ACC_MAJOR_CLAIM",
        "ACC_MULTIPLE_CLAIMS",
        "ACC_UNDISCLOSED_CLAIM",
        "ACC_STRUCTURAL_REPAIR_SUSPECTED",
        "ACC_NO_INSURANCE_DATA",
    ],
    "financial": [
        "FIN_UNDISCLOSED_LOAN",
        "FIN_ACTIVE_LOAN_WITH_PLAN",
        "FIN_PRICE_BELOW_MARKET",
        "FIN_PRICE_ABOVE_MARKET",
        "FIN_NO_LOAN_DISCLOSURE",
    ],
    "ownership": [
        "OWN_NO_RC_DATA",
        "OWN_MULTIPLE_OWNERS_CLAIMED",
    ],
}


# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior used-car appraiser for the Indian market with 20 years of experience. You assess ONE specific trust dimension of a used car based on the evidence packet and reference knowledge provided.

Your output is consumed by a downstream weighted-scoring engine that combines all dimensions. You MUST follow the JSON schema exactly — no markdown, no commentary outside the JSON.

Hard rules:
- Choose ONE state from the allowed values.
- Score is on [0.0, 1.0]: 1.0 = pristine, 0.5 = uncertain or unverifiable, 0.0 = catastrophic deal-breaker.
- Each flag MUST use a flag_id from the allowed list for this dimension.
- Severity controls how the dimension state is rolled up — be conservative about 'critical'; reserve it for genuine deal-breakers like undisclosed loans, confirmed odometer rollback, or hidden major accidents.
- Use the reference knowledge to ground numerical reasoning (average km/year, fair price, repair costs).
- All amounts are in Indian Rupees.
- NEVER invent facts not present in the evidence or reference knowledge.
- The buyer's name is Rahul, a 26-year-old first-time car buyer. Write descriptions for him.
"""


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_rule_fallback(dimension: str) -> Optional[Callable[[EvidencePacket], DimensionAssessment]]:
    """Return the deterministic rule assessor for this dimension."""
    if dimension == "ownership":
        from cartrust.reasoning.rules.ownership import assess_ownership
        return assess_ownership
    if dimension == "odometer":
        from cartrust.reasoning.rules.odometer import assess_odometer
        return assess_odometer
    if dimension == "accident":
        from cartrust.reasoning.rules.accident import assess_accident
        return assess_accident
    if dimension == "financial":
        from cartrust.reasoning.rules.financial import assess_financial
        return assess_financial
    if dimension == "service":
        from cartrust.reasoning.rules.service import assess_service
        return assess_service
    return None


def _build_rag_context(dimension: str, metadata: VehicleMetadata, kb: Any) -> str:
    """Pull the top RAG snippets for this dimension from the knowledge base."""
    if kb is None:
        return ""
    try:
        from cartrust.knowledge.rag import retrieve_knowledge
        templates = _RAG_QUERIES.get(dimension, [])
        chunks: list[str] = []
        for tpl in templates:
            q = tpl.format(year=metadata.year, make=metadata.make, model=metadata.model)
            results = retrieve_knowledge(kb, query=q, n_results=2)
            chunks.extend(r["text"] for r in results)
        # Dedupe while preserving order; cap at 4 chunks to stay token-efficient
        seen: set[str] = set()
        unique: list[str] = []
        for c in chunks:
            if c and c not in seen:
                seen.add(c)
                unique.append(c)
        return "\n\n---\n\n".join(unique[:4])
    except Exception as e:
        logger.warning(f"RAG retrieval failed for {dimension}: {e}")
        return ""


def _serialise_evidence(packet: EvidencePacket) -> dict:
    """Convert an EvidencePacket into a compact dict for the prompt."""
    return {
        "dimension": packet.dimension,
        "data_available": packet.data_available,
        "coverage": packet.coverage,
        "facts": [
            {
                "field": f.field,
                "value": f.value,
                "source": f.source_type,
                "source_confidence": f.source_confidence,
            }
            for f in packet.facts
        ],
        "signals": [
            {
                "name": s.name,
                "value": s.value,
                "unit": s.unit,
                "confidence": s.confidence,
                "basis": s.basis,
            }
            for s in packet.signals
        ],
        "observations": packet.observations,
    }


def _serialise_metadata(metadata: VehicleMetadata) -> dict:
    return {
        "make": metadata.make,
        "model": metadata.model,
        "year": metadata.year,
        "listing_price_inr": metadata.listing_price,
    }


def _strip_json_fences(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        # Remove leading fence and optional language tag
        content = content.split("```", 2)[1]
        if content.startswith("json"):
            content = content[4:]
        # Drop trailing fence if present
        if "```" in content:
            content = content.split("```", 1)[0]
    return content.strip()


def _coerce_assessment(parsed: dict, dimension: str) -> DimensionAssessment:
    """Validate and coerce the LLM JSON output into a DimensionAssessment."""
    valid_states = {"verified_clean", "verified_flagged", "unverifiable", "active_resolvable", "critical"}
    state = parsed.get("state", "unverifiable")
    if state not in valid_states:
        state = "unverifiable"

    score = parsed.get("score", 0.5)
    try:
        score = max(0.0, min(1.0, float(score)))
    except (TypeError, ValueError):
        score = 0.5

    allowed_ids = set(_ALLOWED_FLAG_IDS.get(dimension, []))
    flags: list[Flag] = []
    for raw_flag in parsed.get("flags", []) or []:
        if not isinstance(raw_flag, dict):
            continue
        flag_id = raw_flag.get("flag_id", "")
        # Allow any ID; warn if outside the allowed list but don't drop it
        severity = raw_flag.get("severity", "low")
        if severity not in {"low", "medium", "high", "critical"}:
            severity = "low"
        flags.append(Flag(
            flag_id=flag_id or f"{dimension.upper()}_GENERIC_FLAG",
            severity=severity,
            evidence_summary=raw_flag.get("evidence_summary", "") or raw_flag.get("description", ""),
            description=raw_flag.get("description", "") or raw_flag.get("evidence_summary", ""),
            suggested_actions=raw_flag.get("suggested_actions", []) or [],
        ))
        if allowed_ids and flag_id and flag_id not in allowed_ids:
            logger.debug(f"LLM produced unknown flag_id '{flag_id}' for {dimension}")

    return DimensionAssessment(
        dimension=dimension,
        state=state,
        score=score,
        flags=flags,
        summary=parsed.get("summary", "") or f"{dimension.title()}: assessment complete.",
        reasoning=parsed.get("reasoning", "") or "",
    )


# ── Public entry point ───────────────────────────────────────────────────────

def assess_dimension_with_llm(
    dimension: str,
    evidence_packet: EvidencePacket,
    metadata: VehicleMetadata,
    knowledge_collection: Any = None,
    llm: Any = None,
) -> DimensionAssessment:
    """
    Assess one trust dimension using the LLM with RAG context.

    Falls back to the deterministic rule engine on any failure.
    Always returns a valid DimensionAssessment.
    """
    if llm is None:
        llm = _get_llm()

    fallback = _get_rule_fallback(dimension)

    # No LLM available → use deterministic rules
    if llm is None:
        logger.info(f"No LLM available — using rule fallback for {dimension}.")
        if fallback:
            try:
                return fallback(evidence_packet)
            except Exception as e:
                logger.error(f"Rule fallback failed for {dimension}: {e}")
        return DimensionAssessment(
            dimension=dimension,
            state="unverifiable",
            flags=[],
            score=0.5,
            summary=f"{dimension.title()}: assessment unavailable.",
            reasoning="Neither LLM nor rule fallback could assess this dimension.",
        )

    # Build prompt context
    rag_context = _build_rag_context(dimension, metadata, knowledge_collection)
    evidence_json = json.dumps(_serialise_evidence(evidence_packet), indent=2, default=str)
    metadata_json = json.dumps(_serialise_metadata(metadata), indent=2)
    guidance = _DIMENSION_GUIDANCE.get(dimension, "Use general appraisal best practice.")
    allowed_flags = _ALLOWED_FLAG_IDS.get(dimension, [])

    user_prompt = f"""Dimension to assess: **{dimension}**

Vehicle:
{metadata_json}

Evidence packet (facts + signals from extractors):
{evidence_json}

Reference knowledge (RAG):
{rag_context if rag_context else "No reference knowledge available for this query."}

Scoring guidance for this dimension:
{guidance}

Allowed flag_id values for this dimension:
{json.dumps(allowed_flags)}

Respond with a JSON object that matches this schema EXACTLY (no markdown, no extra keys):
{{
  "state": "verified_clean" | "verified_flagged" | "unverifiable" | "active_resolvable" | "critical",
  "score": <float between 0.0 and 1.0>,
  "summary": "<one sentence for the dimension row>",
  "reasoning": "<2-3 sentence explanation citing specific numbers from the evidence and reference knowledge>",
  "flags": [
    {{
      "flag_id": "<one of the allowed IDs above>",
      "severity": "low" | "medium" | "high" | "critical",
      "evidence_summary": "<technical one-liner with the numbers>",
      "description": "<2-3 plain-language sentences for Rahul>",
      "suggested_actions": ["<short actionable step>", "..."]
    }}
  ]
}}

If everything looks clean, return state=verified_clean with an empty flags array. If data is missing, return state=unverifiable. Return ONLY the JSON object."""

    try:
        from langchain.prompts import ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", user_prompt),
        ])
        chain = prompt | llm
        result = chain.invoke({})
        content = result.content if hasattr(result, "content") else str(result)
        content = _strip_json_fences(content)
        parsed = json.loads(content)
        return _coerce_assessment(parsed, dimension)

    except Exception as e:
        logger.warning(f"LLM assessment failed for {dimension}: {e}. Falling back to rules.")
        if fallback:
            try:
                return fallback(evidence_packet)
            except Exception as fe:
                logger.error(f"Rule fallback also failed for {dimension}: {fe}")
        return DimensionAssessment(
            dimension=dimension,
            state="unverifiable",
            flags=[],
            score=0.5,
            summary=f"{dimension.title()}: assessment failed.",
            reasoning=f"Both LLM and rule engine failed: {type(e).__name__}.",
        )
