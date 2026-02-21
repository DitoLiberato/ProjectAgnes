# AGNES Development Log — 2026-02-21

## Milestone

First full bench **PASS** for the wearable node (`wearable_esp32`) using a real USB upload and a 5-minute stability observation.

## Context

This run was executed from a **local Windows host** (PowerShell), not from the Codespaces terminal, due to physical USB access requirements.

## What was validated

- Local repository clone synchronized with `origin/main`.
- Firmware upload to Seeed XIAO ESP32-C3 completed successfully.
- Serial monitor output remained stable for 5 minutes.
- `seq` field increased monotonically.
- Evidence messages were emitted at approximately 5-second intervals.
- No spontaneous reboot loop observed.

## Issues found during bring-up

1. Board mismatch on first upload attempt.
   - Error: `This chip is ESP32-C3, not ESP32. Wrong --chip argument?`
   - Root cause: wearable env inherited `board = esp32dev`.
   - Resolution: set `board = seeed_xiao_esp32c3` in `firmware/platformio.ini` under `[env:wearable_esp32]`.

2. USB device not visible in Codespaces terminal.
   - Root cause: remote environment lacks direct access to host USB serial for this workflow.
   - Resolution: perform flashing/monitoring from local host terminal.

3. Serial monitor interruption on Windows during copy action.
   - Root cause: `Ctrl+C` was used while monitor was active, which stops monitoring.
   - Resolution: avoid `Ctrl+C` during active observation; use mouse selection and `Enter` (or terminal-specific copy shortcut).

## Corrective actions now documented

- Bench checklist updated with explicit board/port preflight and environment guidance.
- First bring-up guide updated with:
  - local-vs-codespaces rule for USB flashing;
  - wearable board identity and expected upload target;
  - monitor copy-safety note for Windows users.

## Next recommended milestone

Run the same bench PASS flow for:

1. environmental node;
2. hub node;
3. then a multi-node synchronized capture session.
