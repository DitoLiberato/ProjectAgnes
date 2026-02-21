# AGNES Development Log — 2026-02-21

## Milestone

Environmental node (`environmental_esp32`) bench **PASS** on real hardware `ESP32-S3-N16R8`, including successful PSRAM initialization and 5-minute runtime stability.

## Context

This run was executed from a **local Windows host** (PowerShell) due to direct USB serial access requirements.

## What was validated

- Local repository updated to latest `origin/main`.
- Firmware build and upload completed to `COM12` (USB-UART / CH343).
- Boot sequence completed without reset loop.
- PSRAM detection reached expected state: `[environmental] psram=ok`.
- Heartbeat payload reported `"psram":"ok"`.
- Evidence messages remained continuous for ~5 minutes.
- `seq` increased monotonically during observation window.

## Issues found during bring-up and resolutions

1. Flash attempt on wrong USB connector (`OTG`) failed to connect.
   - Symptom: `Failed to connect to ESP32-S3: No serial data received`.
   - Resolution: switched to board USB-UART connector (detected as `COM12`).

2. Initial PSRAM boot error after first successful flash.
   - Symptom: `PSRAM chip not found` and `[environmental] psram=error`.
   - Root cause: board memory mode for S3 N16R8 not fully specified.
   - Resolution: updated custom board/environment config for OPI PSRAM (`memory_type = qio_opi`, `psram_type = opi`), then clean rebuild and reflash.

## Artifacts updated

- `firmware/boards/esp32-s3-devkitc-1-n16r8.json`
- `firmware/platformio.ini`
- commit: `4309a5f`

## Current bench status snapshot

- Wearable node bench: **PASS**
- Environmental node bench: **PASS**
- Hub node bench: **PENDING**
- Integrated multi-node run: **PENDING**

## Next recommended milestone

1. Run HUB standalone bench PASS (`hub_esp32`) for 5 minutes.
2. Run integrated wearable + environmental + hub session.
3. Capture synchronized logs and validate expected state transitions.
