"""
Tests for the VetoEngine.

Covers all five manifesto §5 clinical scenarios from the suppression side:
 - Movement artifact veto
 - Lead-off veto
 - Poor signal quality veto
 - Promoted event (no veto fires)
 - Audible alarm only for forced-critical escalation
"""
import pytest

from agnes.evidence import Evidence, EventSeverity, NodeID, SignalType
from agnes.veto_engine import VetoEngine, VetoRecord
from agnes.evidence import ClinicalEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _ppg_anomaly(quality=0.8) -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.OPTICAL,
        value=85.0,
        quality=quality,
        confidence=quality,
        metadata={"anomaly": True},
    )


def _imu_high_movement() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.MECHANICAL,
        value=3.5,  # > 1.5 m/s² threshold
    )


def _imu_still() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.MECHANICAL,
        value=0.1,  # near-zero
    )


def _ecg_lead_off() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.ELECTRICAL,
        value=0.0,
        quality=0.0,
        confidence=0.0,
        metadata={"lead_off": True},
    )


def _ecg_normal() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.ELECTRICAL,
        value=75.0,
        metadata={"lead_off": False},
    )


def _ppg_normal() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.OPTICAL,
        value=98.0,
        metadata={"anomaly": False},
    )


def _unreliable_ppg() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.OPTICAL,
        value=70.0,
        quality=0.2,
        confidence=0.2,
        metadata={"anomaly": True},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestVetoEngineMovementArtifact:
    """Scenario 1 – Combative Baby (manifesto §5)."""

    def test_ppg_anomaly_with_high_movement_is_vetoed(self):
        engine = VetoEngine()
        result = engine.evaluate(
            "Desaturation",
            [_ppg_anomaly(), _imu_high_movement()],
        )
        assert isinstance(result, VetoRecord)
        assert "Mechanical Agitation" in result.reason

    def test_ppg_anomaly_without_movement_is_not_vetoed_by_movement_rule(self):
        engine = VetoEngine()
        # Only PPG anomaly, no IMU high movement → movement veto should NOT fire
        result = engine.evaluate(
            "Desaturation",
            [_ppg_anomaly(), _imu_still()],
        )
        # Movement rule should not fire; result may be an event or another veto
        if isinstance(result, VetoRecord):
            assert "Mechanical Agitation" not in result.reason

    def test_veto_count_increments(self):
        engine = VetoEngine()
        engine.evaluate("Desat", [_ppg_anomaly(), _imu_high_movement()])
        engine.evaluate("Desat", [_ppg_anomaly(), _imu_high_movement()])
        assert engine.veto_count == 2


class TestVetoEngineLeadOff:
    """Scenario 2 – False Asystole (manifesto §5)."""

    def test_lead_off_ecg_is_vetoed(self):
        engine = VetoEngine()
        result = engine.evaluate("Asystole", [_ecg_lead_off()])
        assert isinstance(result, VetoRecord)
        assert "Lead Disconnected" in result.reason

    def test_normal_ecg_not_vetoed_by_lead_off_rule(self):
        engine = VetoEngine()
        result = engine.evaluate("Tachycardia", [_ecg_normal(), _ppg_normal()])
        # Lead-off veto should not fire for a normal ECG
        if isinstance(result, VetoRecord):
            assert "Lead Disconnected" not in result.reason


class TestVetoEnginePoorSignal:
    """All evidence is unreliable → veto fires."""

    def test_all_unreliable_evidence_vetoed(self):
        engine = VetoEngine()
        result = engine.evaluate("Desaturation", [_unreliable_ppg()])
        assert isinstance(result, VetoRecord)
        assert "unreliable" in result.reason.lower()


class TestVetoEnginePromotion:
    """Valid, convergent evidence should produce a ClinicalEvent."""

    def test_clean_evidence_promotes_event(self):
        engine = VetoEngine()
        result = engine.evaluate(
            "Mild tachycardia",
            [_ecg_normal(), _ppg_normal(), _imu_still()],
            severity=EventSeverity.WARNING,
        )
        assert isinstance(result, ClinicalEvent)
        assert result.description == "Mild tachycardia"
        assert result.severity == EventSeverity.WARNING

    def test_promoted_event_is_silent_by_default(self):
        engine = VetoEngine()
        result = engine.evaluate(
            "Warning event",
            [_ecg_normal(), _ppg_normal()],
            severity=EventSeverity.WARNING,
        )
        assert isinstance(result, ClinicalEvent)
        assert result.audible is False

    def test_critical_severity_makes_event_audible(self):
        """Manifesto §5 Scenario 5 – Apnea requires audible alarm."""
        engine = VetoEngine()
        result = engine.evaluate(
            "Apnea of Prematurity",
            [_ecg_normal(), _ppg_normal()],
            severity=EventSeverity.CRITICAL,
        )
        assert isinstance(result, ClinicalEvent)
        assert result.audible is True

    def test_force_audible_overrides_silent_default(self):
        engine = VetoEngine()
        result = engine.evaluate(
            "Life-threatening event",
            [_ecg_normal(), _ppg_normal()],
            severity=EventSeverity.WARNING,
            force_audible=True,
        )
        assert isinstance(result, ClinicalEvent)
        assert result.audible is True


class TestVetoEngineCustomRules:
    """Custom rules can be added to the engine."""

    def test_add_custom_rule(self):
        engine = VetoEngine(rules=[])  # start with empty rules

        def custom_rule(window):
            if any(e.metadata.get("custom_flag") for e in window):
                return "Custom flag detected"
            return None

        engine.add_rule(custom_rule)

        flagged = Evidence(
            source=NodeID.WEARABLE,
            signal_type=SignalType.OPTICAL,
            value=90.0,
            metadata={"custom_flag": True},
        )
        result = engine.evaluate("Custom event", [flagged])
        assert isinstance(result, VetoRecord)
        assert "Custom flag" in result.reason

    def test_engine_with_no_rules_always_promotes(self):
        engine = VetoEngine(rules=[])
        result = engine.evaluate("Event", [_ppg_anomaly(), _imu_high_movement()])
        assert isinstance(result, ClinicalEvent)
