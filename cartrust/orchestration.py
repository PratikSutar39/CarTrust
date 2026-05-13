"""
CarTrust Orchestration

Loads vehicle inputs from disk and runs all extraction modules
to produce a VehicleEvidence object ready for Phase 3 reasoning.
"""

import json
from datetime import datetime
from pathlib import Path

from cartrust.extraction import (
    extract_accident,
    extract_financial,
    extract_odometer,
    extract_ownership,
    extract_service,
)
from cartrust.schemas import VehicleEvidence, VehicleMetadata


def load_vehicle_inputs(vehicle_dir) -> dict:
    """Load all sample files for one vehicle into a single dictionary."""
    vehicle_dir = Path(vehicle_dir)
    inputs = {}

    listing_path = vehicle_dir / "listing.json"
    if listing_path.exists():
        inputs["listing"] = json.loads(listing_path.read_text())
        inputs["seller_claims"] = inputs["listing"].get("seller_claims", {})

    rc_path = vehicle_dir / "rc.json"
    if rc_path.exists():
        inputs["rc"] = json.loads(rc_path.read_text())

    service_path = vehicle_dir / "service_log.json"
    if service_path.exists():
        inputs["service_log"] = json.loads(service_path.read_text())

    insurance_path = vehicle_dir / "insurance.json"
    if insurance_path.exists():
        inputs["insurance"] = json.loads(insurance_path.read_text())

    if "listing" in inputs:
        year = inputs["listing"].get("year")
        if year:
            inputs["vehicle_age_years"] = datetime.now().year - year

    return inputs


def build_vehicle_evidence(vehicle_dir) -> VehicleEvidence:
    """Run all extraction modules and assemble VehicleEvidence."""
    inputs = load_vehicle_inputs(vehicle_dir)
    listing = inputs.get("listing") or {}

    metadata = VehicleMetadata(
        make=listing.get("make", "Unknown"),
        model=listing.get("model", "Unknown"),
        year=listing.get("year", 0),
        registration_number=inputs.get("rc", {}).get("registration_number"),
        listing_price=listing.get("asking_price"),
    )

    return VehicleEvidence(
        metadata=metadata,
        ownership=extract_ownership(inputs),
        odometer=extract_odometer(inputs),
        accident=extract_accident(inputs),
        financial=extract_financial(inputs),
        service=extract_service(inputs),
        extraction_timestamp=datetime.now(),
    )
