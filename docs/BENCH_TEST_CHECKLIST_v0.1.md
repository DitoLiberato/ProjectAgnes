# AGNES Bench Test Checklist (v0.1)

## 1) Goal

Provide a practical and repeatable checklist to run first bench tests for the three MVP firmware targets:

- `wearable_esp32`
- `environmental_esp32`
- `hub_esp32`

This checklist assumes synthetic telemetry mode (current MVP state) and serial validation.

---

## 2) Required hardware

- 3x ESP32 boards (one for each target: wearable, environmental, hub)
- 3x USB data cables (not charge-only cables)
- A powered USB hub (recommended)
- Stable computer power source (avoid low battery during flashing)

Optional but useful:

- Labels/stickers to name each board (`WEARABLE`, `ENV`, `HUB`)
- Notebook/spreadsheet for test logs

---

## 3) Required software

- VS Code with this repository opened
- Dev container active
- PlatformIO CLI available (`pio` command)
- Local host terminal for USB flashing (recommended)

Important execution rule:

- Build commands can run in Codespaces.
- USB flash/monitor should run on the local host terminal where the board is physically connected.

Quick check:

```bash
cd /workspaces/ProjectAgnes/firmware
pio --version
```

---

## 4) Pre-flight checklist

Before connecting boards:

- [ ] Workspace path is correct: `/workspaces/ProjectAgnes`
- [ ] Firmware path exists: `/workspaces/ProjectAgnes/firmware`
- [ ] `platformio.ini` has the 3 environments
- [ ] Wearable physical board is `Seeed XIAO ESP32-C3`
- [ ] Environmental physical board is `ESP32-S3-N16R8`
- [ ] USB cables are known-good data cables
- [ ] You can identify each board physically

Before upload:

- [ ] No board is shorted or heating unexpectedly
- [ ] All boards are connected by USB
- [ ] Serial ports are detected

Port discovery command:

```bash
cd /workspaces/ProjectAgnes/firmware
pio device list
```

Record mapping:

- [ ] Wearable port = `____________`
- [ ] Environmental port = `____________`
- [ ] Hub port = `____________`

---

## 5) Build validation checklist

Run once before first flash:

```bash
cd /workspaces/ProjectAgnes/firmware
pio run -e wearable_esp32 -e environmental_esp32 -e hub_esp32
```

Pass criteria:

- [ ] `wearable_esp32` = `SUCCESS`
- [ ] `environmental_esp32` = `SUCCESS`
- [ ] `hub_esp32` = `SUCCESS`

---

## 6) Upload checklist (per board)

### Wearable upload

```bash
cd /workspaces/ProjectAgnes/firmware
pio run -e wearable_esp32 -t upload --upload-port <WEARABLE_PORT>
```

- [ ] Upload completed without error

### Environmental upload

```bash
cd /workspaces/ProjectAgnes/firmware
pio run -e environmental_esp32 -t upload --upload-port <ENV_PORT>
```

- [ ] Upload completed without error

### Hub upload

```bash
cd /workspaces/ProjectAgnes/firmware
pio run -e hub_esp32 -t upload --upload-port <HUB_PORT>
```

- [ ] Upload completed without error

---

## 7) Serial runtime checklist

Open monitor for each board (one at a time):

```bash
cd /workspaces/ProjectAgnes/firmware
pio device monitor -p <PORT> -b 115200
```

Stop monitor with `Ctrl+C`.

### Expected logs

Wearable expected:

- [ ] `[wearable] boot ok`
- [ ] One `heartbeat` JSON after boot
- [ ] One `evidence` JSON every ~5 seconds
- [ ] `seq` increases monotonically

Environmental expected:

- [ ] `[environmental] boot ok`
- [ ] One `heartbeat` JSON after boot
- [ ] One `evidence` JSON every ~5 seconds
- [ ] `seq` increases monotonically

Hub expected:

- [ ] `[hub] boot start`
- [ ] `[hub] uart_nextion=ok`
- [ ] `[hub] esp_now=ok` (or `error` if radio init failed)
- [ ] One `heartbeat` JSON every ~2 seconds
- [ ] `seq` increases monotonically

---

## 8) Minimum acceptance criteria (MVP synthetic bench)

Mark test as **PASS** only if all are true:

- [ ] All 3 firmware targets compile
- [ ] All 3 boards flash successfully
- [ ] All 3 boards boot and emit JSON logs
- [ ] Message shape follows schema v0.1
- [ ] No spontaneous reboot loop during 5-minute observation

Reference schema:

- `docs/NODE_HUB_MESSAGE_SCHEMA_v0.1.md`

---

## 9) Common failure checklist

If upload fails:

- [ ] Confirm correct `--upload-port`
- [ ] Press board `BOOT` button during upload start (if required)
- [ ] Replace cable with known data cable
- [ ] Close other serial monitor tools using the same port
- [ ] If error says `This chip is ESP32-C3, not ESP32`, confirm wearable env board is `seeed_xiao_esp32c3`

If monitor shows no logs:

- [ ] Confirm baud is `115200`
- [ ] Press `EN`/`RST` button once
- [ ] Verify correct board port
- [ ] Ensure monitor was not interrupted by `Ctrl+C`

If board resets repeatedly:

- [ ] Try another USB port/hub
- [ ] Remove external peripherals temporarily
- [ ] Reflash firmware

---

## 10) Bench test log template

Use this template for each board:

- Date/time:
- Board role:
- USB port:
- Firmware env:
- Upload result: PASS/FAIL
- Boot log seen: YES/NO
- Heartbeat seen: YES/NO
- Evidence seen (if applicable): YES/NO
- Seq increasing: YES/NO
- Notes:

Overall run:

- Final result: PASS/FAIL
- Blocking issues:
- Next action:
