# AGNES Future AI Supervisor Layer (v0.2)

## 1) Purpose

This document records a planned post-MVP architectural extension for AGNES: an **AI Supervisor / Edge Intelligence Gateway**.

The current MVP remains focused on deterministic node-to-HUB messaging, evidence validation, silent-first notification, HMI rendering, and append-only records. The AI Supervisor is a future layer for interpretation, auditing, summarization, documentation support, and post-event review after the embedded MVP is working.

This layer should be treated as **future architecture planning**, not an immediate MVP dependency.

---

## 2) Core Architectural Rule

```text
ESP32 HUB = deterministic embedded core
AI Supervisor = advisory interpretation and documentation support
Cloud = optional longitudinal analysis and scale
```

The ESP32 HUB should remain responsible for real-time embedded coordination:

- node message intake;
- node health tracking;
- deterministic Veto Engine rules;
- local HMI state;
- append-only records.

The AI Supervisor should consume structured AGNES records and produce advisory outputs. It should not replace the embedded deterministic core.

Core principle:

> **The embedded HUB decides and records. The AI Supervisor interprets, audits, summarizes, and suggests.**

---

## 3) Model-Agnostic AI Pipeline

AGNES should remain **model-agnostic** in the same way it is sensor-agnostic and output-device-agnostic.

The future AI Supervisor should not be hardwired to any single model family. Instead, it should expose interchangeable adapters for different model roles.

Proposed abstract pipeline:

```text
DecisionRecord / EvidenceSummary / NodeHealth
        ↓
Structured Validator Model
        ↓
Verified Structured Summary
        ↓
Narrative Model
        ↓
Human-Readable Advisory Output
        ↓
Output Validator / Consistency Check
        ↓
AdvisoryRecord / NarrativeSummary / DraftClinicalNote
```

Current example model families, used only for planning convenience:

- **Qwen-class model** as a structured validator, JSON auditor, and consistency checker.
- **Gemma / MedGemma-class model** as a narrative generator for human-readable explanations and documentation drafts.
- Other future alternatives may include Llama-class, Mistral-class, Phi-class, or locally fine-tuned AGNES-specific models.

The architecture should be documented and implemented as:

```text
ValidatorModelAdapter -> NarrativeModelAdapter -> OutputValidationAdapter
```

not as:

```text
Qwen -> Gemma
```

This preserves model substitutability.

---

## 4) Serial Validator-Narrator Pattern

The preferred future pattern is a **serial AI pipeline** rather than a single general-purpose model.

### 4.1 Structured Validator Model

Role:

- validate record completeness;
- detect missing fields;
- separate evidence from inference;
- identify conflicts and convergences;
- normalize structured records;
- produce a constrained intermediate object.

Example output concept:

```json
{
  "validated_event_summary": {
    "event_type": "vetoed_ppg_tachycardia",
    "reason": "motion_artifact",
    "supporting_evidence": ["imu_motion_high"],
    "conflicting_evidence": ["ppg_hr_spike"],
    "missing_data": ["ecg_confirmation"],
    "confidence_label": "moderate"
  }
}
```

### 4.2 Narrative Model

Role:

- generate concise human-readable explanations;
- draft shift summaries;
- draft medical or nursing documentation from validated records;
- explain why a veto or promotion occurred;
- generate advisory text with explicit uncertainty.

The Narrative Model should receive the **Verified Structured Summary**, not raw unbounded sensor logs.

### 4.3 Output Validator

Role:

- check that the generated text does not introduce unsupported claims;
- verify that every statement can be traced back to structured AGNES records;
- flag hallucinated or unsupported additions;
- mark outputs as requiring human review.

This can be implemented by:

- a smaller validator model;
- the same structured model used in the first stage;
- deterministic rule checks;
- schema validation plus text-evidence alignment heuristics.

---

## 5) Candidate Hardware Class

The future AI Supervisor may run on a more capable local edge computer, for example:

- NVIDIA Jetson Orin Nano-class developer kit;
- NVIDIA Jetson Orin NX-class edge computer;
- NVIDIA Jetson AGX Orin-class system for later high-compute phases;
- compact x86/ARM mini PC with local AI acceleration;
- equivalent edge AI hardware.

Hardware selection should be deferred until the MVP has demonstrated:

1. real ESP-NOW node-to-HUB exchange;
2. HUB node registry;
3. append-only Black Box records;
4. deterministic Veto Engine v0;
5. HMI state rendering.

---

## 6) Candidate AI Workloads

Initial workloads should be bounded and record-based:

- summarize validated records;
- generate draft shift summaries;
- assist medical/nursing documentation drafts from structured events;
- point out inconsistencies in evidence streams;
- explain veto/promote decisions in natural language;
- support replay and technical debugging;
- produce advisory hypothesis-support text based only on validated records.

The AI layer should use structured AGNES records as input, not unbounded raw free-text clinical context.

---

## 7) Integration Model

Planned data flow:

```text
Wearable / Environmental Nodes
        ↓
ESP32 HUB deterministic core
        ↓
DecisionRecord / EvidenceSummary / NodeHealth
        ↓
AI Supervisor
        ↓
AdvisoryRecord / NarrativeSummary / DraftNote / AuditFlag
```

Candidate non-core communication channels:

- USB serial;
- Wi-Fi UDP;
- MQTT;
- HTTP REST;
- WebSocket;
- local file handoff from Black Box logs.

The HUB should continue operating even if the AI Supervisor is absent, offline, slow, or unavailable.

---

## 8) Suggested Future Record Types

### EvidenceSummary

Compact summary of recent evidence windows.

Candidate fields:

- `summary_id`
- `window_start_ms`
- `window_end_ms`
- `included_nodes`
- `included_sensors`
- `quality_summary`
- `notable_conflicts`
- `notable_convergences`

### VerifiedStructuredSummary

Intermediate constrained output from the validator stage.

Candidate fields:

- `verified_summary_id`
- `source_record_ids`
- `event_type`
- `reason_code`
- `supporting_evidence`
- `conflicting_evidence`
- `missing_or_degraded_inputs`
- `confidence_label`
- `allowed_narrative_scope`

### AdvisoryRecord

Non-binding interpretive response from the AI Supervisor.

Candidate fields:

- `advisory_id`
- `related_decision_id`
- `advisory_type`
- `model_role` (`validator`, `narrator`, `output_validator`)
- `model_family`
- `confidence_label`
- `summary_text`
- `evidence_referenced`
- `limitations`
- `requires_human_review`

### DraftClinicalNote

Documentation-support draft generated from validated AGNES records.

Candidate fields:

- `note_id`
- `note_type`
- `source_record_ids`
- `draft_text`
- `human_review_required`
- `generated_at_ms`
- `unsupported_claims_detected`

---

## 9) Cost Model Considerations

Future AI Supervisor deployment has several cost categories.

### 9.1 Local Edge Inference

Expected costs:

- purchase of AI-capable edge hardware;
- storage for models and logs;
- power consumption;
- cooling/enclosure design;
- maintenance and software updates;
- engineering time for deployment and benchmarking.

Advantages:

- no per-token inference cost;
- better privacy posture;
- less dependence on internet connectivity;
- closer alignment with AGNES edge-first philosophy.

Trade-offs:

- limited model size depending on hardware;
- local optimization burden;
- hardware lifecycle management.

### 9.2 API-Based Inference

Expected costs:

- per-token input/output charges;
- possible hosting or platform fees;
- bandwidth and logging costs;
- privacy, compliance, and data governance review.

Advantages:

- easier benchmarking against stronger models;
- no local GPU/edge hardware requirement;
- faster experimentation.

Trade-offs:

- recurring cost;
- external dependency;
- data-sharing constraints;
- higher governance burden for health-related data.

### 9.3 Fine-Tuning / Adaptation

Not recommended early.

Potential future costs:

- curated dataset creation;
- de-identification and governance;
- GPU compute;
- model evaluation;
- human review of outputs;
- versioning and regression testing.

AGNES should first rely on:

```text
structured prompting -> schema validation -> few-shot examples -> model comparison
```

Fine-tuning should only be considered after a meaningful library of reviewed `DecisionRecord`, `VerifiedStructuredSummary`, `AdvisoryRecord`, and `DraftClinicalNote` examples exists.

---

## 10) Safety and Scope Boundaries

The AI Supervisor is:

- advisory;
- optional;
- record-based;
- separate from the deterministic embedded core;
- logged separately from HUB decisions;
- constrained by structured inputs and schema-validated outputs.

It is not:

- required for the MVP;
- an autonomous diagnostic authority;
- a replacement for clinician judgment;
- a replacement for the Veto Engine;
- a certified medical product.

All human-readable AI outputs should be marked as:

```text
human_review_required = true
source = structured_agnes_records_only
```

---

## 11) Publication Relevance

For the technical manuscript, this future layer helps frame AGNES as a broader clinical evidence architecture rather than a simple alarm filter.

The MVP paper should remain focused on:

- nodal evidence flow;
- subtractive validation;
- silent-first notification;
- append-only record generation.

The AI Supervisor can be presented as a planned extension for:

- local narrative reconstruction;
- Black Box replay assistance;
- documentation automation;
- hypothesis-support workflows based on validated records;
- serial validator-narrator architecture for safer human-readable outputs.

The manuscript should make clear that the AI layer is **outside the initial deterministic MVP critical path**.

---

## 12) Summary

The embedded AGNES MVP should prove the deterministic architecture first. The future AI Supervisor can then add local intelligence without corrupting the safety and auditability of the core.

Preferred future pattern:

```text
Structured Validator Model -> Narrative Model -> Output Validator
```

Practical current example:

```text
Qwen-class validator -> Gemma/MedGemma-class narrator -> validator/rule-based consistency check
```

Final architectural rule:

> **The embedded HUB decides and records. The AI Supervisor validates structure, interprets, audits, summarizes, and suggests.**
