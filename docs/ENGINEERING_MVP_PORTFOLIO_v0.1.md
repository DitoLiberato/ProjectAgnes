# AGNES — Engineering Portfolio do MVP (v0.1)

## 1) Propósito deste documento

Este arquivo registra as decisões de engenharia tomadas até aqui no AGNES MVP, com foco em:

- rastreabilidade técnica;
- justificativa de design;
- relação entre problema, solução e resultado observado;
- apresentação de portfólio para indústria e academia.

Escopo temporal: até o marco de bootstrap do firmware multipacote no PlatformIO e validação de build dos três nós.

---

## 2) Visão de produto do MVP

AGNES é um sistema de vigilância clínica **silent-first**, baseado em validação multimodal subtrativa.

Pipeline-alvo do MVP:

`Signal -> Evidence -> Event Candidate -> Veto/Promote -> Targeted Notification -> Record`

Objetivo técnico desta fase:

- estabelecer uma base reprodutível de desenvolvimento;
- padronizar contrato de mensagens entre nós;
- habilitar evolução incremental de lógica de fusão (Veto Engine) sem retrabalho estrutural.

---

## 3) Decisões de design realizadas

## D1 — Arquitetura distribuída de três nós

**Decisão**

- Separar funções em `wearable`, `environmental` e `hub`.

**Racional**

- Isolamento funcional facilita debug e validação experimental.
- Aproxima a topologia ao cenário real de uso (fontes independentes de evidência).

**Impacto**

- Código base inicial criado e compilando em três ambientes independentes.

## D2 — Framework embarcado e ferramenta de build

**Decisão**

- Usar ESP32 + Arduino Framework com PlatformIO.

**Racional**

- Cadeia de build estável e amplamente adotada na indústria.
- Menor barreira de entrada para prototipagem rápida e colaboração.

**Impacto**

- Projeto com `platformio.ini` multiambiente e builds reproduzíveis no dev container.

## D3 — Contrato de mensagens v0.1 orientado a envelope comum

**Decisão**

- Definir envelope obrigatório (`schema_version`, `msg_type`, `msg_id`, `ts_ms`, `node_id`, `seq`) + payload por tipo.

**Racional**

- Evitar acoplamento entre origem do dado e consumidor.
- Garantir versionamento, ordenação e auditabilidade desde o primeiro dia.

**Impacto**

- API comum implementada em firmware para `heartbeat` e `evidence` com serialização JSON compacta.

## D4 — Separação entre schema e implementação

**Decisão**

- Manter contrato em documento de engenharia e implementação em camada comum (`include` + `src/common`).

**Racional**

- Permite revisar protocolo sem quebrar imediatamente firmware.
- Reduz duplicação e divergência entre nós.

**Impacto**

- Três firmwares passaram a emitir mensagens consistentes via mesma API.

## D5 — Estratégia de bootstrap com telemetria sintética

**Decisão**

- Iniciar com payloads de exemplo (dados sintéticos) para validar pipeline de integração.

**Racional**

- Antecipar riscos de integração de protocolo e estados antes de conectar sensores reais.

**Impacto**

- MVP já demonstra formato de mensagens e ciclo de publicação periódica.

---

## 4) Problemas encontrados e como foram resolvidos

## P1 — Ambiente de desenvolvimento bloqueado por virtualização/WSL/Docker

**Problema**

- Docker Desktop não subia e WSL estava inconsistente para fluxo de dev container.

**Solução aplicada**

- Ajustes de BIOS/UEFI para virtualização;
- atualização e validação do WSL;
- instalação da distro Ubuntu;
- validação ponta a ponta com `docker version` e `hello-world`.

**Resultado**

- Ambiente Linux de desenvolvimento estabilizado e pronto para build embarcado.

## P2 — Erro operacional ao colar conteúdo de arquivo `.ini` no shell

**Problema**

- Bash tentou executar conteúdo de configuração como comandos.

**Solução aplicada**

- Criação dos arquivos via redirecionamento correto (`cat <<EOF`) e validação posterior.

**Resultado**

- `platformio.ini` válido e reconhecido pelo PlatformIO.

## P3 — Commit inicial incluiu artefatos de build

**Problema**

- Diretório `firmware/.pio` foi versionado indevidamente.

**Solução aplicada**

- Inclusão de regra no `.gitignore` para `firmware/.pio/`;
- remoção dos artefatos do índice e emenda do commit.

**Resultado**

- Histórico limpo, repositório leve e prática compatível com engenharia profissional.

---

## 5) Resultados técnicos verificáveis até aqui

## Infraestrutura

- Dev container ativo em Ubuntu 24.04.x.
- Docker funcional com engine Linux.
- Fluxo de desenvolvimento reproduzível no workspace.

## Firmware

- Estrutura `firmware/` organizada por nó e camada comum.
- Três ambientes PlatformIO compilando com sucesso:
  - `wearable_esp32`
  - `environmental_esp32`
  - `hub_esp32`

## Protocolo

- Envelope comum implementado no código.
- Tipos `heartbeat` e `evidence` operacionalizados em todos os nós.
- IDs e sequência por nó preparados para rastreabilidade.

---

## 6) Entregáveis de código desta etapa

- Base PlatformIO multiambiente (`firmware/platformio.ini`).
- Firmwares iniciais para os três nós.
- Camada comum de mensagens:
  - `firmware/include/agnes_messages.h`
  - `firmware/src/common/agnes_messages.cpp`
- Publicação periódica de mensagens sintéticas alinhadas ao schema v0.1.

---

## 7) Trade-offs assumidos no MVP

- **JSON no transporte MVP**: mais legível e auditável; menos eficiente que binário.
- **Arduino framework**: acelera protótipo; menor controle fino que stack bare-metal/IDF pura.
- **Dados sintéticos primeiro**: acelera integração de arquitetura; adia validação de ruído real de sensores.
- **Escopo enxuto**: prioriza prova de conceito reprodutível sobre completude funcional clínica.

---

## 8) Valor de portfólio (indústria e academia)

Este MVP já demonstra competências transferíveis:

- engenharia de sistemas embarcados distribuídos;
- definição e governança de contratos de dados;
- decisões de arquitetura orientadas a segurança e auditabilidade;
- disciplina de versionamento e higiene de repositório;
- capacidade de transformar conceito clínico em artefato técnico executável.

---

## 9) Próximos marcos recomendados

1. Implementar transporte real ESP-NOW usando o envelope comum.
2. Conectar sensores reais por nó e preencher campos de qualidade/confiança com critérios explícitos.
3. Implementar `event_candidate` e `decision_record` no HUB.
4. Persistir trilha append-only local (Black Box) com serialização estável.
5. Criar harness de replay para cenários de validação do Veto Engine.

---

## 10) Conclusão

Até este ponto, o AGNES MVP saiu do nível conceitual para uma base executável, versionada e verificável.

O projeto já possui:

- arquitetura de nós definida e compilável;
- contrato de comunicação inicial implementado;
- evidência concreta de evolução técnica com decisões justificadas.

Isso caracteriza um **marco de engenharia sólido de fase 1**, adequado como cartão de visitas técnico para discussão com times de P&D, grupos acadêmicos e recrutadores de sistemas embarcados/healthtech.
