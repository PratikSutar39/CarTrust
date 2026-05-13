"""
CarTrust Phase 2 Schemas

Fact, Signal, EvidencePacket, VehicleMetadata, VehicleEvidence.
These are the data contracts between the extraction layer (Phase 2)
and the reasoning engine (Phase 3).
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class Fact:
    """
    A single piece of data with its provenance attached.

    Produced by Phase 2 extraction modules.
    Consumed by Phase 3 reasoning engine.
    """

    value: Any
    field: str
    source_type: str
    source_detail: str
    source_confidence: float
    extraction_confidence: float
    raw_excerpt: str
    unit: Optional[str] = None
    timestamp: Optional[datetime] = None

    @property
    def trust_weight(self) -> float:
        """Combined trust: source_confidence × extraction_confidence."""
        return self.source_confidence * self.extraction_confidence


@dataclass
class Signal:
    """
    A derived measurement computed from one or more Facts.

    Phase 2 computes signals. Phase 3 interprets them.
    """

    name: str
    value: Any
    unit: Optional[str] = None
    confidence: float = 1.0
    basis: str = ""
    source_facts: List[Fact] = field(default_factory=list)


@dataclass
class EvidencePacket:
    """
    Complete evidence extracted by one ingestion module for one dimension.

    This is the contract between Phase 2 (extraction) and Phase 3 (reasoning).
    Phase 3 reads only this structure — never the raw inputs.
    """

    dimension: str
    facts: List[Fact]
    signals: List[Signal]
    coverage: float
    observations: List[str]
    data_available: bool
    notes: List[str] = field(default_factory=list)


@dataclass
class VehicleMetadata:
    """Basic identifying information about the vehicle being assessed."""

    make: str
    model: str
    year: int
    registration_number: Optional[str] = None
    listing_price: Optional[int] = None
    listing_url: Optional[str] = None


@dataclass
class VehicleEvidence:
    """
    Complete evidence package for one vehicle.

    This is the output of Phase 2 and the input to Phase 3.
    Contains five EvidencePackets (one per dimension) plus vehicle metadata.
    """

    metadata: VehicleMetadata
    ownership: EvidencePacket
    odometer: EvidencePacket
    accident: EvidencePacket
    financial: EvidencePacket
    service: EvidencePacket
    extraction_timestamp: datetime

    @property
    def all_packets(self) -> List[EvidencePacket]:
        return [self.ownership, self.odometer, self.accident, self.financial, self.service]

    @property
    def overall_coverage(self) -> float:
        coverages = [p.coverage for p in self.all_packets]
        return sum(coverages) / len(coverages) if coverages else 0.0

    @property
    def verifiable_dimensions(self) -> int:
        return sum(1 for p in self.all_packets if p.data_available)
