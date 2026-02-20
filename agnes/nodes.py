"""
AGNES Node Architecture
=======================
Defines the cooperative sensor nodes described in manifesto §3.

Node types
----------
* **WearableNode**       – contact sensors on the patient (MAX30102, AD8232, MPU6050)
* **EnvironmentalNode**  – contactless sensors near the patient (mmWave radar,
                           MLX90640 thermal camera)
* **CentralHub**         – aggregates evidence from all nodes, runs the Veto
                           Engine and Hypothesis Engine, drives the silent HMI

Each node reads raw sensor data and emits ``Evidence`` objects.  The actual
hardware drivers (I2C, SPI, UART) are abstracted behind a minimal interface
so the same logic can be exercised in simulation and on real ESP32 hardware.

Communication between nodes uses the ESP-NOW inspired edge-first model
described in manifesto §3: decisions happen as close to the sensor as
possible to minimise latency and preserve system stability.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Optional

from agnes.evidence import Evidence, NodeID, SignalType
from agnes.veto_engine import VetoEngine, VetoRecord
from agnes.hypothesis_engine import Hypothesis, HypothesisEngine
from agnes.black_box import ClinicalBlackBox, EntryType
from agnes.evidence import ClinicalEvent, EventSeverity


# ---------------------------------------------------------------------------
# Abstract base node
# ---------------------------------------------------------------------------

class BaseNode(ABC):
    """
    Abstract base class for all AGNES sensor nodes.

    Every node has a unique NodeID and can produce Evidence objects.
    Subclasses implement ``read_evidence`` to abstract hardware specifics.
    """

    def __init__(self, node_id: NodeID) -> None:
        self.node_id = node_id
        self._evidence_buffer: list[Evidence] = []

    @abstractmethod
    def read_evidence(self) -> list[Evidence]:
        """
        Sample all sensors on this node and return the resulting Evidence
        objects.  In a real system this calls into hardware drivers; in
        simulation it can read from injected data.
        """

    def flush_buffer(self) -> list[Evidence]:
        """Return and clear the accumulated evidence buffer."""
        items = list(self._evidence_buffer)
        self._evidence_buffer.clear()
        return items


# ---------------------------------------------------------------------------
# Wearable Node (contact)
# ---------------------------------------------------------------------------

@dataclass
class WearableReadings:
    """
    Raw readings from the wearable node sensors.

    Attributes
    ----------
    heart_rate_bpm  : Heart rate in beats per minute (MAX30102 PPG).
    spo2_pct        : Blood oxygen saturation percentage (MAX30102 PPG).
    ppg_quality     : Signal quality [0, 1] for the PPG reading.
    ppg_anomaly     : True when PPG detects an out-of-range condition.
    ppg_pulse_amplitude_low : True when pulse amplitude is reduced (shock marker).
    spo2_falling    : True when SpO₂ trend is downward.
    ecg_hr_bpm      : Heart rate from ECG (AD8232), None if lead off.
    lead_off        : True when AD8232 lead-off detection is active.
    ecg_tachycardia : True when ECG detects tachycardia.
    ppg_tachycardia : True when PPG detects tachycardia.
    accel_ms2       : Resultant 3-axis acceleration magnitude (MPU6050), m/s².
    """

    heart_rate_bpm: float = 0.0
    spo2_pct: float = 98.0
    ppg_quality: float = 1.0
    ppg_anomaly: bool = False
    ppg_pulse_amplitude_low: bool = False
    spo2_falling: bool = False
    ecg_hr_bpm: Optional[float] = None
    lead_off: bool = False
    ecg_tachycardia: bool = False
    ppg_tachycardia: bool = False
    accel_ms2: float = 0.0


class WearableNode(BaseNode):
    """
    Contact wearable node with MAX30102 (PPG), AD8232 (ECG), and MPU6050
    (IMU) sensors (manifesto §3 – "The Wearable Node").

    In simulation, readings are injected via ``inject_readings``.  On real
    hardware the constructor would receive driver handles.
    """

    def __init__(self) -> None:
        super().__init__(NodeID.WEARABLE)
        self._readings = WearableReadings()

    def inject_readings(self, readings: WearableReadings) -> None:
        """Inject simulated or test readings (replaces hardware driver call)."""
        self._readings = readings

    def read_evidence(self) -> list[Evidence]:
        """
        Convert current sensor readings into Evidence objects with full
        metadata for downstream validation.
        """
        r = self._readings
        ts = time.time()
        evidence: list[Evidence] = []

        # --- PPG (MAX30102) ---
        ppg_confidence = r.ppg_quality * (0.5 if r.ppg_anomaly else 1.0)
        evidence.append(
            Evidence(
                source=NodeID.WEARABLE,
                signal_type=SignalType.OPTICAL,
                value=r.spo2_pct,
                quality=r.ppg_quality,
                confidence=ppg_confidence,
                timestamp=ts,
                sensor_id="MAX30102",
                metadata={
                    "heart_rate_bpm": r.heart_rate_bpm,
                    "anomaly": r.ppg_anomaly,
                    "pulse_amplitude_low": r.ppg_pulse_amplitude_low,
                    "spo2_falling": r.spo2_falling,
                    "tachycardia": r.ppg_tachycardia,
                },
            )
        )

        # --- ECG (AD8232) ---
        ecg_quality = 0.0 if r.lead_off else 1.0
        evidence.append(
            Evidence(
                source=NodeID.WEARABLE,
                signal_type=SignalType.ELECTRICAL,
                value=r.ecg_hr_bpm if r.ecg_hr_bpm is not None else 0.0,
                quality=ecg_quality,
                confidence=ecg_quality,
                timestamp=ts,
                sensor_id="AD8232",
                metadata={
                    "lead_off": r.lead_off,
                    "tachycardia": r.ecg_tachycardia,
                },
            )
        )

        # --- IMU (MPU6050) ---
        evidence.append(
            Evidence(
                source=NodeID.WEARABLE,
                signal_type=SignalType.MECHANICAL,
                value=r.accel_ms2,
                quality=1.0,
                confidence=1.0,
                timestamp=ts,
                sensor_id="MPU6050",
                metadata={"kinetic_energy_ms2": r.accel_ms2},
            )
        )

        self._evidence_buffer.extend(evidence)
        return evidence


# ---------------------------------------------------------------------------
# Environmental Node (contactless)
# ---------------------------------------------------------------------------

@dataclass
class EnvironmentalReadings:
    """
    Raw readings from the environmental node sensors.

    Attributes
    ----------
    respiration_rate_rpm    : Breaths per minute from mmWave radar.
    radar_movement_magnitude: Thoracic movement magnitude (0 = absent).
    apnea_detected          : True when radar detects cessation of breathing.
    thermal_gradient_pattern: Named thermal pattern (e.g. "periphery_cooling").
    thermal_quality         : Signal quality [0, 1] for the thermal reading.
    """

    respiration_rate_rpm: float = 15.0
    radar_movement_magnitude: float = 1.0
    apnea_detected: bool = False
    thermal_gradient_pattern: str = "normal"
    thermal_quality: float = 1.0


class EnvironmentalNode(BaseNode):
    """
    Contactless environmental node with mmWave Radar (~24 GHz) and MLX90640
    thermal camera (manifesto §3 – "The Environmental Node").
    """

    def __init__(self) -> None:
        super().__init__(NodeID.ENVIRONMENTAL)
        self._readings = EnvironmentalReadings()

    def inject_readings(self, readings: EnvironmentalReadings) -> None:
        """Inject simulated or test readings."""
        self._readings = readings

    def read_evidence(self) -> list[Evidence]:
        r = self._readings
        ts = time.time()
        evidence: list[Evidence] = []

        # --- mmWave Radar ---
        evidence.append(
            Evidence(
                source=NodeID.ENVIRONMENTAL,
                signal_type=SignalType.RADAR,
                value=r.radar_movement_magnitude,
                quality=1.0,
                confidence=1.0,
                timestamp=ts,
                sensor_id="mmWave_24GHz",
                metadata={
                    "respiration_rate_rpm": r.respiration_rate_rpm,
                    "apnea": r.apnea_detected,
                },
            )
        )

        # --- MLX90640 Thermal Camera ---
        evidence.append(
            Evidence(
                source=NodeID.ENVIRONMENTAL,
                signal_type=SignalType.THERMAL,
                value=r.thermal_gradient_pattern,
                quality=r.thermal_quality,
                confidence=r.thermal_quality,
                timestamp=ts,
                sensor_id="MLX90640",
                metadata={
                    "gradient_pattern": r.thermal_gradient_pattern,
                },
            )
        )

        self._evidence_buffer.extend(evidence)
        return evidence


# ---------------------------------------------------------------------------
# Central Hub
# ---------------------------------------------------------------------------

class CentralHub:
    """
    Central aggregation node that runs the Veto Engine, Hypothesis Engine,
    and Clinical Black Box (manifesto §3 – "The Central Hub & Silent HMI").

    The hub collects Evidence from all registered nodes, runs the decision
    pipeline, and routes the result to the appropriate communication channel
    (visual HMI, wearable haptic, or – exceptionally – audible alarm).
    """

    def __init__(
        self,
        black_box: Optional[ClinicalBlackBox] = None,
    ) -> None:
        self.veto_engine = VetoEngine()
        self.hypothesis_engine = HypothesisEngine()
        self.black_box = black_box or ClinicalBlackBox()
        self._nodes: list[BaseNode] = []
        self._communication_callbacks: list[Callable[[ClinicalEvent], None]] = []

    def register_node(self, node: BaseNode) -> None:
        """Register a sensor node with the hub."""
        self._nodes.append(node)

    def on_event(self, callback: Callable[[ClinicalEvent], None]) -> None:
        """Register a callback that fires when a ClinicalEvent is promoted."""
        self._communication_callbacks.append(callback)

    def process_cycle(
        self,
        candidate_description: str,
        severity: EventSeverity = EventSeverity.WARNING,
        force_audible: bool = False,
    ) -> ClinicalEvent | VetoRecord:
        """
        Run one full decision cycle:
        1. Collect evidence from all registered nodes.
        2. Augment with a Hypothesis if one matches.
        3. Pass through the Veto Engine.
        4. Log the result and dispatch to communication channels.

        Returns the ClinicalEvent or VetoRecord produced.
        """
        # Step 1 – collect evidence
        evidence_window: list[Evidence] = []
        for node in self._nodes:
            evidence_window.extend(node.read_evidence())

        # Step 2 – hypothesis
        hypothesis = self.hypothesis_engine.evaluate(evidence_window)
        if hypothesis is not None:
            self.black_box.record_hypothesis(
                hypothesis_name=hypothesis.name,
                description=hypothesis.description,
                confidence=hypothesis.confidence,
                evidence=evidence_window,
            )
            if not hypothesis.actionable:
                # Non-actionable hypothesis means the engine already knows this
                # is an artifact; we can pre-annotate the candidate description
                candidate_description = (
                    f"{candidate_description} [{hypothesis.name}]"
                )

        # Step 3 – veto evaluation
        result = self.veto_engine.evaluate(
            candidate_description=candidate_description,
            evidence_window=evidence_window,
            severity=severity,
            force_audible=force_audible,
        )

        # Step 4 – record and dispatch
        if isinstance(result, ClinicalEvent):
            if hypothesis is not None:
                result.hypothesis = hypothesis.name
            self.black_box.record_event(result)
            for cb in self._communication_callbacks:
                cb(result)
        else:
            self.black_box.record_veto(result)

        return result
