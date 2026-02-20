# AGNES – Agnostic Global Nodal Evidence System

> *"Silence is not the absence of monitoring; it is the highest expression of a functioning, trustworthy system."*

AGNES is a **silent-first clinical intelligence platform** for intensive care environments. It replaces threshold-based alarm systems with a **multimodal, consensus-based evidence pipeline** that suppresses technical artifacts, generates probabilistic clinical hypotheses, and issues targeted notifications — reserving audible alarms exclusively for life-threatening, unambiguous events.

## The Problem

Modern ICUs suffer from **alarm fatigue**: monitors fire sound for every sensor artifact, desensitising staff, stressing patients, and degrading cognitive bandwidth. AGNES decouples physiological monitoring from acoustic noise by treating sound as a **system failure state**, not a default output.

## Architecture

```
Raw Sensor Data
      │
      ▼
 [Detection]          ESP32 edge nodes sample MAX30102, AD8232,
      │               MPU6050, mmWave Radar, MLX90640
      ▼
 [Validation]         Evidence layer enriches readings with quality,
      │               confidence, temporal context, and sensor metadata
      ▼
[Veto Engine]         Consensus-based gate: alarms are SUPPRESSED
      │               unless independent sources converge
      ▼
[Hypothesis Engine]   Converts validated evidence into actionable
      │               clinical hypotheses (e.g. "Apnea of Prematurity")
      ▼
[Communication]       Silent by default: wearable haptics, visual HMI
      │               Audible only for critical, unambiguous events
      ▼
[Clinical Black Box]  Append-only JSONL/CSV audit log of every
                      decision, veto, and hypothesis
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| **Evidence** | A sensor reading enriched with source, signal type, quality, confidence, and temporal context — never a raw number |
| **Veto Engine** | Suppresses alarms when conflicting evidence indicates an artifact (movement, lead-off, poor SNR) |
| **Hypothesis Engine** | Maps converging evidence patterns to named clinical hypotheses with confidence scores |
| **Clinical Black Box** | Append-only audit trail that enables shift summaries and automated documentation |

## Clinical Scenarios Implemented (Manifesto §5)

1. **Combative Baby** – PPG desaturation + high IMU kinetic energy → suppressed as *Mechanical Agitation Artifact*
2. **False Asystole** – AD8232 lead-off flag + mmWave breathing detected → suppressed as *Lead Disconnection*
3. **Silent Cold Shock** – MLX90640 periphery cooling + reduced PPG amplitude → *Shock Physiology Pattern* alert before decompensation
4. **True SVT** – ECG + PPG converge on tachycardia, IMU confirms immobility → silent wearable notification
5. **Apnea of Prematurity** – mmWave detects cessation + PPG shows falling SpO₂ → **audible alarm** (last resort)

## Hardware Nodes

### Wearable Node (contact)
- **MAX30102** — PPG heart rate & SpO₂ (artifact-prone; requires validation)
- **AD8232** — ECG with lead-off detection (high-authority cardiac validator)
- **MPU6050** — IMU accelerometer/gyroscope (contextual motion evidence)

### Environmental Node (contactless)
- **~24 GHz mmWave Radar** — independent respiratory monitoring
- **MLX90640** — 32×24 thermal camera for shock physiology detection

### Central Hub
- **ESP32** dual-core microcontroller running the Veto + Hypothesis Engines
- **Nextion** display showing Calm/Conflict states without audio triggers

## Project Structure

```
agnes/
├── __init__.py           # Public API
├── evidence.py           # Evidence, ClinicalEvent data structures
├── veto_engine.py        # Consensus-based alarm suppression
├── hypothesis_engine.py  # Probabilistic clinical hypothesis generation
├── black_box.py          # Append-only audit log (JSONL / CSV)
└── nodes.py              # WearableNode, EnvironmentalNode, CentralHub

tests/
├── test_evidence.py
├── test_veto_engine.py
├── test_hypothesis_engine.py
└── test_nodes.py
```

## Quick Start

```python
from agnes import (
    CentralHub, WearableNode, WearableReadings,
    EnvironmentalNode, EnvironmentalReadings,
    ClinicalBlackBox, EventSeverity,
)
from agnes.evidence import ClinicalEvent
from agnes.veto_engine import VetoRecord

# Create the hub with a persistent black box
with ClinicalBlackBox(output_path="shift_log.jsonl") as bb:
    hub = CentralHub(black_box=bb)

    wearable = WearableNode()
    env = EnvironmentalNode()
    hub.register_node(wearable)
    hub.register_node(env)

    # Scenario 5 – Apnea of Prematurity
    wearable.inject_readings(WearableReadings(spo2_falling=True, ppg_anomaly=True))
    env.inject_readings(EnvironmentalReadings(apnea_detected=True, radar_movement_magnitude=0.0))

    result = hub.process_cycle(
        "Apnea of Prematurity",
        severity=EventSeverity.CRITICAL,
        force_audible=True,
    )

    if isinstance(result, ClinicalEvent):
        print(f"Event promoted: {result.description} | audible={result.audible}")
    elif isinstance(result, VetoRecord):
        print(f"Alarm suppressed: {result.reason}")

    # End-of-shift summary
    print(bb.shift_summary())
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## Philosophy

AGNES answers a single question for every sensor reading:

> **"Is it true, and does it matter?"**

If the answer is uncertain, it stays silent.
