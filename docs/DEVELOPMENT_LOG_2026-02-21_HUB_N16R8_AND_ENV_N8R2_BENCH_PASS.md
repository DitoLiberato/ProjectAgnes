# AGNES Development Log — 2026-02-21

## Milestone

Bench validation **PASS** for both remapped ESP32-S3 roles:

- HUB node on `ESP32-S3-N16R8`
- Environmental node on `ESP32-S3-N8R2`

## Context

After hardware role remap, standalone bench validation was executed from local Windows host terminal (PowerShell) with USB-UART serial ports.

## HUB validation (`hub_esp32` on N16R8)

### Upload flow

- Full chip erase executed successfully.
- Firmware upload completed successfully on `COM12`.

### Runtime validation

- Stable heartbeat stream observed for ~5 minutes.
- `sensor_status` confirmed:
  - `"esp_now":"ok"`
  - `"uart_nextion":"ok"`
  - `"wifi_mode":"sta"`
- No reboot loop or lockup observed.

## Environmental validation (`environmental_esp32` on N8R2)

### Upload flow

- Firmware upload completed successfully on `COM13`.

### Runtime validation

- Boot completed with expected logs.
- PSRAM initialized correctly:
  - `[environmental] psram=ok`
  - heartbeat `sensor_status.psram = "ok"`
- Evidence stream continued as expected (periodic, monotonic `seq`).
- No reboot loop observed during observation window.

## Bench state after this milestone

- Wearable standalone bench: **PASS**
- HUB standalone bench (N16R8): **PASS**
- Environmental standalone bench (N8R2): **PASS**
- Integrated multi-node bench (wearable + environmental + hub): **PENDING**

## Next recommended gate

Run integrated multi-node bench and capture synchronized logs from all 3 nodes.
