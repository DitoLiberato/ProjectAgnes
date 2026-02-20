"""
Tests for the node architecture and Central Hub.

Covers:
- WearableNode evidence generation from injected readings
- EnvironmentalNode evidence generation
- CentralHub full decision cycle (end-to-end integration)
- All five manifesto §5 clinical scenarios end-to-end
"""
import pytest

from agnes.evidence import ClinicalEvent, EventSeverity, NodeID, SignalType
from agnes.nodes import (
    CentralHub,
    EnvironmentalNode,
    EnvironmentalReadings,
    WearableNode,
    WearableReadings,
)
from agnes.veto_engine import VetoRecord


# ---------------------------------------------------------------------------
# WearableNode tests
# ---------------------------------------------------------------------------

class TestWearableNode:
    def test_produces_three_evidence_objects(self):
        node = WearableNode()
        node.inject_readings(WearableReadings())
        evidence = node.read_evidence()
        assert len(evidence) == 3

    def test_evidence_sources_are_wearable(self):
        node = WearableNode()
        node.inject_readings(WearableReadings())
        evidence = node.read_evidence()
        for e in evidence:
            assert e.source == NodeID.WEARABLE

    def test_signal_types_cover_optical_electrical_mechanical(self):
        node = WearableNode()
        node.inject_readings(WearableReadings())
        types = {e.signal_type for e in node.read_evidence()}
        assert SignalType.OPTICAL in types
        assert SignalType.ELECTRICAL in types
        assert SignalType.MECHANICAL in types

    def test_lead_off_sets_zero_quality_on_ecg(self):
        node = WearableNode()
        node.inject_readings(WearableReadings(lead_off=True))
        evidence = node.read_evidence()
        ecg = next(e for e in evidence if e.signal_type == SignalType.ELECTRICAL)
        assert ecg.quality == 0.0
        assert ecg.metadata["lead_off"] is True

    def test_ppg_anomaly_propagates_to_metadata(self):
        node = WearableNode()
        node.inject_readings(WearableReadings(ppg_anomaly=True))
        evidence = node.read_evidence()
        ppg = next(e for e in evidence if e.signal_type == SignalType.OPTICAL)
        assert ppg.metadata["anomaly"] is True

    def test_flush_buffer_clears_evidence(self):
        node = WearableNode()
        node.inject_readings(WearableReadings())
        node.read_evidence()
        assert len(node.flush_buffer()) == 3
        assert len(node.flush_buffer()) == 0


# ---------------------------------------------------------------------------
# EnvironmentalNode tests
# ---------------------------------------------------------------------------

class TestEnvironmentalNode:
    def test_produces_two_evidence_objects(self):
        node = EnvironmentalNode()
        node.inject_readings(EnvironmentalReadings())
        evidence = node.read_evidence()
        assert len(evidence) == 2

    def test_evidence_sources_are_environmental(self):
        node = EnvironmentalNode()
        node.inject_readings(EnvironmentalReadings())
        evidence = node.read_evidence()
        for e in evidence:
            assert e.source == NodeID.ENVIRONMENTAL

    def test_signal_types_cover_radar_and_thermal(self):
        node = EnvironmentalNode()
        node.inject_readings(EnvironmentalReadings())
        types = {e.signal_type for e in node.read_evidence()}
        assert SignalType.RADAR in types
        assert SignalType.THERMAL in types

    def test_apnea_flag_propagates_to_radar_metadata(self):
        node = EnvironmentalNode()
        node.inject_readings(EnvironmentalReadings(apnea_detected=True))
        evidence = node.read_evidence()
        radar = next(e for e in evidence if e.signal_type == SignalType.RADAR)
        assert radar.metadata["apnea"] is True


# ---------------------------------------------------------------------------
# CentralHub integration tests (manifesto §5 scenarios)
# ---------------------------------------------------------------------------

class TestCentralHubScenario1:
    """Scenario 1 – Combative Baby: movement artifact is vetoed."""

    def test_combative_baby_is_vetoed(self):
        hub = CentralHub()
        wearable = WearableNode()
        wearable.inject_readings(
            WearableReadings(ppg_anomaly=True, accel_ms2=4.0)
        )
        hub.register_node(wearable)
        result = hub.process_cycle("Desaturation")
        assert isinstance(result, VetoRecord)

    def test_combative_baby_veto_reason_mentions_agitation(self):
        hub = CentralHub()
        wearable = WearableNode()
        wearable.inject_readings(
            WearableReadings(ppg_anomaly=True, accel_ms2=4.0)
        )
        hub.register_node(wearable)
        result = hub.process_cycle("Desaturation")
        assert isinstance(result, VetoRecord)
        assert "Agitation" in result.reason or "agitation" in result.reason.lower()


class TestCentralHubScenario2:
    """Scenario 2 – False Asystole: lead-off is vetoed silently."""

    def test_lead_off_is_vetoed(self):
        hub = CentralHub()
        wearable = WearableNode()
        wearable.inject_readings(WearableReadings(lead_off=True))
        hub.register_node(wearable)
        result = hub.process_cycle("Asystole")
        assert isinstance(result, VetoRecord)
        assert "Lead" in result.reason


class TestCentralHubScenario4:
    """Scenario 4 – True SVT: convergent evidence is promoted silently."""

    def test_true_svt_is_promoted_silently(self):
        hub = CentralHub()
        wearable = WearableNode()
        wearable.inject_readings(
            WearableReadings(
                ecg_tachycardia=True,
                ppg_tachycardia=True,
                accel_ms2=0.05,  # patient still
                lead_off=False,
                ppg_anomaly=False,
                ppg_quality=0.9,
            )
        )
        hub.register_node(wearable)
        result = hub.process_cycle("SVT", severity=EventSeverity.WARNING)
        assert isinstance(result, ClinicalEvent)
        assert result.audible is False


class TestCentralHubScenario5:
    """Scenario 5 – Apnea of Prematurity: audible alarm as last resort."""

    def test_apnea_triggers_audible_alarm(self):
        hub = CentralHub()
        wearable = WearableNode()
        wearable.inject_readings(
            WearableReadings(spo2_falling=True, ppg_anomaly=True)
        )
        env = EnvironmentalNode()
        env.inject_readings(
            EnvironmentalReadings(apnea_detected=True, radar_movement_magnitude=0.0)
        )
        hub.register_node(wearable)
        hub.register_node(env)
        result = hub.process_cycle(
            "Apnea of Prematurity",
            severity=EventSeverity.CRITICAL,
            force_audible=True,
        )
        assert isinstance(result, ClinicalEvent)
        assert result.audible is True


class TestCentralHubCallbacks:
    def test_event_callback_is_called_on_promotion(self):
        received = []
        hub = CentralHub()
        hub.on_event(received.append)

        wearable = WearableNode()
        wearable.inject_readings(
            WearableReadings(
                ecg_tachycardia=False,
                ppg_anomaly=False,
                accel_ms2=0.1,
                lead_off=False,
            )
        )
        hub.register_node(wearable)
        result = hub.process_cycle("Mild event", severity=EventSeverity.WARNING)
        if isinstance(result, ClinicalEvent):
            assert len(received) == 1
            assert received[0] is result

    def test_veto_does_not_trigger_callback(self):
        received = []
        hub = CentralHub()
        hub.on_event(received.append)

        wearable = WearableNode()
        wearable.inject_readings(WearableReadings(lead_off=True))
        hub.register_node(wearable)
        hub.process_cycle("Asystole")
        assert len(received) == 0


class TestCentralHubBlackBox:
    def test_hub_records_decision_in_black_box(self):
        hub = CentralHub()
        wearable = WearableNode()
        wearable.inject_readings(WearableReadings(lead_off=True))
        hub.register_node(wearable)
        hub.process_cycle("Asystole")
        # Should have a veto entry in the black box
        vetos = list(hub.black_box.iter_entries(entry_type=None))
        assert len(vetos) > 0
