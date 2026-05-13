"""Phase 2: Odometer extraction module (multi-signal)."""

import logging
import statistics
from typing import Any, Dict, List

from cartrust.constants import (
    AVERAGE_ANNUAL_KM_INDIA,
    BRAKE_REPLACEMENT_INTERVAL_KM,
    EXTRACTION_CONFIDENCE,
    MIN_ODOMETER_SIGNALS,
    ODOMETER_SIGNAL_CONFIDENCE,
    OIL_CHANGE_INTERVAL_KM,
    SOURCE_CONFIDENCE,
    TYRE_REPLACEMENT_INTERVAL_KM,
)
from cartrust.schemas import EvidencePacket, Fact, Signal

logger = logging.getLogger(__name__)


def extract_odometer(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    """Extract odometer facts and multi-signal estimation signals. Never raises to caller."""
    try:
        return _extract_odometer(raw_inputs)
    except Exception as e:
        logger.error(f"Odometer extraction failed: {e}", exc_info=True)
        return EvidencePacket(
            dimension="odometer",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=["An error occurred during odometer data extraction."],
            data_available=False,
            notes=[f"Internal error: {type(e).__name__}: {str(e)}"],
        )


def _extract_odometer(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    facts: List[Fact] = []
    signals: List[Signal] = []
    observations: List[str] = []

    listing = raw_inputs.get("listing") or {}
    service_log = raw_inputs.get("service_log") or []
    insurance = raw_inputs.get("insurance") or {}
    vehicle_age_years = raw_inputs.get("vehicle_age_years")

    stated_odometer = listing.get("odometer_reading")

    if stated_odometer is None:
        return EvidencePacket(
            dimension="odometer",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=["No odometer reading provided in listing."],
            data_available=False,
        )

    facts.append(Fact(
        value=stated_odometer,
        field="stated_odometer",
        unit="km",
        source_type="listing",
        source_detail="listing_specs",
        source_confidence=SOURCE_CONFIDENCE["listing"],
        extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
        raw_excerpt=f"Odometer: {stated_odometer} km",
    ))
    observations.append(f"Stated odometer reading: {stated_odometer:,} km (from listing).")

    estimation_signals: List[tuple] = []  # (name, value, confidence)

    # Signal A: Oil changes
    oil_change_count = sum(
        1 for entry in service_log
        if "oil change" in str(entry.get("items", "")).lower()
    )
    if oil_change_count >= 2:
        implied = oil_change_count * OIL_CHANGE_INTERVAL_KM
        conf = ODOMETER_SIGNAL_CONFIDENCE["oil_change"]
        estimation_signals.append(("oil_change_implied_km", implied, conf))
        facts.append(Fact(
            value=oil_change_count, field="oil_change_count",
            source_type="service_log", source_detail="aggregated_entries",
            source_confidence=SOURCE_CONFIDENCE["service_log"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"{oil_change_count} oil change entries",
        ))
        observations.append(
            f"{oil_change_count} oil changes recorded. "
            f"At {OIL_CHANGE_INTERVAL_KM:,} km intervals, implies ~{implied:,} km."
        )

    # Signal B: Tyre replacements
    tyre_count = sum(
        1 for entry in service_log
        if any(kw in str(entry.get("items", "")).lower() for kw in ("tyre replacement", "tire replacement"))
    )
    if tyre_count >= 1:
        implied = tyre_count * TYRE_REPLACEMENT_INTERVAL_KM
        conf = ODOMETER_SIGNAL_CONFIDENCE["tyre_replacement"]
        estimation_signals.append(("tyre_implied_km", implied, conf))
        facts.append(Fact(
            value=tyre_count, field="tyre_replacement_count",
            source_type="service_log", source_detail="aggregated_entries",
            source_confidence=SOURCE_CONFIDENCE["service_log"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"{tyre_count} tyre replacement(s)",
        ))
        observations.append(
            f"{tyre_count} tyre replacement(s). "
            f"At {TYRE_REPLACEMENT_INTERVAL_KM:,} km intervals, implies ~{implied:,} km."
        )

    # Signal C: Brake replacements
    brake_count = sum(
        1 for entry in service_log
        if "brake pads" in str(entry.get("items", "")).lower()
    )
    if brake_count >= 1:
        implied = brake_count * BRAKE_REPLACEMENT_INTERVAL_KM
        conf = ODOMETER_SIGNAL_CONFIDENCE["brake_replacement"]
        estimation_signals.append(("brake_implied_km", implied, conf))
        facts.append(Fact(
            value=brake_count, field="brake_replacement_count",
            source_type="service_log", source_detail="aggregated_entries",
            source_confidence=SOURCE_CONFIDENCE["service_log"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"{brake_count} brake pad replacement(s)",
        ))
        observations.append(
            f"{brake_count} brake pad replacement(s). "
            f"At {BRAKE_REPLACEMENT_INTERVAL_KM:,} km intervals, implies ~{implied:,} km."
        )

    # Signal D: Vehicle age heuristic
    if vehicle_age_years and vehicle_age_years > 0:
        implied = int(vehicle_age_years * AVERAGE_ANNUAL_KM_INDIA)
        conf = ODOMETER_SIGNAL_CONFIDENCE["vehicle_age"]
        estimation_signals.append(("vehicle_age_implied_km", implied, conf))
        facts.append(Fact(
            value=vehicle_age_years, field="vehicle_age_years",
            source_type="rc_document", source_detail="derived_from_registration_year",
            source_confidence=SOURCE_CONFIDENCE["rc_document"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"Vehicle age: {vehicle_age_years} years",
        ))
        observations.append(
            f"Vehicle is {vehicle_age_years} years old. "
            f"At India average of {AVERAGE_ANNUAL_KM_INDIA:,} km/year, implies ~{implied:,} km."
        )

    # Signal E: Insurance declared mileage
    insurance_mileage = insurance.get("declared_mileage")
    if insurance_mileage:
        conf = ODOMETER_SIGNAL_CONFIDENCE["insurance_declaration"]
        estimation_signals.append(("insurance_declared_km", insurance_mileage, conf))
        facts.append(Fact(
            value=insurance_mileage, field="insurance_declared_mileage",
            unit="km", source_type="insurance_record",
            source_detail="renewal_form",
            source_confidence=SOURCE_CONFIDENCE["insurance_record"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"Insurance declared: {insurance_mileage} km",
        ))
        observations.append(f"Insurance renewal declared mileage: {insurance_mileage:,} km.")

    # Create Signal objects
    for name, value, conf in estimation_signals:
        signals.append(Signal(
            name=name,
            value=value,
            unit="km",
            confidence=conf,
            basis=f"Computed from service/vehicle data",
            source_facts=list(facts),
        ))

    # Compute median if enough signals
    if len(estimation_signals) >= MIN_ODOMETER_SIGNALS:
        values = [v for _, v, _ in estimation_signals]
        med = statistics.median(values)
        avg_conf = sum(c for _, _, c in estimation_signals) / len(estimation_signals)
        signals.append(Signal(
            name="median_implied_km",
            value=int(med),
            unit="km",
            confidence=round(avg_conf, 2),
            basis=f"Median of {len(estimation_signals)} signals: {sorted(values)}",
            source_facts=list(facts),
        ))
        observations.append(
            f"Median of {len(estimation_signals)} estimation signals: {int(med):,} km."
        )
    else:
        observations.append(
            f"Only {len(estimation_signals)} signal(s) available "
            f"(minimum {MIN_ODOMETER_SIGNALS} needed for comparative estimate)."
        )

    coverage = len(estimation_signals) / 5

    return EvidencePacket(
        dimension="odometer",
        facts=facts,
        signals=signals,
        coverage=coverage,
        observations=observations,
        data_available=True,
    )
