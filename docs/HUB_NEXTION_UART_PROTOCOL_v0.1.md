# AGNES HUB-Nextion UART Protocol v0.1

## 1) Objective

Define the communication protocol between HUB (ESP32-S3) and Nextion HMI for:

- real-time clinical rendering (`ECG`, `PPG`, `HR`, `SpO₂`);
- operational context (AGNES state, reasons, connectivity);
- low-frequency zonal thermal panel updates;
- basic operator actions (`ack`, navigation, technical checks).

---

## 2) MVP technical assumptions

- Physical medium: dedicated UART between HUB and Nextion.
- Initial baud rate: `115200` (evaluate `230400` if needed).
- Command model: HUB sends Nextion commands.
- Nextion terminator: `0xFF 0xFF 0xFF` after each command.
- Development-mode inbound parser expects line-based text commands from Nextion (`\n`/`\r` terminated).

---

## 3) Screen model (MVP)

### 3.1 Main screen

Mandatory fields:

- Numeric: `HR`, `SpO2`
- Waveform: `ECG`
- Waveform: `PPG`
- Index: `AgitationIndex (0-100)`
- AGNES state: `CALM | CONFLICT | VALIDATED_EVENT | DEGRADED | CRITICAL_AUDIO`
- Short reason text: `reason_code` + concise description

### 3.2 Zonal thermal screen

Display per-zone values:

- `head`
- `upper_limbs_proximal`
- `upper_limbs_distal`
- `thorax`
- `abdomen`
- `lower_limbs_proximal`
- `lower_limbs_distal`

Derived indicators:

- `core_periphery_delta_c`
- `thermal_trend` (`rising | stable | falling`)

Refresh policy: default `60s`.

---

## 4) Outbound message model (HUB -> Nextion)

All commands end with `0xFF 0xFF 0xFF`.

### 4.1 State rendering

Example:

`state.txt="VALIDATED_EVENT"`

Associated fields:

- `reason.txt`
- `confidence.val` (0-100)
- `latency.val` (ms)
- `channel.txt` (`hmi | wearable_haptic | audio`)

### 4.2 Numeric updates

Examples:

- `hr.val=132`
- `spo2.val=96`
- `agit.val=37`

### 4.3 Waveform feed

Examples:

- `add ecg,0,85`
- `add ppg,0,63`

Priority policy:

1. ECG waveform
2. PPG waveform
3. Vital numerics
4. State/reason fields
5. Thermal panel

### 4.4 Connectivity summary

Examples:

- `node_wear.txt="OK"`
- `node_env.txt="DEGRADED"`
- `link.txt="ESP-NOW"`

### 4.5 MVP development fields currently implemented

The HUB currently sends these component updates on each heartbeat cycle:

- `proto.txt`
- `state.txt`
- `reason.txt`
- `confidence.val`
- `latency.val`
- `node_wear.txt`
- `node_env.txt`
- `link.txt`
- `uptime.val`
- `page_id.val`
- `cmd_count.val`
- `ts_lsb.val`

Boot-time fields also sent once:

- `boot.txt="hub_boot_ok"`
- `fw.txt="hub-0.1.0"`

---

## 5) Inbound message model (Nextion -> HUB)

Minimum command set:

- `ack_event`
- `mute_request`
- `page_change:<id>`
- `tech_check_request`

Current parser behavior:

- Accepts plain text commands from UART line buffer.
- Valid commands are logged by HUB to serial in JSON form.
- Unknown commands are logged as `"hmi_cmd":"unknown"`.

Each inbound command must include:

- `ts_ms`
- `operator_id` (or `unknown`)
- `source_page`

Example logical frame:

```json
{
  "cmd": "ack_event",
  "ts_ms": 1700001000123,
  "operator_id": "nurse_a",
  "source_page": "main"
}
```

---

## 6) Safety rules

- HMI input cannot cancel validated critical safety decisions.
- `mute_request` is advisory and must be validated by HUB policy.
- Every HMI-originated action must be logged in the append-only trail.
- If UI desynchronization is detected, HUB must force a full re-render.

---

## 7) Error handling

### 7.1 UART write timeout

- Retry command up to `N` times.
- If retries fail, enter `DEGRADED` view and log communication fault.

### 7.2 Invalid inbound command

- Ignore payload.
- Log parse error with raw frame hash.

### 7.3 HMI unavailable

- Keep decision engine running.
- Continue silent routing where possible.
- Escalate to `CRITICAL_AUDIO` only if safety policy requires.

---

## 8) Minimal telemetry for traceability

For each rendered event, record:

- `decision_id`
- `state`
- `reason_code`
- `confidence`
- `render_ts_ms`
- `render_latency_ms`
- `hmi_ack_ts_ms` (if received)

---

## 9) Validation checklist (MVP)

- State transitions render correctly for all five AGNES states.
- ECG/PPG waveform updates remain stable under continuous load.
- Thermal panel updates do not starve waveform rendering.
- `ack_event` and `mute_request` are parsed and logged.
- HUB recovers from forced UART interruption with deterministic fallback.

---

## 10) Versioning and compatibility

- Protocol version: `uart_proto_version = "0.1"`
- Backward-incompatible changes require `0.x -> 0.y` bump and migration note.
- Optional fields must be safely ignored by older parsers.
