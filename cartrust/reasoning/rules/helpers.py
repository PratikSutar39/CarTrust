"""Shared helpers for rule engine assessors."""

from typing import Optional

from cartrust.schemas import EvidencePacket, Signal


def find_signal(evidence: EvidencePacket, name: str) -> Optional[Signal]:
    """Find a signal by name in an EvidencePacket. Returns None if not found."""
    for signal in evidence.signals:
        if signal.name == name:
            return signal
    return None
