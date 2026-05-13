"""
Phase 3 Layer 3: LLM Explanation Layer

This is the ONLY file in reasoning/ that imports LangChain or an LLM SDK.
It takes pre-computed rule engine outputs and writes plain-language descriptions.
"""

import json
import logging
from typing import Any, List

from cartrust.reasoning.schemas import Contradiction, DimensionAssessment

logger = logging.getLogger(__name__)

EXPLANATION_SYSTEM_PROMPT = """You are a report writer for a used car trust assessment system in India.

You receive pre-computed assessment results (flags, severity levels, evidence summaries) and your ONLY job is to write clear, plain-language explanations that a first-time car buyer can understand.

Rules:
- Do NOT change the severity, state, or score. These are already decided.
- Do NOT add new flags or remove existing ones.
- Write each flag description as 2-3 sentences in plain language.
- Use specific numbers and facts from the evidence_summary.
- Never use technical jargon without explaining it.
- Never invent facts not in the evidence_summary.
- The buyer's name is Rahul. He is 26 and buying his first car.
- Amounts are in Indian Rupees (Rs. or INR).
"""


def _get_llm():
    """Lazy-load the LLM based on available API keys.

    Checks (in order): Streamlit secrets, .env file, environment variables.
    """
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    def _secret(name: str) -> str:
        """Read from Streamlit secrets first, fall back to env var."""
        try:
            import streamlit as st
            return st.secrets.get(name, "") or os.getenv(name, "")
        except Exception:
            return os.getenv(name, "")

    openrouter_key = _secret("OPENROUTER_API_KEY")
    openai_key = _secret("OPENAI_API_KEY")
    anthropic_key = _secret("ANTHROPIC_API_KEY")

    if openrouter_key and openrouter_key.startswith("sk-or-"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="openai/gpt-oss-120b:free",
            openai_api_key=openrouter_key,
            openai_api_base="https://openrouter.ai/api/v1",
            temperature=0.1,
        )
    elif openai_key and openai_key.startswith("sk-"):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o", temperature=0.1)
    elif anthropic_key:
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model="claude-sonnet-4-6", temperature=0.1)
    else:
        logger.warning("No LLM API key found. Explanations will use evidence summaries.")
        return None


def explain_assessment(
    assessment: DimensionAssessment,
    rag_context: str,
    llm: Any = None,
) -> DimensionAssessment:
    """
    Fills in plain-language descriptions for a DimensionAssessment.
    If LLM is unavailable, falls back to evidence_summary.
    """
    if llm is None:
        llm = _get_llm()

    # Clean states need no LLM explanation
    if not assessment.flags and assessment.state == "verified_clean":
        assessment.summary = f"{assessment.dimension.title()}: No issues found."
        assessment.reasoning = "All available evidence is consistent and verified."
        return assessment

    if assessment.state == "unverifiable" and not assessment.flags:
        assessment.summary = f"{assessment.dimension.title()}: Could not be verified."
        assessment.reasoning = "Insufficient data was available to assess this dimension."
        return assessment

    if llm is None:
        # Fallback: use evidence_summary
        assessment.summary = f"{assessment.dimension.title()}: {assessment.state.replace('_', ' ')}."
        assessment.reasoning = "LLM explanation unavailable. See flag evidence summaries below."
        for flag in assessment.flags:
            flag.description = flag.evidence_summary
        return assessment

    try:
        from langchain.prompts import ChatPromptTemplate

        flags_input = [
            {
                "flag_id": flag.flag_id,
                "severity": flag.severity,
                "evidence_summary": flag.evidence_summary,
            }
            for flag in assessment.flags
        ]

        prompt = ChatPromptTemplate.from_messages([
            ("system", EXPLANATION_SYSTEM_PROMPT),
            ("human", (
                "Dimension: {dimension}\n"
                "State: {state}\n"
                "Score: {score}\n\n"
                "Flags to explain:\n{flags_json}\n\n"
                "Reference knowledge (if relevant):\n{rag_context}\n\n"
                "Respond with a JSON object with these fields:\n"
                "  - summary: one sentence for the dimension row\n"
                "  - reasoning: 2-3 sentences explaining the overall assessment\n"
                "  - flag_descriptions: array of plain-language descriptions, one per flag (same order)\n\n"
                "Return ONLY valid JSON, no markdown fences."
            )),
        ])

        chain = prompt | llm
        result = chain.invoke({
            "dimension": assessment.dimension,
            "state": assessment.state,
            "score": assessment.score,
            "flags_json": json.dumps(flags_input, indent=2),
            "rag_context": rag_context or "No reference knowledge available.",
        })

        content = result.content if hasattr(result, "content") else str(result)
        # Strip markdown code fences if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        parsed = json.loads(content)
        assessment.summary = parsed.get("summary", "")
        assessment.reasoning = parsed.get("reasoning", "")
        flag_descriptions = parsed.get("flag_descriptions", [])
        for i, desc in enumerate(flag_descriptions):
            if i < len(assessment.flags):
                assessment.flags[i].description = desc

    except Exception as e:
        logger.warning(f"LLM explanation failed for {assessment.dimension}: {e}")
        assessment.summary = f"{assessment.dimension.title()}: {assessment.state.replace('_', ' ')}."
        assessment.reasoning = "LLM explanation unavailable. See flag evidence summaries."
        for flag in assessment.flags:
            if not flag.description:
                flag.description = flag.evidence_summary

    return assessment


def explain_contradiction(contradiction: Contradiction, llm: Any = None) -> Contradiction:
    """Writes a plain-language description for a detected contradiction."""
    if llm is None:
        llm = _get_llm()

    if llm is None:
        contradiction.description = contradiction.evidence_summary
        return contradiction

    try:
        from langchain.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", EXPLANATION_SYSTEM_PROMPT),
            ("human", (
                "A contradiction was detected between these dimensions: {dims}\n"
                "Severity: {severity}\n"
                "Technical evidence: {evidence}\n\n"
                "Write a 2-3 sentence plain-language explanation of this contradiction "
                "for a first-time Indian car buyer named Rahul. "
                "Return ONLY the explanation text, no JSON, no markdown."
            )),
        ])

        chain = prompt | llm
        result = chain.invoke({
            "dims": ", ".join(contradiction.dimensions_involved),
            "severity": contradiction.severity,
            "evidence": contradiction.evidence_summary,
        })
        contradiction.description = result.content if hasattr(result, "content") else str(result)

    except Exception as e:
        logger.warning(f"LLM explanation failed for contradiction {contradiction.contradiction_id}: {e}")
        contradiction.description = contradiction.evidence_summary

    return contradiction
