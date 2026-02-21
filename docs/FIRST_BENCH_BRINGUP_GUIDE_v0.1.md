# AGNES First Bench Bring-Up Guide (v0.1)

## 1) Who this guide is for

This guide is for a first-time user of:

- ESP32 hardware
- PlatformIO CLI workflow
- AGNES multi-node firmware structure

It is intentionally detailed and uses a strict step-by-step sequence.

---

## 2) What you will do

By the end of this guide, you will:

1. Connect three ESP32 boards safely.
2. Identify which USB serial port belongs to each board.
3. Upload the correct firmware to each node.
4. Open serial monitors and verify expected runtime behavior.
5. Decide PASS/FAIL for your first bench run.

---

## 2.1) Where to run each command (critical)

- Use the **local host terminal** (Windows PowerShell/Linux/macOS terminal) for USB flashing and serial monitoring.
- Use Codespaces terminal for repository editing and optional cloud builds.

If your board is physically plugged into your computer USB port, assume flash/monitor commands must run locally.

---

## 3) Safety and preparation (read fully before starting)

- Use only USB data cables.
- Do not connect raw external sensor wiring during first bring-up.
- Keep boards on a non-conductive surface.
- If any board gets hot, disconnect immediately.
- Keep one board operation at a time until you are confident.

Recommended physical labeling:

- Board A -> `WEARABLE`
- Board B -> `ENV`
- Board C -> `HUB`

---

## 4) Open the correct project folder

In VS Code terminal, run:

```bash
cd /workspaces/ProjectAgnes
pwd
```

Expected output should end with:

```text
/workspaces/ProjectAgnes
```

Now move into firmware folder:

```bash
cd firmware
pwd
```

Expected output:

```text
/workspaces/ProjectAgnes/firmware
```

---

## 5) Verify PlatformIO command availability

Run:

```bash
pio --version
```

If this prints a version number, continue.
If command not found, stop and fix PlatformIO availability in your dev environment first.

---

## 6) Verify project environments

Run:

```bash
pio project config --json-output
```

Confirm these environments exist:

- `wearable_esp32`
- `environmental_esp32`
- `hub_esp32`

Wearable board requirement:

- The wearable target is a `Seeed XIAO ESP32-C3`.
- In `firmware/platformio.ini`, `wearable_esp32` must use `board = seeed_xiao_esp32c3`.

Environmental board requirement:

- The environmental target is an `ESP32-S3-N8R2`.
- In `firmware/platformio.ini`, `environmental_esp32` must use `board = esp32-s3-devkitc-1-n8r2`.

HUB board requirement:

- The HUB target is an `ESP32-S3-N16R8`.
- In `firmware/platformio.ini`, `hub_esp32` must use `board = esp32-s3-devkitc-1-n16r8`.

---

## 7) Connect one board at a time and map ports

This is the most important beginner step.

### 7.1 Baseline list (before plugging a board)

Run:

```bash
pio device list
```

Copy this output into your notes as "baseline".

### 7.2 Plug only the wearable board

- Connect wearable board by USB.
- Wait 3 to 5 seconds.
- Run again:

```bash
pio device list
```

Find the new port (for example `/dev/ttyUSB0` or `/dev/ttyACM0` on Linux, or `COM5` on Windows).
Write down:

- `WEARABLE_PORT=<new port>`

### 7.3 Repeat for environmental board

- Keep wearable connected.
- Plug environmental board.
- Run:

```bash
pio device list
```

Write down:

- `ENV_PORT=<new port>`

### 7.4 Repeat for hub board

- Keep previous two connected.
- Plug hub board.
- Run:

```bash
pio device list
```

Write down:

- `HUB_PORT=<new port>`

You now have a persistent mapping for this session.

---

## 8) Build all firmware targets (sanity gate)

Run:

```bash
pio run -e wearable_esp32 -e environmental_esp32 -e hub_esp32
```

Required result:

- all three must end with `SUCCESS`.

If any target fails, do not proceed to upload. Resolve build error first.

---

## 9) Upload firmware to each node (exact commands)

Replace placeholders with your real ports.

### 9.1 Upload wearable

```bash
pio run -e wearable_esp32 -t upload --upload-port <WEARABLE_PORT>
```

Expected: upload completion message with no fatal error.

If you see `This chip is ESP32-C3, not ESP32`, stop and verify:

- wearable env uses `board = seeed_xiao_esp32c3`
- you rebuilt after pulling latest changes

If upload stalls:

- Press and hold `BOOT` on board.
- Start upload command.
- Release `BOOT` when flashing starts.

### 9.2 Upload environmental

```bash
pio run -e environmental_esp32 -t upload --upload-port <ENV_PORT>
```

Expected: upload completion message with no fatal error.

### 9.3 Upload hub

```bash
pio run -e hub_esp32 -t upload --upload-port <HUB_PORT>
```

Expected: upload completion message with no fatal error.

---

## 10) Run serial monitor and validate each node

Use one monitor at a time first (simpler for beginners).

General monitor command:

```bash
pio device monitor -p <PORT> -b 115200
```

Exit monitor any time with:

- `Ctrl+C`

Important for Windows users:

- `Ctrl+C` also interrupts live monitoring.
- Do not use `Ctrl+C` while trying to copy evidence output.
- Prefer mouse selection + `Enter` (or your terminal copy shortcut).

### 10.1 Wearable expected behavior

Monitor command:

```bash
pio device monitor -p <WEARABLE_PORT> -b 115200
```

You should see:

1. `[wearable] boot ok`
2. One JSON `heartbeat` after boot
3. One JSON `evidence` every ~5 seconds

What to verify in JSON:

- `msg_type` appears as `heartbeat` and `evidence`
- `node_id` equals `contact_node`
- `seq` increases each message

### 10.2 Environmental expected behavior

Monitor command:

```bash
pio device monitor -p <ENV_PORT> -b 115200
```

You should see:

1. `[environmental] boot ok`
2. One JSON `heartbeat` after boot
3. One JSON `evidence` every ~5 seconds

What to verify:

- `node_id` equals `env_node`
- `sensor_type` should be `mmwave` in current synthetic evidence
- `seq` increases

### 10.3 Hub expected behavior

Monitor command:

```bash
pio device monitor -p <HUB_PORT> -b 115200
```

You should see:

1. `[hub] boot start`
2. `[hub] uart_nextion=ok`
3. `[hub] esp_now=ok` (or `error` if init fails)
4. JSON `heartbeat` about every ~2 seconds

What to verify:

- `node_id` equals `hub`
- `sensor_status` includes `esp_now` and `uart_nextion`
- `seq` increases

---

## 11) Run a 5-minute stability check

For each node, keep monitor open for 5 minutes and observe:

- no reboot loop
- periodic messages remain continuous
- no corrupted JSON output

Pass condition for node stability:

- steady output + increasing `seq` + no crash.

---

## 12) PASS/FAIL decision for first bench run

Mark **PASS** only if all conditions below are true:

- All three environments build successfully.
- All three boards upload successfully.
- All three boards show expected boot logs.
- Wearable and environmental publish `evidence` periodically.
- Hub publishes `heartbeat` periodically.
- No board enters reboot loop during 5-minute observation.

If one condition fails, mark **FAIL** and record exact failing step.

---

## 13) Troubleshooting (beginner-oriented)

## A) `pio device list` shows no board

- Change cable (most common issue).
- Try another USB port.
- Reconnect board and wait 5 seconds.
- Check if board power LED is on.

## B) Upload permission/port busy errors

- Close any open monitor first (`Ctrl+C`).
- Retry upload command.
- Confirm you are using the correct port for that board.

## C) Garbage characters in monitor

- Ensure baud is exactly `115200`.
- Restart monitor with the command from this guide.

## D) Board keeps resetting

- Remove external peripherals.
- Use direct USB connection (avoid weak hub).
- Reflash firmware.

## E) Hub reports `esp_now=error`

- This is a valid diagnostic state for now.
- Record it in logs and continue bench verification of serial behavior.

## F) Upload error says chip mismatch (`ESP32-C3` vs `ESP32`)

- Confirm wearable board config in `platformio.ini` is `seeed_xiao_esp32c3`.
- Run clean + upload again.

## G) Monitor appears frozen after copy attempt

- Check if `Ctrl+C` was pressed accidentally.
- Start monitor again and press board reset once.

---

## 14) What this first test does NOT validate yet

This first bring-up validates local firmware execution and serial output.
It does **not** yet validate:

- real sensor acquisition
- real ESP-NOW end-to-end node-to-hub transport
- HUB fusion logic and Veto Engine decisions

Those are next milestones after this bench baseline is stable.

---

## 15) Quick command summary (copy/paste)

```bash
cd /workspaces/ProjectAgnes/firmware
pio --version
pio device list
pio run -e wearable_esp32 -e environmental_esp32 -e hub_esp32
pio run -e wearable_esp32 -t upload --upload-port <WEARABLE_PORT>
pio run -e environmental_esp32 -t upload --upload-port <ENV_PORT>
pio run -e hub_esp32 -t upload --upload-port <HUB_PORT>
pio device monitor -p <WEARABLE_PORT> -b 115200
pio device monitor -p <ENV_PORT> -b 115200
pio device monitor -p <HUB_PORT> -b 115200
```

Related references:

- `docs/BENCH_TEST_CHECKLIST_v0.1.md`
- `docs/NODE_HUB_MESSAGE_SCHEMA_v0.1.md`
- `firmware/platformio.ini`
