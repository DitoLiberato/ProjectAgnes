# AGNES (PojectAgnes)

Agnostic Global Nodal Evidence System — arquitetura **silent-first** para monitoramento clínico com validação multimodal.

## Índice mestre

### Documentação de engenharia

- [Portfolio de Engenharia do MVP](docs/ENGINEERING_MVP_PORTFOLIO_v0.1.md)
- [Plano de Engenharia do MVP](docs/ENGINEERING_MVP_PLAN.md)

### Contratos e protocolos

- [Node-HUB Message Schema v0.1](docs/NODE_HUB_MESSAGE_SCHEMA_v0.1.md)
- [HUB-Nextion UART Protocol v0.1](docs/HUB_NEXTION_UART_PROTOCOL_v0.1.md)

### Firmware

- [Estrutura PlatformIO](firmware/platformio.ini)
- [Nó Wearable](firmware/src/wearable/main.cpp)
- [Nó Ambiental](firmware/src/environmental/main.cpp)
- [Nó HUB](firmware/src/hub/main.cpp)
- [Camada comum de mensagens](firmware/include/agnes_messages.h)

## Estado atual

- MVP em fase de base técnica consolidada (infra + firmware multipacote + contrato inicial de mensagens).
- Próximo marco: integração ESP-NOW real + Veto Engine no HUB com trilha append-only.
