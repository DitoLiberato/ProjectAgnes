# AGNES Node-HUB Message Schema v0.1

## 1. Objetivo

Definir um contrato mínimo, estável e rastreável para troca de mensagens entre:

- Nó de contato (XIAO ESP32-C3)
- Nó ambiental (ESP32-S3)
- HUB (ESP32-S3)

Este schema permite:

- integrar hello world de sensores sem retrabalho estrutural;
- padronizar coleta, validação e logging;
- alimentar o Veto Engine de forma consistente.

---

## 2. Princípios do protocolo

- Simples para MVP.
- Determinístico e auditável.
- Tolerante a perda de pacote.
- Extensível sem quebrar compatibilidade.

---

## 3. Modelo de transporte (MVP)

- Transporte primário: ESP-NOW.
- Carga útil: JSON UTF-8 compacto.
- Mensagem por pacote: 1 objeto JSON.
- Controle de versão: campo obrigatório `schema_version`.

> Nota: quando o payload ultrapassar limite de pacote no ESP-NOW, enviar apenas valores derivados/resumidos no nó e manter sinal bruto local para debug serial.

---

## 4. Envelope comum (obrigatório)

Todos os tipos de mensagem devem conter:

- `schema_version` (string) — ex.: `"0.1"`
- `msg_type` (string) — ex.: `"heartbeat"`, `"evidence"`
- `msg_id` (string) — UUID ou ID único monotônico por nó
- `ts_ms` (number) — epoch em milissegundos
- `node_id` (string) — `contact_node`, `env_node`, `hub`
- `seq` (number) — contador sequencial por nó

Exemplo de envelope:

```json
{
  "schema_version": "0.1",
  "msg_type": "heartbeat",
  "msg_id": "contact_node-1700000000123-1024",
  "ts_ms": 1700000000123,
  "node_id": "contact_node",
  "seq": 1024
}
```

---

## 5. Tipos de mensagem

## 5.1 HEARTBEAT

Uso: saúde do nó e conectividade.

Campos adicionais:

- `uptime_ms` (number)
- `rssi_dbm` (number)
- `battery_pct` (number, opcional)
- `firmware_version` (string)
- `sensor_status` (object)

Exemplo:

```json
{
  "schema_version": "0.1",
  "msg_type": "heartbeat",
  "msg_id": "env_node-1700000001123-2048",
  "ts_ms": 1700000001123,
  "node_id": "env_node",
  "seq": 2048,
  "uptime_ms": 530001,
  "rssi_dbm": -62,
  "firmware_version": "env-0.1.0",
  "sensor_status": {
    "mmwave": "ok",
    "thermal": "ok"
  }
}
```

## 5.2 EVIDENCE

Uso: dado processado por sensor/fusão local.

Campos adicionais:

- `sensor_type` (`ecg`, `ppg`, `imu`, `mmwave`, `thermal`)
- `signal_type` (`electrical`, `optical`, `mechanical`, `thermal`)
- `value` (number ou object)
- `quality_score` (0.0-1.0)
- `confidence_score` (0.0-1.0)
- `context_tags` (array de strings)

Exemplos:

ECG/PPG numérico:

```json
{
  "schema_version": "0.1",
  "msg_type": "evidence",
  "msg_id": "contact_node-1700000002123-2049",
  "ts_ms": 1700000002123,
  "node_id": "contact_node",
  "seq": 2049,
  "sensor_type": "ppg",
  "signal_type": "optical",
  "value": {
    "hr_bpm": 132,
    "spo2_pct": 96
  },
  "quality_score": 0.89,
  "confidence_score": 0.84,
  "context_tags": ["stable_rest"]
}
```

Movimento (IMU/mmWave):

```json
{
  "schema_version": "0.1",
  "msg_type": "evidence",
  "msg_id": "env_node-1700000003123-2050",
  "ts_ms": 1700000003123,
  "node_id": "env_node",
  "seq": 2050,
  "sensor_type": "mmwave",
  "signal_type": "mechanical",
  "value": {
    "resp_rate_bpm": 28,
    "motion_index": 42
  },
  "quality_score": 0.91,
  "confidence_score": 0.86,
  "context_tags": ["resp_detected", "movement_moderate"]
}
```

Térmico zonal:

```json
{
  "schema_version": "0.1",
  "msg_type": "evidence",
  "msg_id": "env_node-1700000060123-2060",
  "ts_ms": 1700000060123,
  "node_id": "env_node",
  "seq": 2060,
  "sensor_type": "thermal",
  "signal_type": "thermal",
  "value": {
    "zones_c": {
      "head": 35.2,
      "upper_limbs_proximal": 34.1,
      "upper_limbs_distal": 32.6,
      "thorax": 36.0,
      "abdomen": 35.8,
      "lower_limbs_proximal": 33.7,
      "lower_limbs_distal": 31.9
    },
    "core_periphery_delta_c": 3.4,
    "thermal_trend": "falling"
  },
  "quality_score": 0.78,
  "confidence_score": 0.74,
  "context_tags": ["thermal_update_60s"]
}
```

## 5.3 EVENT_CANDIDATE

Uso: opcional no MVP inicial; pode ser gerado apenas no HUB.

Campos adicionais:

- `candidate_type`
- `candidate_score`
- `supporting_evidence_ids` (array)
- `conflicting_evidence_ids` (array)
- `temporal_window_ms`

## 5.4 COMMAND

Uso: comando do HUB para nó.

Campos adicionais:

- `command` (ex.: `set_rate`, `self_test`, `sync_time`)
- `params` (object)

## 5.5 ACK

Uso: confirmação de recebimento de comando.

Campos adicionais:

- `ack_for_msg_id`
- `status` (`ok`, `error`)
- `error_code` (opcional)

## 5.6 ERROR

Uso: telemetria de falha.

Campos adicionais:

- `error_code`
- `error_text`
- `severity` (`info`, `warning`, `critical`)

---

## 6. Cadência recomendada (MVP)

- `heartbeat`: 1 a cada 2 s
- `evidence` ECG/PPG/IMU/mmWave: 2 a 10 Hz para valores derivados
- `evidence` térmico zonal: 1 a cada 60 s

> Observação: curvas completas de ECG/PPG para tela podem usar canal dedicado de stream resumido no HUB, sem aumentar carga de telemetria entre nós.

---

## 7. Regras de robustez

- Rejeitar mensagem sem `schema_version`.
- Rejeitar `quality_score`/`confidence_score` fora de 0.0-1.0.
- Se `seq` regressivo, marcar possível reset de nó.
- Persistir no Black Box toda falha de parsing com `reason_code = invalid_payload`.

---

## 8. Compatibilidade e evolução

- Mudanças incompatíveis exigem incremento de versão maior (`0.x` -> `1.0`).
- Campos novos devem ser opcionais inicialmente.
- HUB deve ignorar campos desconhecidos sem falhar.

---

## 9. Checklist de implementação (fase hello world)

1. Cada nó envia `heartbeat` válido.
2. Cada sensor envia pelo menos 1 `evidence` válido.
3. HUB valida envelope e imprime resumo serial.
4. HUB grava JSONL bruto recebido para auditoria.
5. Só após isso iniciar regras de Veto Engine.
