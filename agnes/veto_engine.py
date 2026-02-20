"""
AGNES Veto Engine
=================
Implements the "Subtractive Validation" model described in manifesto §4.

Philosophy
----------
The Veto Engine is a *consensus-based* gate.  A candidate alarm is only
promoted to a ClinicalEvent when independent evidence sources *converge*.
If evidence conflicts (e.g. PPG detects tachycardia while the IMU detects
high kinetic energy), the engine *explicitly suppresses* the alarm and
records the reason as a veto.

Veto logic flow (manifesto §2):
    Signal → Evidence → [Veto Engine] → Event (or Vetoed + logged)

Design contract
---------------
* The engine never discards evidence silently.  Every suppression is recorded
  with a human-readable reason so the Clinical Black Box can reconstruct the
  full decision chain.
* Sound (``audible=True``) is reserved exclusively for system failures or
  life-threatening criticalities that pass ALL validation layers.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Optional

from agnes.evidence import ClinicalEvent, EventSeverity, Evidence, SignalType


# ---------------------------------------------------------------------------
# Veto records
# ---------------------------------------------------------------------------

@dataclass
class VetoRecord:
    """
    Immutable record of a suppressed alarm (append-only, manifesto §6).

    Attributes
    ----------
    veto_id        : Unique identifier for this suppression decision.
    reason         : Human-readable explanation of why the alarm was vetoed.
    conflicting    : Evidence items that caused the conflict.
    candidate_desc : Description of the candidate alarm that was suppressed.
    timestamp      : When the veto decision was made.
    """

    veto_id: str
    reason: str
    conflicting: list[Evidence]
    candidate_desc: str
    timestamp: float = field(default_factory=time.time)

    def __repr__(self) -> str:
        return (
            f"VetoRecord(id={self.veto_id!r}, reason={self.reason!r}, "
            f"ts={self.timestamp:.3f})"
        )


# ---------------------------------------------------------------------------
# Built-in veto rules (manifesto §4 scenarios)
# ---------------------------------------------------------------------------

def _rule_movement_artifact(evidence_window: list[Evidence]) -> Optional[str]:
    """
    Veto PPG/optical readings when simultaneous high-kinetic-energy IMU
    evidence is present (manifesto §4 – "Handling Artifact").
    """
    has_optical_anomaly = any(
        e.signal_type == SignalType.OPTICAL
        and isinstance(e.value, (int, float))
        and e.metadata.get("anomaly", False)
        for e in evidence_window
    )
    has_movement = any(
        e.signal_type == SignalType.MECHANICAL
        and isinstance(e.value, (int, float))
        and float(e.value) > 1.5  # m/s² threshold for significant movement
        for e in evidence_window
    )
    if has_optical_anomaly and has_movement:
        return "Mechanical Agitation Artifact: PPG anomaly coincides with high IMU kinetic energy"
    return None


def _rule_lead_off(evidence_window: list[Evidence]) -> Optional[str]:
    """
    Veto ECG readings when the AD8232 Lead-off pins indicate a disconnected
    lead (manifesto §3 Wearable Node, §5 Scenario 2).
    """
    for e in evidence_window:
        if (
            e.signal_type == SignalType.ELECTRICAL
            and e.metadata.get("lead_off", False)
        ):
            return "Lead Disconnected: AD8232 lead-off detection active"
    return None


def _rule_poor_signal_quality(evidence_window: list[Evidence]) -> Optional[str]:
    """
    Veto any event if all contributing evidence has poor signal quality
    (quality < 0.5) – the system lacks sufficient confidence to alarm.
    """
    unreliable = [e for e in evidence_window if not e.is_reliable]
    if unreliable and len(unreliable) == len(evidence_window):
        return "All evidence unreliable: insufficient signal quality/confidence to promote"
    return None


# Default rule chain applied by VetoEngine unless overridden
DEFAULT_VETO_RULES: list[Callable[[list[Evidence]], Optional[str]]] = [
    _rule_lead_off,
    _rule_movement_artifact,
    _rule_poor_signal_quality,
]


# ---------------------------------------------------------------------------
# VetoEngine
# ---------------------------------------------------------------------------

class VetoEngine:
    """
    Consensus-based alarm gate (manifesto §4).

    Usage
    -----
    engine = VetoEngine()
    result = engine.evaluate(
        candidate_description="Tachycardia",
        evidence_window=[ppg_evidence, imu_evidence],
        severity=EventSeverity.WARNING,
    )
    if isinstance(result, ClinicalEvent):
        ...  # promoted – send silent notification
    elif isinstance(result, VetoRecord):
        ...  # suppressed – log but stay silent
    """

    def __init__(
        self,
        rules: Optional[list[Callable[[list[Evidence]], Optional[str]]]] = None,
    ) -> None:
        self._rules = rules if rules is not None else list(DEFAULT_VETO_RULES)
        self.veto_history: list[VetoRecord] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        candidate_description: str,
        evidence_window: list[Evidence],
        severity: EventSeverity = EventSeverity.WARNING,
        force_audible: bool = False,
    ) -> ClinicalEvent | VetoRecord:
        """
        Evaluate whether a candidate alarm should be promoted or vetoed.

        Parameters
        ----------
        candidate_description : Human-readable description of the candidate alarm.
        evidence_window       : All Evidence objects relevant to this decision.
        severity              : Clinical urgency if the event is promoted.
        force_audible         : Override silent-first rule for true life-threatening
                                criticality (manifesto §5 Scenario 5).

        Returns
        -------
        ClinicalEvent  : if the event passes all veto rules (alarm promoted).
        VetoRecord     : if any rule fires (alarm suppressed, reason recorded).
        """
        # Apply each rule in order; first match wins the veto
        for rule in self._rules:
            reason = rule(evidence_window)
            if reason is not None:
                record = VetoRecord(
                    veto_id=str(uuid.uuid4()),
                    reason=reason,
                    conflicting=list(evidence_window),
                    candidate_desc=candidate_description,
                )
                self.veto_history.append(record)
                return record

        # No veto fired → promote the event
        # Sound is only used when explicitly forced (life-threatening, unrecognised
        # criticality, or apnoea-of-prematurity type scenarios)
        audible = force_audible or severity == EventSeverity.CRITICAL
        return ClinicalEvent(
            event_id=str(uuid.uuid4()),
            description=candidate_description,
            severity=severity,
            contributing_evidence=list(evidence_window),
            timestamp=time.time(),
            audible=audible,
        )

    def add_rule(
        self, rule: Callable[[list[Evidence]], Optional[str]]
    ) -> None:
        """Register an additional veto rule at the end of the chain."""
        self._rules.append(rule)

    @property
    def veto_count(self) -> int:
        """Total number of alarms suppressed since instantiation."""
        return len(self.veto_history)
