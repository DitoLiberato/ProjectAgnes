"""Tests for the Evidence and ClinicalEvent data structures."""
import pytest

from agnes.evidence import (
    ClinicalEvent,
    EventSeverity,
    Evidence,
    NodeID,
    SignalType,
)


class TestEvidence:
    def test_valid_evidence_created(self):
        e = Evidence(
            source=NodeID.WEARABLE,
            signal_type=SignalType.OPTICAL,
            value=98.0,
            quality=0.9,
            confidence=0.85,
        )
        assert e.source == NodeID.WEARABLE
        assert e.signal_type == SignalType.OPTICAL
        assert e.value == 98.0

    def test_quality_bounds_enforced(self):
        with pytest.raises(ValueError, match="quality"):
            Evidence(
                source=NodeID.WEARABLE,
                signal_type=SignalType.OPTICAL,
                value=98.0,
                quality=1.5,
            )

    def test_confidence_bounds_enforced(self):
        with pytest.raises(ValueError, match="confidence"):
            Evidence(
                source=NodeID.WEARABLE,
                signal_type=SignalType.ELECTRICAL,
                value=75.0,
                confidence=-0.1,
            )

    def test_is_reliable_true(self):
        e = Evidence(
            source=NodeID.WEARABLE,
            signal_type=SignalType.OPTICAL,
            value=98.0,
            quality=0.8,
            confidence=0.7,
        )
        assert e.is_reliable is True

    def test_is_reliable_false_low_quality(self):
        e = Evidence(
            source=NodeID.WEARABLE,
            signal_type=SignalType.OPTICAL,
            value=98.0,
            quality=0.3,
            confidence=0.9,
        )
        assert e.is_reliable is False

    def test_is_reliable_false_low_confidence(self):
        e = Evidence(
            source=NodeID.WEARABLE,
            signal_type=SignalType.OPTICAL,
            value=98.0,
            quality=0.9,
            confidence=0.2,
        )
        assert e.is_reliable is False

    def test_default_metadata_is_empty_dict(self):
        e = Evidence(
            source=NodeID.ENVIRONMENTAL,
            signal_type=SignalType.RADAR,
            value=1.2,
        )
        assert e.metadata == {}

    def test_two_evidence_objects_have_independent_metadata(self):
        e1 = Evidence(
            source=NodeID.WEARABLE, signal_type=SignalType.OPTICAL, value=97.0
        )
        e2 = Evidence(
            source=NodeID.WEARABLE, signal_type=SignalType.OPTICAL, value=96.0
        )
        e1.metadata["key"] = "value"
        assert "key" not in e2.metadata


class TestClinicalEvent:
    def _make_event(self, audible=False):
        return ClinicalEvent(
            event_id="test-001",
            description="Test tachycardia",
            severity=EventSeverity.WARNING,
            contributing_evidence=[],
            audible=audible,
        )

    def test_event_defaults_to_silent(self):
        event = self._make_event()
        assert event.audible is False

    def test_event_repr_contains_key_info(self):
        event = self._make_event()
        r = repr(event)
        assert "test-001" in r
        assert "warning" in r
