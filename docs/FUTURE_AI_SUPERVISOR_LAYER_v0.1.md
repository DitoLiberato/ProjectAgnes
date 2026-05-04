# AGNES Future AI Supervisor Layer (v0.1)

## 1) Purpose

This document records a planned post-MVP architectural extension for AGNES: an **AI Supervisor / Edge Intelligence Gateway**.

The current MVP remains focused on deterministic node-to-HUB messaging, evidence validation, silent-first notification, and append-only records. The AI Supervisor is a future layer for interpretation, auditing, summarization, and documentation support after the embedded MVP is working.

---

## 2) Core Architectural Rule

```text
ESP32 HUB = deterministic core
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

---

## 3) Candidate Hardware Class

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

## 4) Candidate AI Workloads

The AI Supervisor may eventually host a local model such as a Gemma-class model or equivalent.

Initial workloads should be bounded and record-based:

- summarize validated records;
- generate draft shift summaries;
- assist medical/nursing documentation drafts from structured events;
- point out inconsistencies in evidence streams;
- explain veto/promote decisions in natural language;
- support replay and technical debugging.

The AI layer should use structured AGNES records as input, not unbounded raw free-text clinical context.

---

## 5) Integration Model

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

## 6) Suggested Future Record Types

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

### AdvisoryRecord

Non-binding interpretive response from the AI Supervisor.

Candidate fields:

- `advisory_id`
- `related_decision_id`
- `advisory_type`
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

---

## 7) Safety and Scope Boundaries

The AI Supervisor is:

- advisory;
- optional;
- record-based;
- separate from the deterministic embedded core;
- logged separately from HUB decisions.

It is not:

- required for the MVP;
- an autonomous diagnostic authority;
- a replacement for clinician judgment;
- a replacement for the Veto Engine;
- a certified medical product.

---

## 8) Publication Relevance

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
- hypothesis-support workflows based on validated records.

---

## 9) Summary

The embedded AGNES MVP should prove the deterministic architecture first. The future AI Supervisor can then add local intelligence without corrupting the safety and auditability of the core.

> **The embedded HUB decides and records. The AI Supervisor interprets, audits, summarizes, and suggests.**
