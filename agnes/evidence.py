"""
AGNES Evidence Layer
====================
Defines the core Evidence data structure that AGNES uses instead of raw sensor
readings.  Every piece of data processed by the system must be wrapped in an
Evidence object so that the Veto Engine and Hypothesis Engine have enough
metadata to reason about it.

Signal processing chain (manifesto §2):
    Detection → Validation → Decision → Targeted Communication → Recording
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class SignalType(Enum):
    """Nature of the detection modality (manifesto §4)."""
    ELECTRICAL = auto()   # ECG (AD8232)
    OPTICAL = auto()      # PPG (MAX30102)
    THERMAL = auto()      # Thermal camera (MLX90640)
    MECHANICAL = auto()   # IMU (MPU6050)
    RADAR = auto()        # mmWave radar (~24 GHz)


class NodeID(Enum):
    """Logical identifiers for the cooperative sensor nodes (manifesto §3)."""
    WEARABLE = "wearable"          # Contact wearable node
    ENVIRONMENTAL = "environmental"  # Contactless environmental node
    CENTRAL_HUB = "central_hub"    # Hub / display node


@dataclass
class Evidence:
    """
    A validated sensor reading enriched with the metadata required for
    clinical reasoning (manifesto §4 - Defining Evidence vs Raw Data).

    Attributes
    ----------
    source      : Node that produced this evidence.
    signal_type : Physical modality of the measurement.
    value       : Numeric reading or categorical state string.
    quality     : Signal-to-Noise Ratio proxy in [0.0, 1.0];
                  1.0 = perfect signal, 0.0 = unusable.
    confidence  : Probability [0.0, 1.0] that the value is physiologically
                  accurate given current sensor health.
    timestamp   : Unix epoch (seconds) when the sample was taken.
    duration_s  : Duration of the observation window in seconds (0 = instant).
    sensor_id   : Optional string identifying the specific sensor.
    metadata    : Arbitrary key-value pairs for extra context (e.g. lead-off
                  flag, kinetic energy magnitude).
    """

    source: NodeID
    signal_type: SignalType
    value: float | str
    quality: float = 1.0
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)
    duration_s: float = 0.0
    sensor_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.quality <= 1.0:
            raise ValueError(f"quality must be in [0, 1], got {self.quality}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be in [0, 1], got {self.confidence}"
            )

    @property
    def is_reliable(self) -> bool:
        """True when both quality and confidence are above minimum thresholds."""
        return self.quality >= 0.5 and self.confidence >= 0.5


class EventSeverity(Enum):
    """Clinical urgency of a promoted event."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ClinicalEvent:
    """
    A validated, promoted clinical event ready for targeted communication
    (manifesto §2, layer 4).

    Only events that pass Veto Engine consensus reach this stage.
    """

    event_id: str
    description: str
    severity: EventSeverity
    contributing_evidence: list[Evidence]
    hypothesis: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    audible: bool = False  # Sound is the exception, not the rule (manifesto §1)

    def __repr__(self) -> str:
        return (
            f"ClinicalEvent(id={self.event_id!r}, severity={self.severity.value}, "
            f"audible={self.audible}, hypothesis={self.hypothesis!r})"
        )
