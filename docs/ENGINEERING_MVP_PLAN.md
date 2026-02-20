# AGNES MVP Engineering Plan (v0.1)

## 1) Objetivo do MVP

Provar, de forma demonstrável e reprodutível, que a arquitetura AGNES (silent-first + validação subtrativa multimodal) reduz alarmes falsos sem perder detecção de eventos críticos relevantes.

### Hipótese central

A convergência entre fontes independentes de evidência melhora a qualidade da decisão clínica digital quando comparada ao modelo tradicional baseado em limiares isolados.

### Critérios de sucesso

- Redução de falsos positivos em comparação ao baseline threshold-only.
- Preservação de sensibilidade em eventos críticos simulados.
- Latência ponta-a-ponta adequada para demonstração de vigilância em tempo real.
- 100% dos eventos com trilha de decisão auditável (promoção, veto ou incerteza).

---

## 2) Escopo do MVP

### Incluído

- Pipeline AGNES completo: `Signal -> Evidence -> Event Candidate -> Veto/Promote -> Targeted Notification -> Record`.
- Três nós físicos funcionais com comunicação local.
- HMI silenciosa com explicabilidade de decisão.
- Registro append-only local (Clinical Black Box).
- Protocolo de validação com cenários simulados.

### Fora de escopo (MVP)

- Produto regulado para uso clínico real.
- Diagnóstico automatizado.
- Infraestrutura cloud obrigatória e integração com prontuário.
- Modelos avançados de IA/ML como dependência principal.

---

## 3) Arquitetura de referência (definida)

## Topologia de hardware

1. **HUB:** ESP32-S3 (placa dedicada)
   - Fusão de evidências
   - Veto Engine
   - Roteamento de alertas silenciosos
   - Gerenciamento da HMI Nextion (controle e visualização de estado)
   - Acionamento de áudio como exceção crítica
   - Registro local append-only

2. **Nó de contato wearable:** XIAO ESP32-C3
   - `AD8232` (ECG)
   - `MAX30102` (PPG/SpO₂)
   - `MPU6050` (IMU)

3. **Nó ambiental:** ESP32-S3
   - `mmWave` (respiração + dados de movimento no ambiente/paciente)
   - `MLX90640` (gradientes térmicos e tendência hemodinâmica)

## Comunicação

- Primária: ESP-NOW entre nós.
- Secundária: serial para debug e captura de logs de bancada.

## HMI

- **Nextion Intelligent Series** no HUB como interface principal de controle e output visual, equivalente funcional ao monitor atual, com filosofia silent-first.
- Estados mínimos exibidos: `CALM`, `CONFLICT`, `VALIDATED_EVENT`, `DEGRADED`, `CRITICAL_AUDIO`.
- Exibir sempre: estado atual, motivo da decisão, sensores de suporte/conflito, nível de confiança e canal de notificação acionado.

### Conteúdo clínico visual obrigatório (MVP)

- Numéricos: `SpO₂ (%)` e `Heart Rate (bpm)`.
- Curvas: `PPG plethysmography` e `ECG waveform`.
- Índice de agitação do paciente (`0-100`) baseado em fusão `IMU + mmWave`.
- Mapa térmico corporal por zonas com dados processados (sem envio de frame bruto da câmera).

### Zonas térmicas corporais (MVP)

- `head`
- `upper_limbs_proximal`
- `upper_limbs_distal`
- `thorax`
- `abdomen`
- `lower_limbs_proximal`
- `lower_limbs_distal`

### Política de atualização de dados na HMI

- `ECG waveform`: alta prioridade e atualização contínua.
- `PPG waveform`: alta prioridade e atualização contínua.
- Numéricos (`HR`, `SpO₂`): atualização periódica rápida.
- Índice de agitação: atualização periódica intermediária.
- Painel térmico zonal: atualização lenta por tendência, padrão `60s`.

### Interface HUB <-> Nextion (requisito MVP)

- Canal: UART dedicado.
- Modelo de dados: mensagens curtas orientadas a estado (ex.: `state`, `reason_code`, `confidence`, `latency_ms`).
- Comandos de entrada da HMI (mínimo): `ack_event`, `mute_request`, `page_change`, `tech_check_request`.
- Comandos de saída do HUB (mínimo): `render_state`, `render_reason`, `render_priority`, `render_connectivity`.
- Regra de segurança: interface visual nunca suprime decisão crítica; apenas confirma ciência operacional.

### Limitações técnicas e mitigação (HMI)

- Limitação: renderização de mapa térmico por pixel em Nextion pode degradar desempenho e estabilidade.
   - Mitigação: transmitir apenas temperaturas por zona e indicadores derivados.
- Limitação: concorrência de banda UART entre curvas e painéis auxiliares.
   - Mitigação: priorização de `ECG/PPG` e atualização térmica desacoplada em baixa frequência.
- Limitação: interpretação térmica isolada pode induzir leitura clínica indevida.
   - Mitigação: tratar térmica como evidência contextual complementar no Veto Engine.

---

## 4) Papel clínico-técnico dos sensores

- **ECG (AD8232):** alta autoridade para ritmo cardíaco e confirmação elétrica.
- **PPG (MAX30102):** complemento cardiovascular (FC/SpO₂), suscetível a artefatos de movimento.
- **IMU (MPU6050):** contexto cinemático local do wearable (agitação, handling, deslocamento).
- **mmWave:** dupla função no MVP:
  - detecção de padrão respiratório/micro-movimento torácico;
  - captação de movimento como evidência contextual independente em apoio ao IMU.
- **MLX90640:** evidência térmica complementar para gradiente core-periferia e tendência de instabilidade hemodinâmica.

### Regra de autoridade no MVP

- Nenhum sensor isolado define evento crítico de forma definitiva.
- Eventos críticos exigem convergência multimodal e qualidade mínima.
- MLX90640 e mmWave podem elevar prioridade de investigação, mas com gates de qualidade.

---

## 5) Contrato de dados (schema lógico v0.1)

## Evidence (unidade mínima de inferência)

Campos obrigatórios:

- `event_id` (uuid)
- `timestamp_ms` (epoch)
- `node_id` (`wearable_contact`, `environmental`, `hub`)
- `sensor_type` (`ecg`, `ppg`, `imu`, `mmwave`, `thermal`)
- `signal_type` (`electrical`, `optical`, `mechanical`, `thermal`)
- `value` (numérico ou objeto simples)
- `quality_score` (0.0-1.0)
- `confidence_score` (0.0-1.0)
- `context_tags` (lista; ex.: `movement_high`, `lead_off`, `occlusion`, `stable_rest`)

## EventCandidate

- `candidate_type` (ex.: `tachy_suspect`, `desat_suspect`, `apnea_suspect`, `shock_pattern_suspect`)
- `supporting_evidence_ids` (lista)
- `conflicting_evidence_ids` (lista)
- `temporal_window_ms`
- `candidate_score` (0.0-1.0)

## DecisionRecord (Black Box)

- `decision_id`
- `candidate_id`
- `decision` (`promote`, `veto`, `hold`, `degraded_mode`)
- `reason_code` (ex.: `movement_artifact`, `lead_disconnected`, `multimodal_convergence`, `insufficient_quality`)
- `explanation_text` (curto e legível para humano)
- `notified_channels` (`hmi`, `wearable_haptic`, `audio`)
- `latency_ms`

---

## 6) Veto Engine v1 (determinístico e explicável)

## Princípios

- Segurança por consenso, não por gatilho isolado.
- Supressão explícita de conflitos com justificativa.
- Escalonamento sonoro apenas em criticidade validada ou falha sistêmica.

## Regras-base

1. **Promoção de evento crítico**
   - Exigir pelo menos 2 fontes independentes coerentes.
   - Exigir `quality_score` e `confidence_score` acima dos limiares mínimos por sensor.

2. **Veto por artefato de movimento**
   - Exemplo: PPG alterado + IMU alto movimento + mmWave indicando movimento não compatível com piora fisiológica primária.

3. **Veto técnico**
   - Exemplo: `lead_off` do ECG ativo em cenário de suposta assistolia.

4. **Hold (incerteza)**
   - Sem convergência suficiente: manter monitoramento, notificar silenciosamente e registrar conflito.

5. **Escalonamento de áudio (exceção)**
   - Criticidade alta + convergência robusta,
   - ou perda de observabilidade relevante (degradação sistêmica).

---

## 7) Estados operacionais do sistema

- `CALM`: sem eventos relevantes, sinais consistentes.
- `CONFLICT`: inconsistência entre fontes, possível artefato.
- `VALIDATED_EVENT`: evento confirmado multimodalmente.
- `DEGRADED`: perda parcial de sensores/comunicação; monitoramento reduzido com transparência.
- `CRITICAL_AUDIO`: exceção sonora habilitada por regra de segurança.

### Mapeamento visual na Nextion (MVP)

- Cada estado deve ter tela dedicada e inequívoca.
- Toda mudança de estado deve registrar timestamp e razão no Black Box.
- Transições `CONFLICT -> CALM` e `VALIDATED_EVENT -> CALM` exigem atualização explícita de resolução.

---

## 8) Cenários de validação (MVP)

1. **Artefato por agitação**
   - Esperado: veto com razão `movement_artifact`.

2. **Desconexão de ECG**
   - Esperado: veto com razão `lead_disconnected` e alerta técnico silencioso.

3. **Taquicardia real em repouso**
   - Esperado: promoção por convergência ECG+PPG com baixo movimento IMU/mmWave.

4. **Apneia simulada com dessaturação**
   - Esperado: promoção crítica com possibilidade de `CRITICAL_AUDIO`.

5. **Padrão térmico de alerta hemodinâmico**
   - Esperado: `hold` ou alerta de reavaliação com razão explícita, sem diagnóstico automático.

6. **Falha de nó/sensor**
   - Esperado: entrada em `DEGRADED` com rastreabilidade e limites operacionais claros.

---

## 9) Métricas de avaliação

- Taxa de falso positivo por cenário.
- Sensibilidade em eventos críticos simulados.
- Latência mediana e p95 por tipo de decisão.
- Taxa de eventos com explicação registrada.
- Disponibilidade da comunicação entre nós.
- Integridade de renderização HMI (campos obrigatórios e curvas sem perda perceptível).
- Confiabilidade da atualização térmica zonal no ciclo de `60s`.

---

## 10) Riscos e mitigação

1. **Ruído no ECG em wearable compacto**
   - Mitigação: layout, aterramento, cabos curtos, filtro digital, eventual ADC externo.

2. **Variação térmica ambiental (MLX90640)**
   - Mitigação: janela de calibração, controle de distância/FOV, gate de qualidade térmica.

3. **Conflitos de movimento (IMU vs mmWave)**
   - Mitigação: regras de contexto temporal e score de coerência cruzada.

4. **Sincronização temporal entre nós**
   - Mitigação: sincronização periódica e janelas de fusão fixas.

5. **Complexidade excessiva no MVP**
   - Mitigação: regras simples, explicáveis, com evolução incremental.

---

## 11) Cronograma sugerido (8 semanas)

- **S1-S2:** schema de dados, logger append-only, testes de comunicação.
- **S3-S4:** integração dos nós (contato + ambiental) e aquisição estável.
- **S5:** implementação Veto Engine v1 + códigos de razão.
- **S6:** integração HMI silenciosa e canais de notificação.
- **S7:** protocolo de validação com baseline threshold-only.
- **S8:** consolidação de métricas, demonstração e relatório de candidatura a laboratório.

---

## 12) Entregáveis do MVP

1. Protótipo com 3 nós operacionais.
2. Pipeline AGNES funcional ponta-a-ponta.
3. Integração HUB-Nextion com estados, razões e comandos mínimos de operação.
4. Black Box local em JSONL.
5. Demonstração de cenários com resultados mensuráveis.
6. Relatório técnico com limitações, riscos e próximos passos.

---

## 13) Critérios de aceite do ciclo MVP

- Comunicação entre nós estável durante sessão de teste.
- Veto Engine toma decisões reproduzíveis para os cenários definidos.
- Logs permitem reconstrução completa do raciocínio de decisão.
- Demonstração evidencia redução de ruído de alarmes sem perda de eventos críticos simulados.
- Nextion exibe corretamente estados e razões em todos os cenários definidos.
- Material técnico apto para submissão/apresentação em laboratório acadêmico ou industrial.

---

## 14) Próxima evolução (após MVP)

- Refinar pesos/limiares com dados reais supervisionados.
- Incorporar modelo probabilístico leve para ranking de hipóteses.
- Melhorar miniaturização e segurança elétrica para uso prolongado.
- Expandir integração documental e trilhas para validação regulatória futura.
