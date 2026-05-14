"""
FastAPI backend for CarTrust.
Exposes POST /assess — receives form data, runs the CarTrust pipeline,
returns a TrustReport as JSON.
"""

import os
import sys
import logging
from typing import List, Optional
from pathlib import Path

# Ensure the repo root is on the path so `cartrust` package is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CarTrust API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


# ── Request schema ────────────────────────────────────────────────────────────

class ServiceEntry(BaseModel):
    date: str = ""
    odometer: str = ""
    items: str = ""
    workshop: str = ""


class InsuranceClaim(BaseModel):
    year: str = ""
    amount: str = ""
    description: str = ""


class AssessRequest(BaseModel):
    make: str
    model: str
    year: str
    registration: str = ""
    listing_price: str = ""
    odometer_reading: str = ""
    rc_owner_name: str = ""
    rc_registration_date: str = ""
    rc_owner_count: str = "1"
    hypothecation_bank: str = ""
    service_entries: List[ServiceEntry] = []
    insurance_claims: List[InsuranceClaim] = []
    seller_claims_clean_history: bool = False
    seller_claims_single_owner: bool = False
    seller_loan_disclosure: str = "not_mentioned"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_raw_inputs(req: AssessRequest) -> dict:
    """Convert AssessRequest → raw_inputs dict for the extraction layer."""
    service_log = []
    for e in req.service_entries:
        if not e.date and not e.odometer and not e.items:
            continue
        entry: dict = {}
        if e.date:
            entry["date"] = e.date
        if e.odometer:
            try:
                entry["odometer_km"] = int(e.odometer)
            except ValueError:
                pass
        if e.items:
            entry["items"] = [i.strip() for i in e.items.split(",") if i.strip()]
        if e.workshop:
            entry["workshop"] = e.workshop
        service_log.append(entry)

    insurance_claims = []
    for c in req.insurance_claims:
        if not c.year and not c.amount:
            continue
        claim: dict = {}
        if c.year:
            try:
                claim["year"] = int(c.year)
            except ValueError:
                pass
        if c.amount:
            try:
                claim["amount"] = int(c.amount)
            except ValueError:
                pass
        if c.description:
            claim["description"] = c.description
        insurance_claims.append(claim)

    loan_map = {
        "not_mentioned": {"denied": False, "acknowledged": False, "closure_plan_provided": False},
        "denied": {"denied": True, "acknowledged": False, "closure_plan_provided": False},
        "acknowledged": {"denied": False, "acknowledged": True, "closure_plan_provided": False},
        "closure_plan": {"denied": False, "acknowledged": True, "closure_plan_provided": True},
    }

    raw: dict = {
        "make": req.make,
        "model": req.model,
        "year": int(req.year),
        "service_log": service_log,
        "insurance_claims": insurance_claims,
        "seller_claims_clean_history": req.seller_claims_clean_history,
        "seller_claims_single_owner": req.seller_claims_single_owner,
        "seller_loan_disclosure_status": loan_map.get(req.seller_loan_disclosure, loan_map["not_mentioned"]),
    }

    if req.registration:
        raw["registration_number"] = req.registration.upper()
    if req.listing_price:
        try:
            raw["listing_price"] = int(req.listing_price)
        except ValueError:
            pass
    if req.odometer_reading:
        try:
            raw["odometer_reading"] = int(req.odometer_reading)
        except ValueError:
            pass

    rc: dict = {}
    if req.rc_owner_name:
        rc["owner_name"] = req.rc_owner_name
    if req.rc_registration_date:
        rc["registration_date"] = req.rc_registration_date
    if req.rc_owner_count:
        try:
            rc["owner_count"] = int(req.rc_owner_count)
        except ValueError:
            pass
    if req.hypothecation_bank:
        rc["hypothecation"] = req.hypothecation_bank

    if rc:
        raw["rc_details"] = rc

    return raw


def _report_to_dict(report) -> dict:
    """Serialise TrustReport to JSON-safe dict."""
    assessments = []
    for a in report.assessments:
        flags = []
        for f in a.flags:
            flags.append({
                "flag_id": f.flag_id,
                "severity": f.severity,
                "description": f.description or f.evidence_summary,
                "evidence_summary": f.evidence_summary,
            })
        assessments.append({
            "dimension": a.dimension,
            "state": a.state,
            "score": a.score,
            "summary": a.summary,
            "reasoning": a.reasoning,
            "flags": flags,
        })

    contradictions = []
    for c in report.contradictions:
        contradictions.append({
            "contradiction_id": c.contradiction_id,
            "severity": c.severity,
            "dimensions_involved": c.dimensions_involved,
            "description": c.description or c.evidence_summary,
        })

    result: dict = {
        "registration_number": report.registration_number,
        "make": report.make,
        "model": report.model,
        "year": report.year,
        "listing_price": report.listing_price,
        "assessments": assessments,
        "contradictions": contradictions,
        "composite_score": report.composite_score,
        "coverage_ratio": report.coverage_ratio,
        "confidence_level": report.confidence_level,
        "verdict": report.verdict,
        "verdict_explanation": report.verdict_explanation,
        "action_checklist": report.action_checklist,
        "unverifiable_dimensions": report.unverifiable_dimensions,
        "unverifiable_explanation": report.unverifiable_explanation,
    }

    if report.cost_estimate:
        result["cost_estimate"] = {
            "total_low": report.cost_estimate.total_low,
            "total_high": report.cost_estimate.total_high,
            "currency": report.cost_estimate.currency,
        }

    return result


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "service": "CarTrust API",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "assess": "POST /assess",
        },
        "note": "This is the backend API. Deploy the frontend (frontend/) on Vercel and point CARTRUST_BACKEND_URL to this URL.",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/assess")
def assess(req: AssessRequest):
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    try:
        from datetime import datetime
        from cartrust.schemas import VehicleEvidence, VehicleMetadata
        from cartrust.extraction.ownership import extract_ownership
        from cartrust.extraction.odometer import extract_odometer
        from cartrust.extraction.accident import extract_accident
        from cartrust.extraction.financial import extract_financial
        from cartrust.extraction.service import extract_service
        from cartrust.reasoning.pipeline import build_trust_report
    except ImportError as e:
        logger.error("Import error: %s", e)
        raise HTTPException(status_code=500, detail=f"Backend import error: {e}")

    raw_inputs = _build_raw_inputs(req)
    logger.info("Assessing: %s %s %s", req.year, req.make, req.model)

    try:
        ownership_ep = extract_ownership(raw_inputs)
        odometer_ep = extract_odometer(raw_inputs)
        accident_ep = extract_accident(raw_inputs)
        financial_ep = extract_financial(raw_inputs)
        service_ep = extract_service(raw_inputs)

        listing_price = None
        if req.listing_price:
            try:
                listing_price = int(req.listing_price)
            except ValueError:
                pass

        metadata = VehicleMetadata(
            make=req.make,
            model=req.model,
            year=int(req.year),
            registration_number=req.registration.upper() if req.registration else None,
            listing_price=listing_price,
        )

        vehicle_evidence = VehicleEvidence(
            metadata=metadata,
            ownership=ownership_ep,
            odometer=odometer_ep,
            accident=accident_ep,
            financial=financial_ep,
            service=service_ep,
            extraction_timestamp=datetime.utcnow(),
        )
    except Exception as e:
        logger.error("Extraction error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Extraction error: {e}")

    try:
        # Load knowledge collection if available
        knowledge_collection = None
        kb_path = Path(__file__).parent.parent / "cartrust" / "knowledge" / "chroma_db"
        if kb_path.exists():
            try:
                import chromadb
                client = chromadb.PersistentClient(path=str(kb_path))
                knowledge_collection = client.get_or_create_collection("cartrust_kb")
            except Exception as e:
                logger.warning("Could not load knowledge base: %s", e)

        report = build_trust_report(
            vehicle_evidence=vehicle_evidence,
            llm=None,  # _get_llm() called internally if API key is set
            knowledge_collection=knowledge_collection,
        )
    except Exception as e:
        logger.error("Pipeline error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    return _report_to_dict(report)
