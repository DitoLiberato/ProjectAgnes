# AGNES (ProjectAgnes)

Agnostic Global Nodal Evidence System — a **silent-first** architecture for clinical monitoring with multimodal validation.

## Master Index

### Engineering Documentation

- [MVP Engineering Portfolio](docs/ENGINEERING_MVP_PORTFOLIO_v0.1.md)
- [MVP Engineering Plan](docs/ENGINEERING_MVP_PLAN.md)
- [Bench Test Checklist v0.1](docs/BENCH_TEST_CHECKLIST_v0.1.md)
- [First Bench Bring-Up Guide v0.1](docs/FIRST_BENCH_BRINGUP_GUIDE_v0.1.md)
- [Development Log — 2026-02-21 First Wearable Bench PASS](docs/DEVELOPMENT_LOG_2026-02-21_FIRST_WEARABLE_BENCH_PASS.md)
- [Development Log — 2026-02-21 Environmental N16R8 Bench PASS](docs/DEVELOPMENT_LOG_2026-02-21_ENVIRONMENTAL_N16R8_BENCH_PASS.md)
- [Development Log — 2026-02-21 Hardware Role Remap (N16R8 HUB / N8R2 ENV)](docs/DEVELOPMENT_LOG_2026-02-21_HARDWARE_ROLE_REMAP_N16R8_HUB_N8R2_ENV.md)
- [Development Log — 2026-02-21 HUB N16R8 and ENV N8R2 Bench PASS](docs/DEVELOPMENT_LOG_2026-02-21_HUB_N16R8_AND_ENV_N8R2_BENCH_PASS.md)
- [Language Policy](docs/LANGUAGE_POLICY.md)

### Contracts and Protocols

- [Node-HUB Message Schema v0.1](docs/NODE_HUB_MESSAGE_SCHEMA_v0.1.md)
- [HUB-Nextion UART Protocol v0.1](docs/HUB_NEXTION_UART_PROTOCOL_v0.1.md)

### Firmware

- [Estrutura PlatformIO](firmware/platformio.ini)
- [Wearable Node](firmware/src/wearable/main.cpp)
- [Environmental Node](firmware/src/environmental/main.cpp)
- [HUB Node](firmware/src/hub/main.cpp)
- [Shared Message Layer](firmware/include/agnes_messages.h)

## Current Status

- MVP is in the consolidated technical foundation phase (infrastructure + multi-target firmware + initial message contract).
- Bench status: wearable PASS, hub PASS (N16R8), environmental PASS (N8R2).
- Next milestone: integrated multi-node run (wearable + environmental + hub), followed by real ESP-NOW integration + HUB Veto Engine with an append-only record trail.


