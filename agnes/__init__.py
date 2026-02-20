"""
AGNES – Agnostic Global Nodal Evidence System
=============================================

A silent-first clinical intelligence platform that decouples physiological
monitoring from acoustic noise, replacing threshold-based alerting with
multimodal, consensus-based evidence validation.

Architecture (manifesto §2):
    Signal → Evidence → [Veto Engine] → Event → Targeted Communication → Sound (exception)

Core modules
------------
* ``evidence``           – Evidence, ClinicalEvent, and related data structures
* ``veto_engine``        – Consensus-based alarm suppression
* ``hypothesis_engine``  – Probabilistic clinical hypothesis generation
* ``black_box``          – Append-only Clinical Black Box (JSONL / CSV)
* ``nodes``              – Wearable, Environmental and Central Hub nodes
"""

from agnes.evidence import (  # noqa: F401
    Evidence,
    ClinicalEvent,
    EventSeverity,
    NodeID,
    SignalType,
)
from agnes.veto_engine import VetoEngine, VetoRecord  # noqa: F401
from agnes.hypothesis_engine import Hypothesis, HypothesisEngine  # noqa: F401
from agnes.black_box import ClinicalBlackBox  # noqa: F401
from agnes.nodes import (  # noqa: F401
    WearableNode,
    WearableReadings,
    EnvironmentalNode,
    EnvironmentalReadings,
    CentralHub,
)

__version__ = "0.1.0"
__all__ = [
    "Evidence",
    "ClinicalEvent",
    "EventSeverity",
    "NodeID",
    "SignalType",
    "VetoEngine",
    "VetoRecord",
    "Hypothesis",
    "HypothesisEngine",
    "ClinicalBlackBox",
    "WearableNode",
    "WearableReadings",
    "EnvironmentalNode",
    "EnvironmentalReadings",
    "CentralHub",
]
