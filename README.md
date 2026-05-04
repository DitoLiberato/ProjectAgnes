# AGNES (ProjectAgnes)

**Agnostic Global Nodal Evidence System** — a silent-first clinical vigilance architecture for multimodal signal validation, subtractive alarm logic, and auditable clinical event reconstruction.

AGNES is being developed as an **early research and engineering prototype**. Its current purpose is to demonstrate a reproducible architecture for:

- distributed physiological and contextual sensing;
- evidence-based validation before event promotion;
- silent-first, targeted notification;
- append-only traceability for future Clinical Black Box workflows.

> **Research prototype only. Not for clinical use.**  
> This repository does not provide a certified medical device, diagnostic system, patient monitor, treatment recommendation system, or clinical decision-making tool. Nothing in this repository should be used for patient care.

---

## 1. Conceptual Summary

Traditional clinical monitoring often follows a direct chain:

```text
Signal -> Alarm -> Sound -> Stress
```

AGNES explores a different architecture:

```text
Signal -> Evidence -> Event Candidate -> Veto/Promote -> Targeted Notification -> Record
```

The project is built around five core principles:

1. **Silent-first vigilance** — sound is an exception, not the default.
2. **Subtractive validation** — conflicting evidence can explicitly suppress false alarms.
3. **Nodal architecture** — no single sensor is granted absolute authority.
4. **Explainability** — every promoted or vetoed event must have a recorded rationale.
5. **Clinical Black Box readiness** — the system should preserve an auditable trail from day one.

---

## 2. Current MVP Status

The MVP is currently in the **technical foundation / hello-world node phase**.

Validated so far:

| Role | Hardware | PlatformIO env | Firmware status | Bench status |
|---|---|---|---|---|
| Wearable contact node | Seeed XIAO ESP32-C3 | `wearable_esp32` | Synthetic heartbeat + evidence firmware uploaded | PASS |
| HUB node | ESP32-S3-N16R8 | `hub_esp32` | HUB heartbeat + ESP-NOW init + Nextion UART bring-up uploaded | PASS |
| Environmental node | ESP32-S3-N8R2 | `environmental_esp32` | Synthetic heartbeat + environmental evidence firmware uploaded | PASS |

Current limitation:

- The three nodes have passed **standalone bench validation**.
- The **integrated multi-node run is still pending**.
- Current evidence payloads are mostly **synthetic / simulated**, intended to validate message structure, firmware targets, and bench workflow before real sensor integration.

Next engineering gate:

```text
Simulated evidence -> ESP-NOW real transport -> HUB node registry -> append-only Black Box log -> Veto Engine v0 -> HMI state rendering -> real sensors
```

---

## 3. Repository Map

### Engineering Documentation

- [MVP Engineering Portfolio](docs/ENGINEERING_MVP_PORTFOLIO_v0.1.md)
- [MVP Engineering Plan](docs/ENGINEERING_MVP_PLAN.md)
- [Future AI Supervisor Layer](docs/FUTURE_AI_SUPERVISOR_LAYER_v0.1.md)
- [Bench Test Checklist v0.1](docs/BENCH_TEST_CHECKLIST_v0.1.md)
- [First Bench Bring-Up Guide v0.1](docs/FIRST_BENCH_BRINGUP_GUIDE_v0.1.md)
- [Development Log — 2026-02-21 First Wearable Bench PASS](docs/DEVELOPMENT_LOG_2026-02-21_FIRST_WEARABLE_BENCH_PASS.md)
- [Development Log — 2026-02-21 Environmental N16R8 Bench PASS](docs/DEVELOPMENT_LOG_2026-02-21_ENVIRONMENTAL_N16R8_BENCH_PASS.md)
- [Development Log — 2026-02-21 Hardware Role Remap (N16R8 HUB / N8R2 ENV)](docs/DEVELOPMENT_LOG_2026-02-21_HARDWARE_ROLE_REMAP_N16R8_HUB_N8R2_ENV.md)
- [Development Log — 2026-02-21 HUB N16R8 and ENV N8R2 Bench PASS](docs/DEVELOPMENT_LOG_2026-02-21_HUB_N16R8_AND_ENV_N8R2_BENCH_PASS.md)
- [Language Policy](docs/LANGUAGE_POLICY.md)

### Contracts and Protocols

- [Node-HUB Message Schema v0.1](docs/NODE_HUB_MESSAGE_SCHEMA_v0.1.md)
- [HUB-Nextion UART Protocol v0.1](docs/HUB_NEXTION_UART_PROTOCOL_v0.1.md)

### Firmware

- [PlatformIO configuration](firmware/platformio.ini)
- [Wearable Node firmware](firmware/src/wearable/main.cpp)
- [Environmental Node firmware](firmware/src/environmental/main.cpp)
- [HUB Node firmware](firmware/src/hub/main.cpp)
- [Shared Message Layer](firmware/include/agnes_messages.h)

---

## 4. Firmware Architecture

The firmware currently uses PlatformIO with the Arduino framework and three independent build targets:

```text
firmware/
  include/
    agnes_messages.h
  src/
    common/
      agnes_messages.cpp
    wearable/
      main.cpp
    environmental/
      main.cpp
    hub/
      main.cpp
  platformio.ini
```

Current design choice:

- Each sensing node emits structured `heartbeat` and `evidence` messages.
- The HUB initializes ESP-NOW and the Nextion UART interface.
- The shared message layer provides early JSON serialization for the v0.1 message contract.

Important near-term refactor:

- Add `boot_id` to the common envelope.
- Replace raw JSON string fragments with validated payload construction.
- Add inbound ESP-NOW receive callback on HUB.
- Add node registry and duplicate/stale packet detection.
- Add append-only Black Box logging.
- Add deterministic Veto Engine v0.

---

## 5. Hardware Roles

### Wearable Contact Node

Target board:

- Seeed XIAO ESP32-C3

Planned / staged sensors:

- AD8232 ECG front-end
- MAX30102 PPG / SpO₂
- MPU6050 IMU

Current firmware role:

- emits synthetic contact-node heartbeat and PPG-like evidence.

### Environmental Node

Target board:

- ESP32-S3-N8R2

Planned / staged sensors:

- mmWave radar
- MLX90640 thermal camera
- optional RGB vision in later iterations

Current firmware role:

- validates PSRAM availability;
- emits synthetic environmental heartbeat and mmWave-like evidence.

### HUB Node

Target board:

- ESP32-S3-N16R8

Planned / staged responsibilities:

- ESP-NOW message ingestion;
- evidence fusion;
- Veto Engine;
- Notification Engine;
- Nextion HMI rendering;
- append-only local logging.

Current firmware role:

- initializes ESP-NOW;
- initializes Nextion UART;
- emits HUB heartbeat;
- renders basic heartbeat/status fields to the HMI.

### Future AI Supervisor / Edge Intelligence Gateway

A future post-MVP layer may add a more capable local edge computer, such as a Jetson-class device or equivalent AI-capable mini computer.

This layer is planned as an **advisory supervisor**, not as the deterministic safety core. Its role would be to consume structured AGNES records and support:

- consistency auditing across nodes;
- event narrative reconstruction;
- draft medical/nursing documentation;
- Black Box replay;
- hypothesis-support workflows based on validated evidence.

The embedded ESP32 HUB remains the deterministic real-time coordinator. The AI Supervisor interprets, audits, summarizes, and suggests.

---

## 6. Message Contract

The current v0.1 contract uses compact UTF-8 JSON with a mandatory envelope:

- `schema_version`
- `msg_type`
- `msg_id`
- `ts_ms`
- `node_id`
- `seq`

Implemented message types:

- `heartbeat`
- `evidence`

Planned message types:

- `event_candidate`
- `decision_record`
- `command`
- `ack`
- `error`

Future post-MVP advisory record types may include:

- `evidence_summary`
- `advisory_record`
- `draft_clinical_note`

Protocol direction:

- Keep the message contract stable and traceable.
- Treat real sensors as producers of `Evidence`, not as direct alarm triggers.
- Keep HUB logic independent from any specific display, AI supervisor, cloud service, or future wearable/HUD output.

---

## 7. Development Strategy

The current strategy is intentionally incremental:

1. Establish reproducible multi-target firmware builds.
2. Validate standalone firmware upload and serial stability on each board.
3. Validate real inter-node transport using simulated evidence.
4. Implement HUB state registry and append-only record trail.
5. Implement Veto Engine v0 using deterministic rules.
6. Render AGNES states on the Nextion HMI.
7. Integrate real sensors one at a time.
8. Run scenario-based validation with recorded evidence and decisions.
9. Only after the embedded MVP is stable, evaluate an optional AI Supervisor / Edge Intelligence Gateway.

This avoids confusing sensor noise, AI behavior, or hardware acceleration with architecture failure.

---

## 8. Near-Term Technical Priorities

### P0 — Protocol hardening

- Add `boot_id`.
- Standardize `node_role` vs `node_id`.
- Validate score ranges and allowed sensor/signal types.
- Cap maximum payload size.
- Add malformed-message handling.

### P1 — Real ESP-NOW integration

- Implement HUB receive callback.
- Add message acceptance/rejection logs.
- Track last heartbeat and sequence per node.
- Detect degraded/offline nodes.

### P2 — Minimal Clinical Black Box

- Append-only JSON Lines via serial first.
- SD card persistence later.
- Record accepted/rejected messages and decision rationale.

### P3 — Veto Engine v0

Initial deterministic rules:

- PPG abnormal + high motion -> `VETO: movement_artifact`
- PPG abnormal + ECG concordant + low motion -> `PROMOTE: validated_event`
- ECG lead-off -> `TECHNICAL_VETO: lead_disconnected`
- Insufficient convergence -> `HOLD: uncertainty`

### P4 — Future AI Supervisor planning only

- Keep the AI Supervisor out of the MVP critical path.
- Define record types and interface boundaries.
- Preserve deterministic HUB autonomy if the AI layer is absent or unavailable.

---

## 9. Publication-Oriented Framing

This repository is not intended to demonstrate clinical efficacy at this stage.

It is intended to demonstrate:

- a reproducible nodal architecture;
- an evidence-based communication contract;
- traceable engineering decisions;
- a silent-first validation pipeline;
- a foundation for controlled simulated testing.

Potential publication framing:

> A nodal subtractive-validation architecture for silent-first physiological monitoring: design rationale and early embedded prototype.

A future technical manuscript may discuss the AI Supervisor as a planned extension for local narrative reconstruction, advisory interpretation, and documentation support. It should not be framed as autonomous diagnosis or as part of the MVP safety-critical loop.

---

## 10. License / Intellectual Property Note

A formal license has not yet been selected.

Until a license is added, all rights are reserved by default. Reuse, redistribution, or derivative work should not be assumed to be permitted.

The project is public for transparency, technical discussion, and academic/portfolio traceability, not as a certified open medical product.
