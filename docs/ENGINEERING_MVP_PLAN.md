# AGNES MVP Engineering Plan (v0.1)

## 1) MVP Objective

Provide a demonstrable and reproducible proof that AGNES (silent-first + subtractive multimodal validation) can reduce false alarms without losing relevant critical-event sensitivity.

### Core hypothesis

Convergence of independent evidence sources improves decision quality compared to threshold-only alarm logic.

### Success criteria

- Reduced false-positive rate versus threshold-only baseline.
- Preserved sensitivity in simulated critical events.
- End-to-end latency compatible with real-time vigilance demonstrations.
- 100% of decisions recorded with an auditable rationale trail.

---

## 2) MVP Scope

### In scope

- Complete AGNES pipeline: `Signal -> Evidence -> Event Candidate -> Veto/Promote -> Targeted Notification -> Record`.
- Three functional physical nodes with local communication.
- Silent-first HMI with explainable state transitions.
- Local append-only record (Clinical Black Box).
- Validation protocol with representative simulated scenarios.

### Out of scope (MVP)

- Certified medical product for real clinical deployment.
- Autonomous diagnosis.
- Mandatory cloud stack and EHR integration.
- Advanced AI/ML models as core dependency.

---

## 3) Reference Architecture

### Hardware topology

1. **HUB: ESP32-S3**
   - Evidence fusion
   - Veto Engine
   - Silent-notification routing
   - Nextion HMI control and state rendering
   - Audio escalation only for validated critical exceptions
   - Local append-only logging

2. **Wearable contact node: XIAO ESP32-C3**
   - `AD8232` (ECG)
   - `MAX30102` (PPG/SpO₂)
   - `MPU6050` (IMU)

3. **Environmental node: ESP32-S3**
   - `mmWave` (respiration and movement context)
   - `MLX90640` (thermal gradients and hemodynamic trend clues)

### Communication

- Primary: ESP-NOW.
- Secondary: serial channel for bench debugging and capture.

### HMI

- **Nextion Intelligent Series** as the main visual/interaction console.
- Minimum states: `CALM`, `CONFLICT`, `VALIDATED_EVENT`, `DEGRADED`, `CRITICAL_AUDIO`.
- Always display: current state, decision reason, supporting/conflicting signals, confidence, and active notification channel.

### Mandatory clinical visual content (MVP)

- Numeric: `SpO₂ (%)`, `Heart Rate (bpm)`
- Curves: `PPG pleth`, `ECG waveform`
- Agitation index (`0-100`) based on `IMU + mmWave`
- Zonal thermal body-map derived values (no raw frame streaming)

### Thermal body zones (MVP)

- `head`
- `upper_limbs_proximal`
- `upper_limbs_distal`
- `thorax`
- `abdomen`
- `lower_limbs_proximal`
- `lower_limbs_distal`

### HMI update policy

- `ECG`: continuous high-priority updates
- `PPG`: continuous high-priority updates
- `HR`/`SpO₂`: fast periodic updates
- Agitation index: medium periodic updates
- Thermal panel: slow trend update, default `60s`

### HUB <-> Nextion interface requirements (MVP)

- Dedicated UART link.
- Short state-oriented messages (`state`, `reason_code`, `confidence`, `latency_ms`).
- Minimum HMI input commands: `ack_event`, `mute_request`, `page_change`, `tech_check_request`.
- Minimum HUB output commands: `render_state`, `render_reason`, `render_priority`, `render_connectivity`.
- Safety rule: UI interaction never suppresses validated critical safety decisions.

---

## 4) Sensor roles and authority model

- **ECG (AD8232)**: high-authority rhythm validation.
- **PPG (MAX30102)**: cardiovascular complement (HR/SpO₂), motion-sensitive.
- **IMU (MPU6050)**: wearable kinematic context (agitation/handling/movement).
- **mmWave**: respiration pattern and independent motion context.
- **MLX90640**: thermal context for core-periphery trend clues.

### Authority rule (MVP)

- No single sensor can unilaterally confirm a critical event.
- Critical events require multimodal convergence with minimum quality gates.
- mmWave/thermal can raise investigation priority but cannot independently close diagnosis.

---

## 5) Logical data contract (v0.1)

### Evidence (minimum inference unit)

Mandatory fields:

- `event_id` (uuid)
- `timestamp_ms` (epoch)
- `node_id` (`wearable_contact`, `environmental`, `hub`)
- `sensor_type` (`ecg`, `ppg`, `imu`, `mmwave`, `thermal`)
- `signal_type` (`electrical`, `optical`, `mechanical`, `thermal`)
- `value` (numeric or simple object)
- `quality_score` (`0.0-1.0`)
- `confidence_score` (`0.0-1.0`)
- `context_tags` (e.g., `movement_high`, `lead_off`, `stable_rest`)

### EventCandidate

- `candidate_type`
- `supporting_evidence_ids`
- `conflicting_evidence_ids`
- `temporal_window_ms`
- `candidate_score`

### DecisionRecord (Black Box)

- `decision_id`
- `candidate_id`
- `decision` (`promote`, `veto`, `hold`, `degraded_mode`)
- `reason_code`
- `explanation_text`
- `notified_channels` (`hmi`, `wearable_haptic`, `audio`)
- `latency_ms`

---

## 6) Veto Engine v1 (deterministic and explainable)

### Principles

- Consensus-driven safety, not single-threshold triggering.
- Explicit conflict suppression with documented rationale.
- Audio escalation only for validated criticality or systemic observability loss.

### Base rules

1. **Critical event promotion**
   - At least two coherent independent sources.
   - Sensor-specific minimum quality/confidence gates.

2. **Motion artifact veto**
   - Example: altered PPG + high IMU motion + non-supportive mmWave context.

3. **Technical veto**
   - Example: ECG lead-off under suspected asystole.

4. **Hold state (uncertainty)**
   - No convergence: continue monitoring, notify silently, register conflict.

5. **Audio escalation (exception)**
   - High criticality + robust convergence, or major observability degradation.

---

## 7) Operational states

- `CALM`: stable and coherent signals.
- `CONFLICT`: source inconsistency/artifact suspicion.
- `VALIDATED_EVENT`: multimodal confirmation reached.
- `DEGRADED`: partial sensing/communication loss.
- `CRITICAL_AUDIO`: audible escalation enabled by safety rule.

### Nextion visual mapping

- Dedicated unambiguous view per state.
- Every state transition logged with timestamp and reason.
- `CONFLICT -> CALM` and `VALIDATED_EVENT -> CALM` require explicit resolution update.

---

## 8) Validation scenarios (MVP)

1. **Agitation artifact**
   - Expected: veto with `movement_artifact` reason.

2. **ECG disconnection**
   - Expected: veto with `lead_disconnected` plus silent technical notice.

3. **Real resting tachycardia**
   - Expected: promotion via ECG+PPG convergence with low movement context.

4. **Simulated apnea with desaturation**
   - Expected: critical promotion, with possible `CRITICAL_AUDIO` escalation.

5. **Thermal hemodynamic-risk pattern**
   - Expected: `hold` or re-evaluation notice with explicit rationale.

6. **Node/sensor failure**
   - Expected: `DEGRADED` state with clear operational limits.

---

## 9) Evaluation metrics

- False-positive rate per scenario.
- Sensitivity in simulated critical scenarios.
- Decision latency (median and p95).
- Ratio of events with explicit recorded explanation.
- Inter-node communication availability.
- HMI rendering integrity (required fields and stable curves).
- Thermal zonal refresh reliability at `60s` cadence.

---

## 10) Risks and mitigations

1. **ECG noise in compact wearable setup**
   - Mitigation: layout hygiene, grounding, filtering, optional external ADC.

2. **Environmental thermal variability (MLX90640)**
   - Mitigation: calibration windows, distance/FOV control, thermal quality gating.

3. **Motion-context conflicts (IMU vs mmWave)**
   - Mitigation: temporal coherence rules and cross-source consistency scoring.

4. **Inter-node time synchronization drift**
   - Mitigation: periodic synchronization and fixed fusion windows.
