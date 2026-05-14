"""Phase 3: Cost estimation module (LLM + RAG)."""

import json
import logging
from typing import Any, Optional

from cartrust.reasoning.schemas import CostEstimate
from cartrust.schemas import VehicleEvidence

logger = logging.getLogger(__name__)


def generate_cost_estimate(
    vehicle_evidence: VehicleEvidence,
    knowledge_collection: Any,
    llm: Any,
    assessed_mileage: Optional[int] = None,
) -> Optional[CostEstimate]:
    """
    Generate a 3-year cost estimate using RAG knowledge + LLM.
    Returns None if LLM is unavailable or fails.
    """
    if llm is None:
        return None

    try:
        from cartrust.knowledge.rag import retrieve_knowledge
        from langchain.prompts import ChatPromptTemplate

        meta = vehicle_evidence.metadata
        mileage = assessed_mileage or next(
            (f.value for p in vehicle_evidence.all_packets
             for f in p.facts if f.field == "stated_odometer"),
            None,
        )

        cost_results = retrieve_knowledge(
            knowledge_collection,
            query=f"{meta.year} {meta.make} {meta.model} maintenance cost insurance resale value",
            n_results=4,
        )
        knowledge_text = "\n\n".join(r["text"] for r in cost_results) if cost_results else "No specific knowledge available."

        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "You are a used car cost estimation expert for the Indian market. "
                "Use the provided knowledge base to estimate costs. "
                "Never fabricate numbers — only use figures from the knowledge provided. "
                "If data is unavailable for a specific model, use general Indian market benchmarks."
            )),
            ("human", (
                "Vehicle: {year} {make} {model}\n"
                "Listing price: Rs. {listing_price}\n"
                "Assessed mileage: {mileage} km\n\n"
                "Knowledge base:\n{knowledge}\n\n"
                "Provide a 3-year ownership cost estimate as JSON with these fields:\n"
                "  - annual_maintenance_low: integer (INR)\n"
                "  - annual_maintenance_high: integer (INR)\n"
                "  - annual_insurance_estimate: integer (INR)\n"
                "  - total_3yr_low: integer (INR, 3 years maintenance + insurance)\n"
                "  - total_3yr_high: integer (INR)\n"
                "  - fair_market_value_low: integer (INR)\n"
                "  - fair_market_value_high: integer (INR)\n"
                "  - basis: string (cite the source document or benchmark used)\n\n"
                "Return ONLY valid JSON, no markdown fences."
            )),
        ])

        chain = prompt | llm
        result = chain.invoke({
            "year": meta.year,
            "make": meta.make,
            "model": meta.model,
            "listing_price": f"{meta.listing_price:,}" if meta.listing_price else "unknown",
            "mileage": f"{mileage:,}" if mileage else "unknown",
            "knowledge": knowledge_text,
        })

        content = result.content if hasattr(result, "content") else str(result)
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        data = json.loads(content)
        return CostEstimate(**data)

    except Exception as e:
        logger.warning(f"Cost estimate generation failed: {e}")
        return None
