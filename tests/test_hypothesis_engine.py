"""
Tests for the HypothesisEngine.

Covers all five clinical scenarios from manifesto §5.
"""
import pytest

from agnes.evidence import Evidence, NodeID, SignalType
from agnes.hypothesis_engine import HypothesisEngine


# ---------------------------------------------------------------------------
# Evidence helpers
# ---------------------------------------------------------------------------

def _ppg_anomaly(spo2_falling=False) -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.OPTICAL,
        value=85.0,
        metadata={
            "anomaly": True,
            "spo2_falling": spo2_falling,
            "tachycardia": False,
            "pulse_amplitude_low": False,
        },
    )


def _imu_high_movement() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.MECHANICAL,
        value=3.5,
    )


def _imu_still() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.MECHANICAL,
        value=0.1,
    )


def _ecg_lead_off() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.ELECTRICAL,
        value=0.0,
        quality=0.0,
        confidence=0.0,
        metadata={"lead_off": True, "tachycardia": False},
    )


def _ecg_tachy() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.ELECTRICAL,
        value=160.0,
        metadata={"lead_off": False, "tachycardia": True},
    )


def _ppg_tachy() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.OPTICAL,
        value=98.0,
        metadata={"anomaly": False, "tachycardia": True, "spo2_falling": False,
                  "pulse_amplitude_low": False},
    )


def _radar_breathing() -> Evidence:
    return Evidence(
        source=NodeID.ENVIRONMENTAL,
        signal_type=SignalType.RADAR,
        value=1.2,
        metadata={"respiration_rate_rpm": 18, "apnea": False},
    )


def _radar_apnea() -> Evidence:
    return Evidence(
        source=NodeID.ENVIRONMENTAL,
        signal_type=SignalType.RADAR,
        value=0.0,
        metadata={"respiration_rate_rpm": 0, "apnea": True},
    )


def _thermal_normal() -> Evidence:
    return Evidence(
        source=NodeID.ENVIRONMENTAL,
        signal_type=SignalType.THERMAL,
        value="normal",
        metadata={"gradient_pattern": "normal"},
    )


def _thermal_shock() -> Evidence:
    return Evidence(
        source=NodeID.ENVIRONMENTAL,
        signal_type=SignalType.THERMAL,
        value="periphery_cooling",
        metadata={"gradient_pattern": "periphery_cooling"},
    )


def _ppg_low_amplitude() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.OPTICAL,
        value=92.0,
        metadata={
            "anomaly": False,
            "tachycardia": False,
            "pulse_amplitude_low": True,
            "spo2_falling": False,
        },
    )


def _ppg_spo2_falling() -> Evidence:
    return Evidence(
        source=NodeID.WEARABLE,
        signal_type=SignalType.OPTICAL,
        value=88.0,
        metadata={
            "anomaly": True,
            "tachycardia": False,
            "pulse_amplitude_low": False,
            "spo2_falling": True,
        },
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestHypothesisScenario1:
    """Scenario 1 – Combative Baby / Mechanical Agitation Artifact."""

    def test_detects_mechanical_agitation(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_ppg_anomaly(), _imu_high_movement()])
        assert h is not None
        assert "Mechanical Agitation" in h.name

    def test_agitation_hypothesis_is_not_actionable(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_ppg_anomaly(), _imu_high_movement()])
        assert h is not None
        assert h.actionable is False

    def test_no_agitation_without_movement(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_ppg_anomaly(), _imu_still()])
        # Should not be a mechanical agitation hypothesis
        if h is not None:
            assert "Mechanical Agitation" not in h.name


class TestHypothesisScenario2:
    """Scenario 2 – False Asystole / Lead Disconnection."""

    def test_detects_lead_disconnection(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_ecg_lead_off(), _radar_breathing()])
        assert h is not None
        assert "Lead Disconnection" in h.name

    def test_lead_disconnection_is_actionable(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_ecg_lead_off(), _radar_breathing()])
        assert h is not None
        assert h.actionable is True

    def test_lead_disconnection_has_high_confidence(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_ecg_lead_off(), _radar_breathing()])
        assert h is not None
        assert h.confidence >= 0.95


class TestHypothesisScenario3:
    """Scenario 3 – Silent Cold Shock."""

    def test_detects_shock_physiology(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_thermal_shock(), _ppg_low_amplitude()])
        assert h is not None
        assert "Shock" in h.name

    def test_shock_hypothesis_is_actionable(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_thermal_shock(), _ppg_low_amplitude()])
        assert h is not None
        assert h.actionable is True

    def test_no_shock_without_thermal_evidence(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_thermal_normal(), _ppg_low_amplitude()])
        if h is not None:
            assert "Shock" not in h.name


class TestHypothesisScenario4:
    """Scenario 4 – True SVT / Validated Tachyarrhythmia."""

    def test_detects_validated_tachyarrhythmia(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_ecg_tachy(), _ppg_tachy(), _imu_still()])
        assert h is not None
        assert "Tachyarrhythmia" in h.name

    def test_tachyarrhythmia_is_actionable(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_ecg_tachy(), _ppg_tachy(), _imu_still()])
        assert h is not None
        assert h.actionable is True

    def test_no_validated_tachy_without_patient_still(self):
        engine = HypothesisEngine()
        # Patient moving – should not confirm tachyarrhythmia
        h = engine.evaluate([_ecg_tachy(), _ppg_tachy(), _imu_high_movement()])
        if h is not None:
            assert "Tachyarrhythmia" not in h.name


class TestHypothesisScenario5:
    """Scenario 5 – Apnea of Prematurity."""

    def test_detects_apnea_of_prematurity(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_radar_apnea(), _ppg_spo2_falling()])
        assert h is not None
        assert "Apnea" in h.name

    def test_apnea_is_actionable(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_radar_apnea(), _ppg_spo2_falling()])
        assert h is not None
        assert h.actionable is True

    def test_apnea_has_high_confidence(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_radar_apnea(), _ppg_spo2_falling()])
        assert h is not None
        assert h.confidence >= 0.90

    def test_no_apnea_without_radar_evidence(self):
        engine = HypothesisEngine()
        h = engine.evaluate([_ppg_spo2_falling()])
        if h is not None:
            assert "Apnea" not in h.name


class TestHypothesisNoMatch:
    def test_returns_none_for_normal_readings(self):
        engine = HypothesisEngine()
        normal_ppg = Evidence(
            source=NodeID.WEARABLE,
            signal_type=SignalType.OPTICAL,
            value=98.0,
            metadata={"anomaly": False, "tachycardia": False,
                      "pulse_amplitude_low": False, "spo2_falling": False},
        )
        normal_ecg = Evidence(
            source=NodeID.WEARABLE,
            signal_type=SignalType.ELECTRICAL,
            value=75.0,
            metadata={"lead_off": False, "tachycardia": False},
        )
        normal_imu = Evidence(
            source=NodeID.WEARABLE,
            signal_type=SignalType.MECHANICAL,
            value=0.05,
        )
        h = engine.evaluate([normal_ppg, normal_ecg, normal_imu])
        assert h is None


class TestHypothesisCustomRules:
    def test_add_custom_rule(self):
        from agnes.hypothesis_engine import Hypothesis

        engine = HypothesisEngine(rules=[])

        def custom_rule(window):
            if any(e.metadata.get("special") for e in window):
                return Hypothesis(
                    name="Special Condition",
                    description="Custom rule fired",
                    confidence=0.75,
                )
            return None

        engine.add_rule(custom_rule)

        special = Evidence(
            source=NodeID.WEARABLE,
            signal_type=SignalType.OPTICAL,
            value=90.0,
            metadata={"special": True},
        )
        h = engine.evaluate([special])
        assert h is not None
        assert h.name == "Special Condition"
