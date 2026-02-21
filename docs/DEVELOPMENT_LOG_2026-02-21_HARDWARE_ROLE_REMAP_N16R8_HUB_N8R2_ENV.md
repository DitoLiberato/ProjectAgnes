# AGNES Development Log — 2026-02-21

## Milestone

Hardware role remap approved and applied in firmware configuration:

- HUB -> `ESP32-S3-N16R8`
- Environmental node -> `ESP32-S3-N8R2`
- Wearable node -> `Seeed XIAO ESP32-C3` (unchanged)

## Why this remap

`N16R8` provides larger flash/PSRAM headroom and is better allocated to HUB growth (fusion logic, records, HMI integration, and communication orchestration).

## Firmware/config changes applied

- Added custom board profile: `firmware/boards/esp32-s3-devkitc-1-n8r2.json`
- Updated `environmental_esp32` in `firmware/platformio.ini` to use `esp32-s3-devkitc-1-n8r2`
- Kept `hub_esp32` on `esp32-s3-devkitc-1-n16r8`
- Memory mode alignment:
  - HUB (`N16R8`): `memory_type=qio_opi`, `psram_type=opi`
  - ENV (`N8R2`): `memory_type=qio_qspi`, `psram_type=qspi`

## Build validation results

- `pio run -e hub_esp32` -> `SUCCESS`
- `pio run -e environmental_esp32` -> `SUCCESS`

## Bench status impact

- Environmental PASS recorded earlier on `N16R8` remains historical.
- Environmental node now requires re-validation on `N8R2` hardware.
- HUB standalone validation on `N16R8` remains pending.
- Integrated 3-node bench remains pending.

## Next actions

1. Flash/test HUB firmware on `N16R8` board (5-minute stability gate).
2. Flash/test environmental firmware on `N8R2` board (PSRAM + heartbeat gate).
3. Execute integrated wearable + environmental + hub bench.
