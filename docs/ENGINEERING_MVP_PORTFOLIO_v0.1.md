# AGNES — MVP Engineering Portfolio (v0.1)

## 1) Purpose of this document

This file records the engineering decisions made so far in the AGNES MVP, with a focus on:

- technical traceability;
- design rationale;
- clear linkage between problems, solutions, and results;
- portfolio-grade communication for industry and academia.

Time scope: up to the PlatformIO multi-target firmware bootstrap milestone and successful build validation across the three nodes.

---

## 2) MVP product view

AGNES is a **silent-first** clinical vigilance architecture built on subtractive multimodal validation.

Target pipeline:

`Signal -> Evidence -> Event Candidate -> Veto/Promote -> Targeted Notification -> Record`

Technical objective of this phase:

- establish a reproducible development foundation;
- standardize the node-to-hub message contract;
- enable incremental evolution of fusion logic (Veto Engine) without structural rework.

---

## 3) Design decisions implemented

## D1 — Three-node distributed architecture

**Decision**

- Split responsibilities into `wearable`, `environmental`, and `hub` nodes.

**Rationale**

- Functional isolation improves debugability and experimental validation.
- Topology mirrors realistic deployment constraints and independent evidence sources.

**Impact**

- Three baseline firmware targets created and compiling independently.

## D2 — Embedded framework and build toolchain

**Decision**

- Use ESP32 + Arduino framework with PlatformIO.

**Rationale**

- Stable and widely adopted toolchain.
- Fast prototyping and lower onboarding friction for collaborators.

**Impact**

- Multi-environment `platformio.ini` with reproducible builds in the dev container.

## D3 — v0.1 contract based on a mandatory envelope

**Decision**

- Enforce common envelope fields (`schema_version`, `msg_type`, `msg_id`, `ts_ms`, `node_id`, `seq`) plus type-specific payloads.

**Rationale**

- Decouple producers from consumers.
- Preserve versioning, ordering, and auditability from day one.

**Impact**

- Shared firmware API implemented for `heartbeat` and `evidence` compact JSON messages.

## D4 — Separation between specification and implementation

**Decision**

- Keep protocol in engineering docs and implement in a shared message layer (`include` + `src/common`).

**Rationale**

- Protocol review can evolve without immediate firmware breakage.
- Avoid duplicated serialization logic across node applications.

**Impact**

- All three firmware targets now publish protocol-consistent messages through the same API.

## D5 — Synthetic telemetry bootstrap strategy

**Decision**

- Start with synthetic payloads to validate integration and message flow before real sensor wiring.

**Rationale**

- Reduces early integration risk and verifies architecture assumptions sooner.

**Impact**

- MVP already demonstrates structured periodic publishing behavior aligned with schema v0.1.

---

## 4) Problems faced and applied solutions

## P1 — Development stack blocked by virtualization/WSL/Docker issues

**Problem**

- Docker Desktop startup and WSL consistency issues blocked containerized workflow.

**Applied solution**

- BIOS/UEFI virtualization enablement;
- WSL update and runtime validation;
- Ubuntu distro installation;
- Docker engine validation with `docker version` and `hello-world`.

**Result**

- Stable Linux-based development environment for embedded build execution.

## P2 — Operational error when pasting `.ini` file content into shell

**Problem**

- Shell interpreted configuration lines as commands.

**Applied solution**

- File creation via correct redirection flow and post-creation validation.

**Result**

- Valid `platformio.ini` detected by PlatformIO and builds executed successfully.

## P3 — Build artifacts accidentally committed

**Problem**

- `firmware/.pio` build artifacts were tracked in git.

**Applied solution**

- Add `firmware/.pio/` to `.gitignore`;
- remove artifacts from index;
- amend commit.

**Result**

- Clean history, lighter repository, and professional SCM hygiene.

---

## 5) Verifiable technical results to date

## Infrastructure

- Dev container running on Ubuntu 24.04.x.
- Docker engine operational with Linux backend.
- Reproducible local workflow in the project workspace.

## Firmware

- `firmware/` structure organized by node plus shared layer.
- Successful builds for all three PlatformIO environments:
  - `wearable_esp32`
  - `environmental_esp32`
  - `hub_esp32`

## Protocol

- Common envelope implemented in code.
- `heartbeat` and `evidence` message types operationalized across all nodes.
- Per-node sequencing and deterministic message IDs enabled for traceability.

---

## 6) Delivered artifacts in this phase

- PlatformIO multi-target base (`firmware/platformio.ini`).
- Initial firmware applications for the three nodes.
- Shared message layer:
  - `firmware/include/agnes_messages.h`
  - `firmware/src/common/agnes_messages.cpp`
- Periodic synthetic message emission aligned with schema v0.1.

---

## 7) MVP trade-offs

- **JSON payloads in MVP**: better readability and auditability; less efficient than binary encoding.
- **Arduino framework**: faster prototyping; less low-level control than pure ESP-IDF.
- **Synthetic-first telemetry**: accelerates architecture validation; delays real-signal noise characterization.
- **Strict MVP scope**: prioritizes reproducible proof-of-concept over full clinical feature coverage.

---

## 8) Portfolio value (industry and academia)

The current MVP demonstrates transferable engineering competencies:

- distributed embedded systems design;
- contract-driven communication and protocol governance;
- safety-oriented architecture choices with auditability constraints;
- source control discipline and repository hygiene;
- ability to translate clinical concepts into executable technical artifacts.

---

## 9) Recommended next milestones

1. Implement real ESP-NOW transport using the common envelope.
2. Integrate real sensor data paths and calibrate quality/confidence criteria.
3. Implement `event_candidate` and `decision_record` in HUB logic.
4. Persist append-only local Black Box records with stable serialization.
5. Add replay harness for scenario-driven Veto Engine validation.

---

## 10) Conclusion

At this point, AGNES MVP has progressed from concept documentation to an executable, versioned, and verifiable technical baseline.

The project now has:

- a compilable multi-node architecture;
- an initial implemented communication contract;
- explicit, traceable engineering decisions with measurable outcomes.

This marks a **solid Phase-1 engineering milestone**, suitable as a technical portfolio artifact for discussions with R&D teams, academic groups, and embedded/healthtech recruiters.
