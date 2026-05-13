"""Phase 3 Rule Engine: Odometer assessor (multi-signal)."""

import logging
import statistics

from cartrust.constants import MIN_ODOMETER_SIGNALS
from cartrust.reasoning.rules.helpers import find_signal
from cartrust.reasoning.schemas import DimensionAssessment, Flag
from cartrust.schemas import EvidencePacket

logger = logging.getLogger(__name__)


def assess_odometer(evidence: EvidencePacket) -> DimensionAssessment:
    """Pure Python. Interprets multi-signal odometer evidence."""
    try:
        return _assess_odometer(evidence)
    except Exception as e:
        logger.error(f"Odometer rule engine failed: {e}", exc_info=True)
        return DimensionAssessment(dimension="odometer", state="unverifiable", score=0.0)


def _assess_odometer(evidence: EvidencePacket) -> DimensionAssessment:
    if not evidence.data_available:
        return DimensionAssessment(dimension="odometer", state="unverifiable", score=0.0)

    stated_fact = next(
        (f for f in evidence.facts if f.field == "stated_odometer"), None
    )
    if not stated_fact:
        return DimensionAssessment(dimension="odometer", state="unverifiable", score=0.0)

    stated_km = stated_fact.value

    # Gather estimation signals (exclude median itself)
    estimation_signals = [
        s for s in evidence.signals
        if (s.name.endswith("_implied_km") or s.name == "insurance_declared_km")
        and s.name != "median_implied_km"
    ]

    if len(estimation_signals) < MIN_ODOMETER_SIGNALS:
        return DimensionAssessment(
            dimension="odometer",
            state="unverifiable",
            score=0.0,
            flags=[],
        )

    # Use pre-computed median if available, else compute
    median_signal = find_signal(evidence, "median_implied_km")
    if median_signal:
        median_km = median_signal.value
    else:
        values = sorted([s.value for s in estimation_signals])
        median_km = int(statistics.median(values))

    discrepancy = abs(median_km - stated_km)
    discrepancy_ratio = discrepancy / stated_km if stated_km > 0 else 0.0

    higher_threshold = stated_km * 1.10
    agreeing_signals = [s for s in estimation_signals if s.value > higher_threshold]
    agreement_count = len(agreeing_signals)

    signal_details = "; ".join(
        f"{s.name}={s.value:,} km (conf:{s.confidence})"
        for s in estimation_signals
    )

    flags = []

    # Rule: multi-signal discrepancy (>10% with 2+ agreeing signals)
    if discrepancy_ratio > 0.10 and agreement_count >= 2:
        flags.append(Flag(
            flag_id="ODO_MULTI_SIGNAL_DISCREPANCY",
            severity="high",
            evidence_summary=(
                f"Stated odometer: {stated_km:,} km. "
                f"Median of {len(estimation_signals)} signals: {median_km:,} km. "
                f"Discrepancy: {discrepancy:,} km ({discrepancy_ratio:.0%}). "
                f"Agreeing signals (>10% higher): {agreement_count} of {len(estimation_signals)}. "
                f"Signals: {signal_details}."
            ),
            suggested_actions=[
                "Request the odometer reading from the most recent authorized service visit.",
                "Verify the odometer against the OBD-II diagnostic reading at a service center.",
                f"Negotiate price based on estimated actual mileage of ~{median_km:,} km.",
            ],
        ))
        score = max(0.0, 1.0 - (discrepancy_ratio * 2))
        state = "verified_flagged"

    # Rule: minor discrepancy (5-10% with 2+ agreeing signals)
    elif discrepancy_ratio > 0.05 and agreement_count >= 2:
        flags.append(Flag(
            flag_id="ODO_MINOR_DISCREPANCY",
            severity="medium",
            evidence_summary=(
                f"Stated odometer: {stated_km:,} km. "
                f"Median of signals: {median_km:,} km. "
                f"Discrepancy: {discrepancy:,} km ({discrepancy_ratio:.0%}). "
                f"Signals: {signal_details}."
            ),
            suggested_actions=[
                "Verify the odometer at an authorized service center.",
                "Ask the seller about the discrepancy.",
            ],
        ))
        score = 0.70
        state = "verified_flagged"

    else:
        score = 0.95
        state = "verified_clean"

    return DimensionAssessment(
        dimension="odometer",
        state=state,
        flags=flags,
        score=round(score, 2),
    )
