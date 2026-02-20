# AGNES (PojectAgnes)

Agnostic Global Nodal Evidence System — a **silent-first** architecture for clinical monitoring with multimodal validation.

## Master Index

### Engineering Documentation

- [MVP Engineering Portfolio](docs/ENGINEERING_MVP_PORTFOLIO_v0.1.md)
- [MVP Engineering Plan](docs/ENGINEERING_MVP_PLAN.md)
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
- Next milestone: real ESP-NOW integration + HUB Veto Engine with an append-only record trail.
