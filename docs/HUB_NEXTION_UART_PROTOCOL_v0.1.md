# AGNES HUB-Nextion UART Protocol v0.1

## 1. Objetivo

Definir o protocolo de comunicação entre HUB (ESP32-S3) e tela Nextion para:

- exibição clínica em tempo real (ECG, PPG, HR, SpO₂);
- contexto operacional (estado AGNES, razões, conectividade);
- painel térmico zonal em baixa frequência;
- ações simples do operador (ack, navegação, checagem técnica).

---

## 2. Premissas técnicas (MVP)

- Meio físico: UART dedicado HUB↔Nextion.
- Baudrate inicial recomendado: 115200 (avaliar 230400 se necessário).
- Protocolo de comando: instruções Nextion enviadas pelo HUB.
- Terminador padrão Nextion: `0xFF 0xFF 0xFF` ao final de cada comando.

---

## 3. Modelo de telas (MVP)

## 3.1 Tela principal

Campos obrigatórios:

- Numéricos: `HR`, `SpO2`
- Curva: `ECG`
- Curva: `PPG`
- Índice: `AgitationIndex (0-100)`
- Estado AGNES: `CALM | CONFLICT | VALIDATED_EVENT | DEGRADED | CRITICAL_AUDIO`
- Texto curto: `reason_code` + descrição resumida

## 3.2 Tela térmica zonal

Mostrar valores por zona:

- `head`
- `upper_limbs_proximal`
- `upper_limbs_distal`
- `thorax`
- `abdomen`
- `lower_limbs_proximal`
- `lower_limbs_distal`

Indicadores derivados:

- `core_periphery_delta_c`
- `thermal_trend` (`rising`, `stable`, `falling`)

---

## 4. Prioridade e taxa de atualização

Ordem de prioridade (do maior para o menor):

1. Estado crítico e alarmes
2. Curvas `ECG` e `PPG`
3. Numéricos `HR` e `SpO2`
4. `AgitationIndex`
5. Térmico zonal

Cadência recomendada:

- Estado/alarme: imediato por evento
- ECG: 25-50 pontos/s (amostragem exibida, não sinal cru total)
- PPG: 25-50 pontos/s
- HR/SpO2: 1 Hz
- Agitação: 2-4 Hz
- Térmico zonal: 1 atualização a cada 60 s

---

## 5. Comandos HUB -> Nextion

## 5.1 Estado AGNES

Exemplo (texto de estado):

- `state_txt.txt="CONFLICT"`
- `reason_txt.txt="movement_artifact"`

## 5.2 Numéricos vitais

- `hr_val.val=132`
- `spo2_val.val=96`

## 5.3 Curvas

Assumindo componentes waveform:

- ECG: `add ecg_wave,0,<valor_0_255>`
- PPG: `add ppg_wave,0,<valor_0_255>`

## 5.4 Índice de agitação

- `agit_val.val=42`
- `agit_bar.val=42`

## 5.5 Térmico zonal

Exemplos:

- `t_head.txt="35.2"`
- `t_thorax.txt="36.0"`
- `t_abd.txt="35.8"`
- `delta_txt.txt="3.4"`
- `trend_txt.txt="falling"`

## 5.6 Conectividade

- `link_contact.val=1`
- `link_env.val=1`
- `link_hub.val=1`

> Todo comando deve terminar com `0xFF 0xFF 0xFF`.

---

## 6. Eventos Nextion -> HUB

No MVP, eventos mínimos:

- `ack_event`
- `mute_request`
- `page_change`
- `tech_check_request`

Implementação prática:

- Cada botão Nextion envia token ASCII curto usando `prints`.
- HUB recebe token serial e traduz para comando interno.

Exemplos de tokens:

- `EVT:ACK`
- `EVT:MUTE`
- `EVT:PAGE:THERMAL`
- `EVT:TECHCHECK`

---

## 7. Regras de segurança operacional

- Nextion não decide lógica clínica; apenas apresenta e confirma ação humana.
- `mute_request` nunca cancela evento crítico validado; só silencia sinal não crítico conforme política do HUB.
- Toda ação do operador recebida via UART deve entrar no Black Box com timestamp.

---

## 8. Limitações conhecidas e mitigação

## 8.1 Gráfico térmico por imagem

Limitação:

- Nextion não é ideal para renderização de mapa térmico por pixel em alta taxa.

Mitigação:

- usar mapa corporal por zonas com números e indicador de tendência.

## 8.2 Banda UART concorrente

Limitação:

- atualizações simultâneas de curvas e muitos textos podem gerar atraso visual.

Mitigação:

- fila de prioridade no HUB;
- redução adaptativa da taxa de curvas em caso de congestionamento;
- térmico desacoplado em 60 s.

## 8.3 Coerência visual

Limitação:

- atualizações fora de ordem podem gerar inconsistência momentânea.

Mitigação:

- enviar pacote lógico em sequência fixa: estado -> numéricos -> curvas -> contexto -> térmico.

---

## 9. Exemplo de ciclo de atualização (1 segundo)

1. HUB envia estado AGNES (se houver mudança).
2. HUB envia `HR/SpO2`.
3. HUB envia lote de pontos ECG/PPG para 1 s.
4. HUB envia `AgitationIndex`.
5. A cada 60 ciclos, HUB envia atualização térmica zonal.

---

## 10. Critérios de aceite da integração UART

- Tela exibe todos os campos obrigatórios sem travamento por 30 min de teste.
- Estado AGNES muda corretamente em todos os cenários de validação.
- Curvas ECG/PPG mantêm continuidade visual adequada para MVP.
- Atualização térmica ocorre a cada 60 s com zonas corretas.
- Eventos de operador (ACK/MUTE/PAGE/TECHCHECK) são recebidos e logados pelo HUB.
