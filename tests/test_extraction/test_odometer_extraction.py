"""Tests for the odometer evidence extraction module."""

import pytest
from cartrust.extraction.odometer import extract_odometer


def _raw_with_oil_changes(count, km_per_change=5500, stated_km=None):
    """Build a raw input dict with `count` oil change service entries."""
    service_entries = [
        {
            "date": f"202{i % 4}-0{(i % 9) + 1}-15",
            "odometer": km_per_change * (i + 1),
            "items": "oil change, oil filter",
            "center": "authorized",
        }
        for i in range(count)
    ]
    return {
        "service_log": service_entries,
        "listing": {"odometer_reading": stated_km or km_per_change * count},
    }


class TestOdometerExtractionOilChanges:
    def test_oil_change_count_extracted(self):
        raw = _raw_with_oil_changes(5, stated_km=27500)
        packet = extract_odometer(raw)
        oil_signal = next((s for s in packet.signals if s.name == "oil_change_implied_km"), None)
        assert oil_signal is not None

    def test_oil_change_implied_value(self):
        raw = _raw_with_oil_changes(5, stated_km=27500)
        packet = extract_odometer(raw)
        oil_signal = next((s for s in packet.signals if s.name == "oil_change_implied_km"), None)
        assert oil_signal is not None
        # 5 oil changes × 5500 km = 27500
        assert oil_signal.value == 27500

    def test_agreement_count_signal_present(self):
        """Median signal should be present when ≥2 estimation signals exist."""
        raw = _raw_with_oil_changes(5, stated_km=27500)
        raw["service_log"].append({
            "date": "2023-06-01",
            "odometer": 42000,
            "items": "tyre replacement, alignment",
            "center": "authorized",
        })
        packet = extract_odometer(raw)
        # Should have at least 2 estimation signals → median computed
        median_signal = next((s for s in packet.signals if s.name == "median_implied_km"), None)
        assert median_signal is not None

    def test_data_available_with_odometer_reading(self):
        raw = _raw_with_oil_changes(3, stated_km=16500)
        packet = extract_odometer(raw)
        assert packet.data_available is True


class TestOdometerExtractionEmpty:
    def test_empty_inputs(self):
        packet = extract_odometer({})
        assert packet.dimension == "odometer"
        assert packet.data_available is False

    def test_no_service_log(self):
        raw = {"listing": {"odometer_reading": 35000}}
        packet = extract_odometer(raw)
        assert packet.dimension == "odometer"
        # data_available True but no estimation signals → only stated odometer
        assert packet.data_available is True

    def test_never_raises(self):
        """Extraction must never raise — always return a packet."""
        packet = extract_odometer({"service_log": None, "rc": None})
        assert packet.dimension == "odometer"
