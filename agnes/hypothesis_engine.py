"""
AGNES Hypothesis Engine
=======================
Implements the "externalization of experienced clinical reasoning" described
in manifesto §4.

The Hypothesis Engine elevates raw numerical readings to probabilistic
clinical hypotheses that clinicians can immediately act upon.  Instead of
"SpO₂ = 88 %" it offers "Apnea of Prematurity – confidence 0.87".

Architecture
------------
Each ``HypothesisRule`` encodes a pattern of converging evidence streams and
maps it to a named clinical hypothesis with a confidence estimate.  Rules are
evaluated in priority order; the first rule that matches returns its
hypothesis.

This design is intentionally simple and deterministic so that every
inference can be audited and understood by a clinician.  Probabilistic
machine-learning models may be layered on top in future iterations but the
rule layer must always remain explainable (manifesto §2, §3 Veto Engine).

Clinical scenarios covered (manifesto §5)
------------------------------------------
1. Mechanical Agitation Artifact  – combative patient
2. Lead Disconnection             – false asystole
3. Shock Physiology Pattern       – silent cold shock
4. Validated Tachyarrhythmia      – true SVT
5. Apnea of Prematurity           – convergent apnea
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from agnes.evidence import Evidence, SignalType


# ---------------------------------------------------------------------------
# Hypothesis result
# ---------------------------------------------------------------------------

@dataclass
class Hypothesis:
    """
    A probabilistic clinical interpretation derived from multimodal evidence.

    Attributes
    ----------
    name        : Short clinical label (e.g. "Apnea of Prematurity").
    description : Detailed clinical narrative suitable for documentation.
    confidence  : Probability [0.0, 1.0] that this is the correct interpretation.
    actionable  : True when the hypothesis warrants targeted communication.
    """

    name: str
    description: str
    confidence: float
    actionable: bool = True

    def __repr__(self) -> str:
        return (
            f"Hypothesis({self.name!r}, confidence={self.confidence:.2f}, "
            f"actionable={self.actionable})"
        )


# ---------------------------------------------------------------------------
# Hypothesis rule type
# ---------------------------------------------------------------------------

HypothesisRule = Callable[[list[Evidence]], Optional[Hypothesis]]


# ---------------------------------------------------------------------------
# Built-in clinical pattern rules (manifesto §5 scenarios)
# ---------------------------------------------------------------------------

def _hypothesis_mechanical_agitation(
    window: list[Evidence],
) -> Optional[Hypothesis]:
    """
    Scenario 1 – "Combative Baby" (manifesto §5).
    PPG anomaly + high IMU movement → artifact, not a true physiological event.
    """
    optical_anomaly = any(
        e.signal_type == SignalType.OPTICAL and e.metadata.get("anomaly", False)
        for e in window
    )
    high_movement = any(
        e.signal_type == SignalType.MECHANICAL
        and isinstance(e.value, (int, float))
        and float(e.value) > 1.5
        for e in window
    )
    if optical_anomaly and high_movement:
        return Hypothesis(
            name="Mechanical Agitation Artifact",
            description=(
                "PPG desaturation/anomaly detected coincidentally with intense "
                "3-axis IMU movement, consistent with patient handling or agitation. "
                "Physiological interpretation is unreliable until patient is calm."
            ),
            confidence=0.90,
            actionable=False,
        )
    return None


def _hypothesis_lead_disconnection(
    window: list[Evidence],
) -> Optional[Hypothesis]:
    """
    Scenario 2 – "False Asystole" (manifesto §5).
    ECG lead-off flag active while mmWave detects ongoing chest movement.
    """
    lead_off = any(
        e.signal_type == SignalType.ELECTRICAL and e.metadata.get("lead_off", False)
        for e in window
    )
    breathing_detected = any(
        e.signal_type == SignalType.RADAR
        and isinstance(e.value, (int, float))
        and float(e.value) > 0  # any positive respiratory movement
        for e in window
    )
    if lead_off and breathing_detected:
        return Hypothesis(
            name="Lead Disconnection",
            description=(
                "AD8232 lead-off detection is active (physical lead disconnection) "
                "while mmWave radar confirms ongoing thoracic movement. "
                "This is a technical artifact, not cardiac arrest. "
                "Nurse notified via wearable haptic channel."
            ),
            confidence=0.97,
            actionable=True,
        )
    return None


def _hypothesis_shock_physiology(
    window: list[Evidence],
) -> Optional[Hypothesis]:
    """
    Scenario 3 – Silent "Cold Shock" (manifesto §5).
    Thermal periphery cooling + reduced PPG pulse amplitude → shock physiology.
    """
    periphery_cooling = any(
        e.signal_type == SignalType.THERMAL
        and e.metadata.get("gradient_pattern") == "periphery_cooling"
        for e in window
    )
    low_pulse_amplitude = any(
        e.signal_type == SignalType.OPTICAL
        and e.metadata.get("pulse_amplitude_low", False)
        for e in window
    )
    if periphery_cooling and low_pulse_amplitude:
        return Hypothesis(
            name="Shock Physiology Pattern",
            description=(
                "Thermal camera detects core-to-periphery gradient consistent with "
                "flow centralisation. PPG pulse amplitude is reduced. "
                "These findings precede overt haemodynamic collapse. "
                "Visual reassessment alert issued before clinical decompensation."
            ),
            confidence=0.82,
            actionable=True,
        )
    return None


def _hypothesis_validated_tachyarrhythmia(
    window: list[Evidence],
) -> Optional[Hypothesis]:
    """
    Scenario 4 – True SVT (manifesto §5).
    ECG + PPG both indicate tachycardia while IMU confirms immobility.
    """
    ecg_tachy = any(
        e.signal_type == SignalType.ELECTRICAL
        and e.metadata.get("tachycardia", False)
        for e in window
    )
    ppg_tachy = any(
        e.signal_type == SignalType.OPTICAL
        and e.metadata.get("tachycardia", False)
        for e in window
    )
    patient_still = any(
        e.signal_type == SignalType.MECHANICAL
        and isinstance(e.value, (int, float))
        and float(e.value) < 0.3  # near-zero kinetic energy
        for e in window
    )
    if ecg_tachy and ppg_tachy and patient_still:
        return Hypothesis(
            name="Validated Tachyarrhythmia",
            description=(
                "ECG and PPG independently confirm tachycardia while IMU confirms "
                "patient immobility, ruling out motion artifact. "
                "High-confidence cardiac arrhythmia. "
                "Staff notified via wearables; room silence maintained."
            ),
            confidence=0.93,
            actionable=True,
        )
    return None


def _hypothesis_apnea_of_prematurity(
    window: list[Evidence],
) -> Optional[Hypothesis]:
    """
    Scenario 5 – Apnea of Prematurity (manifesto §5).
    mmWave detects cessation of chest movement while PPG detects falling SpO₂.
    This is a life-threatening convergence that triggers the audible alarm.
    """
    apnea_radar = any(
        e.signal_type == SignalType.RADAR
        and e.metadata.get("apnea", False)
        for e in window
    )
    spo2_falling = any(
        e.signal_type == SignalType.OPTICAL
        and e.metadata.get("spo2_falling", False)
        for e in window
    )
    if apnea_radar and spo2_falling:
        return Hypothesis(
            name="Apnea of Prematurity",
            description=(
                "mmWave radar detects cessation of thoracic movement and PPG "
                "independently detects falling SpO₂. Convergence of two independent "
                "sources on life-threatening apnea. Immediate physical intervention "
                "required. Audible alarm activated as last resort."
            ),
            confidence=0.95,
            actionable=True,
        )
    return None


# Default rule chain (evaluated in order; first match wins)
DEFAULT_HYPOTHESIS_RULES: list[HypothesisRule] = [
    _hypothesis_lead_disconnection,     # highest specificity first
    _hypothesis_apnea_of_prematurity,
    _hypothesis_validated_tachyarrhythmia,
    _hypothesis_shock_physiology,
    _hypothesis_mechanical_agitation,
]


# ---------------------------------------------------------------------------
# HypothesisEngine
# ---------------------------------------------------------------------------

class HypothesisEngine:
    """
    Converts multimodal evidence into probabilistic clinical hypotheses.

    Usage
    -----
    engine = HypothesisEngine()
    hypothesis = engine.evaluate(evidence_window)
    if hypothesis:
        print(hypothesis.description)
    """

    def __init__(
        self,
        rules: Optional[list[HypothesisRule]] = None,
    ) -> None:
        self._rules = rules if rules is not None else list(DEFAULT_HYPOTHESIS_RULES)

    def evaluate(self, evidence_window: list[Evidence]) -> Optional[Hypothesis]:
        """
        Return the first matching clinical hypothesis or None if no pattern
        matches.

        Parameters
        ----------
        evidence_window : All Evidence items available at the current decision
                          point.

        Returns
        -------
        Hypothesis | None
        """
        for rule in self._rules:
            result = rule(evidence_window)
            if result is not None:
                return result
        return None

    def add_rule(self, rule: HypothesisRule) -> None:
        """Register an additional hypothesis rule at the end of the chain."""
        self._rules.append(rule)
