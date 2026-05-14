"""Phase 2: Service history extraction module."""

import logging
from typing import Any, Dict, List

from cartrust.constants import (
    EXTRACTION_CONFIDENCE,
    SERVICE_GAP_THRESHOLD_MONTHS,
    SERVICE_STALE_THRESHOLD_MONTHS,
    SOURCE_CONFIDENCE,
)
from cartrust.schemas import EvidencePacket, Fact, Signal
from cartrust.utils import months_between, parse_date, today

logger = logging.getLogger(__name__)


def extract_service(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    """Extract service history facts and gap signals. Never raises to caller."""
    try:
        return _extract_service(raw_inputs)
    except Exception as e:
        logger.error(f"Service extraction failed: {e}", exc_info=True)
        return EvidencePacket(
            dimension="service",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=["An error occurred during service data extraction."],
            data_available=False,
            notes=[f"Internal error: {type(e).__name__}: {str(e)}"],
        )


def _extract_service(raw_inputs: Dict[str, Any]) -> EvidencePacket:
    facts: List[Fact] = []
    signals: List[Signal] = []
    observations: List[str] = []

    service_log = raw_inputs.get("service_log") or []

    if not service_log:
        return EvidencePacket(
            dimension="service",
            facts=[],
            signals=[],
            coverage=0.0,
            observations=["No service records were provided."],
            data_available=False,
        )

    facts.append(Fact(
        value=len(service_log),
        field="service_entry_count",
        source_type="service_log",
        source_detail="aggregated",
        source_confidence=SOURCE_CONFIDENCE["service_log"],
        extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
        raw_excerpt=f"{len(service_log)} service entries",
    ))
    observations.append(f"Service log contains {len(service_log)} entries.")

    sorted_entries = sorted(
        service_log,
        key=lambda e: parse_date(e.get("date")) or __import__("datetime").datetime.min
    )

    for i, entry in enumerate(sorted_entries):
        date_str = entry.get("date")
        odo = entry.get("odometer")
        items = entry.get("items", [])
        center = entry.get("center", "unknown")
        facts.append(Fact(
            value={"date": date_str, "odometer": odo, "items": items, "center": center},
            field=f"service_entry_{i}",
            source_type="service_log",
            source_detail=f"entry_{i}_{date_str}",
            source_confidence=SOURCE_CONFIDENCE["service_log"],
            extraction_confidence=EXTRACTION_CONFIDENCE["digital_json"],
            raw_excerpt=f"{date_str}: {', '.join(items) if isinstance(items, list) else items} at {center}",
            timestamp=parse_date(date_str),
        ))

    # Signal: date range span
    if sorted_entries:
        first_dt = parse_date(sorted_entries[0].get("date"))
        last_dt = parse_date(sorted_entries[-1].get("date"))
        if first_dt and last_dt:
            span_months = months_between(first_dt, last_dt)
            signals.append(Signal(
                name="service_log_span_months",
                value=round(span_months, 1),
                unit="months",
                confidence=0.90,
                basis=f"Service records span from {first_dt.date()} to {last_dt.date()} ({span_months:.1f} months).",
            ))
            observations.append(
                f"Service records span {span_months:.1f} months ({first_dt.date()} to {last_dt.date()})."
            )

    # Signal: gaps between consecutive entries
    gaps = []
    for i in range(1, len(sorted_entries)):
        prev_dt = parse_date(sorted_entries[i - 1].get("date"))
        curr_dt = parse_date(sorted_entries[i].get("date"))
        if prev_dt and curr_dt:
            gap_months = months_between(prev_dt, curr_dt)
            gaps.append({
                "from": prev_dt.date().isoformat(),
                "to": curr_dt.date().isoformat(),
                "months": round(gap_months, 1),
            })

    signals.append(Signal(
        name="service_gaps",
        value=gaps,
        unit="months",
        confidence=0.90,
        basis=f"Computed {len(gaps)} intervals between {len(sorted_entries)} entries.",
    ))

    # Signal: long gaps exceeding threshold
    long_gaps = [g for g in gaps if g["months"] > SERVICE_GAP_THRESHOLD_MONTHS]
    signals.append(Signal(
        name="long_service_gaps",
        value=long_gaps,
        unit="months",
        confidence=0.90,
        basis=f"{len(long_gaps)} gap(s) exceeding {SERVICE_GAP_THRESHOLD_MONTHS} months found.",
    ))
    for gap in long_gaps:
        observations.append(
            f"Service gap: {gap['months']} months between {gap['from']} and {gap['to']}."
        )

    # Signal: months since last service
    if sorted_entries:
        last_service_dt = parse_date(sorted_entries[-1].get("date"))
        if last_service_dt:
            months_since = months_between(last_service_dt, today())
            signals.append(Signal(
                name="months_since_last_service",
                value=round(months_since, 1),
                unit="months",
                confidence=0.90,
                basis=f"Last service: {last_service_dt.date()}. {months_since:.1f} months ago.",
            ))
            observations.append(f"Last recorded service was {months_since:.1f} months ago.")

    # Signal: unique service centers
    centers = list(set(
        entry.get("center", "unknown")
        for entry in service_log
        if entry.get("center")
    ))
    signals.append(Signal(
        name="service_centers_used",
        value=centers,
        unit="count",
        confidence=0.85,
        basis=f"{len(centers)} unique service center(s): {', '.join(centers)}.",
    ))
    observations.append(f"Serviced at {len(centers)} center(s): {', '.join(centers)}.")

    return EvidencePacket(
        dimension="service",
        facts=facts,
        signals=signals,
        coverage=1.0,
        observations=observations,
        data_available=True,
    )
