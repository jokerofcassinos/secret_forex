# 🎯 MANUAL DE SISTEMAS AETHELGARD — PARTE 4
**Quantum Setup Engine · Adaptive Neural Zones (ANZ) · Gestão de Risco Quântica**

---

## 19. QUANTUM SETUP ENGINE v2.0 — VISÃO GERAL

| Campo | Valor |
|-------|-------|
| **Arquivo** | `Code/N_Core/quantum_setups.py` (576 linhas) |
| **Classe** | `QuantumSetupEngine` |
| **Teoria** | Fusão multi-setup híbrido (Swing + Scalp Dimensional) |
| **Objetivo** | Identificar 7 padrões de execução quântica a cada tick |

### O Que Faz
O **Quantum Setup Engine** é o cérebro de tomada de decisão da Singularidade. Ele avalia 7 configurações de entrada (setups) a cada tick do mercado, cruzando **todos** os motores de física C++ simultaneamente. Cada setup possui condições específicas e requer um número mínimo de "confirmações quânticas" de diferentes subsistemas.

### Modos de Operação
| Modo | Descrição | Dados Disponíveis |
|------|-----------|-------------------|
| **LIVE** | Tempo real, todas as engines ativas | RHT, RMT, QRW, QGC, QTE, QDD, MHD, KSI, CYT |
| **BACKFILL** | Reconstrução histórica no boot | Apenas Regime, LBM, QCD, QHO, Ricci. Condições relaxadas |

### Sistema de Cooldown Anti-Spam
Cada setup possui um cooldown em barras após ser disparado, impedindo repetições:

| Setup | Cooldown (barras) |
|-------|-------------------|
| S1 Estilingue | 15 |
| S2 Aniquilação | 15 |
| S3 Bosônico | 15 |
| S4 Harmônico | 20 |
| S5 Colapso | 30 |
| S6 Tunelamento | 15 |
| S7 Tsunami | 40 |

### Telemetria de Saída
Formato: `S3_BOSONIC_IGNITION:LONG:C3|S7_TSUNAMI_MACRO:LONG:C3`
Enviado via campo `parts[39]` da `nexus_data_str` para o `Nexus_Observer.mq5`.

---

## 20. SETUP S1 — ESTILINGUE GRAVITACIONAL 🏹

| Campo | Valor |
|-------|-------|
| **ID** | `S1_GRAVITATIONAL_SLINGSHOT` |
| **Tipo** | Reversão pós-Stop-Hunt |
| **Modo** | 🔴 LIVE ONLY (requer MHD Z-Pinch) |
| **Cor HUD** | `RGB(255, 165, 0)` — Laranja |

### Tese Física
Instituições executam Stop Hunts deliberados ("Varreduras de Liquidez"). O MHD detecta a compressão do plasma magnético. Quando o plasma colapsa (Z-Pinch), o preço é arremessado na direção oposta como um estilingue.

### Condições de Disparo
1. `Z_PINCH_PLASMA` ativo no MHD (compressão extrema detectada)
2. `QGC Pull ≥ 2.0` (gravidade gravitacional institucional forte)
3. `QHO n ≥ 4` (energia acumulada no sistema harmônico)
4. **Direção:** Oposta ao sweep. TOP_SWEEP → SHORT, BOTTOM_SWEEP → LONG
5. **Mínimo 1 confirmação** entre:
   - RHT Flash alinhado com a reversão
   - LBM Rupture na direção de reversão

### Confiança
`confirms + 1` (mínimo 2, máximo 3)

---

## 21. SETUP S2 — ANIQUILAÇÃO DE VÁCUO 💥

| Campo | Valor |
|-------|-------|
| **ID** | `S2_VACUUM_ANNIHILATION` |
| **Tipo** | FVG Fill + Mudança de Regime |
| **Modo** | ✅ LIVE + BACKFILL |
| **Cor HUD** | `RGB(255, 50, 50)` — Vermelho |

### Tese Física
Gaps de preço (FVGs) são **Vácuos de Antimatéria**. Quando o regime muda e a topologia está estressada, o vácuo é "aniquilado" — o preço preenche o gap com violência.

### Condições de Disparo
1. **QCD Fissão** ativa (`FISSION_EXPANSION_UP` ou `DOWN`) — obrigatório
2. **Ricci ≥ 1.0** — topologia estressada
3. **Regime em transição** — `prev_regime ≠ regime` e `regime ≠ 0`
4. **[LIVE]** S-Matrix `singularity_strength ≥ 0.08` + `|QDD| ≥ 0.4`

### Confiança
Backfill: 2 | Live: 3

---

## 22. SETUP S3 — CONDENSADO BOSÔNICO IGNIÇÃO 🔥

| Campo | Valor |
|-------|-------|
| **ID** | `S3_BOSONIC_IGNITION` |
| **Tipo** | Breakout pós-Squeeze |
| **Modo** | ✅ LIVE + BACKFILL |
| **Cor HUD** | `RGB(255, 215, 0)` — Ouro |

### Tese Física
O mercado entra em **Superfluidez** (Condensado Bosônico) quando volume explode e volatilidade desaba. Após N barras de compressão, uma Fissão QCD detona o breakout.

### Condições de Disparo
1. **Squeeze LBM** por N barras consecutivas:
   - Live: `≥ 5 barras` | Backfill: `≥ 3 barras`
2. **QCD Fissão** no exato momento da saída do squeeze
3. **[LIVE] Mínimo 2 confirmações** entre:
   - RHT Flash alinhado
   - QRW Skew alinhado
   - RMT Pure Signal ativo
4. **[BACKFILL]** Squeeze + Fissão basta (0 confirmações)

### State Tracking
`self.squeeze_bar_count` — Contagem interna de barras em squeeze. Resetado ao sair.

### Confiança
`max(1, confirms)` — 1 a 3

---

## 23. SETUP S4 — RESSONÂNCIA HARMÔNICA 🌊

| Campo | Valor |
|-------|-------|
| **ID** | `S4_HARMONIC_RESONANCE` |
| **Tipo** | Pullback Entry na Tendência |
| **Modo** | ✅ LIVE + BACKFILL |
| **Cor HUD** | `RGB(0, 255, 180)` — Verde Neon |

### Tese Física
Em regime TSUNAMI forte, o preço recua para um **shell de energia intermediário** (QHO n=2 ou n=3). É o pullback institucional. A gravidade (QGC) confirma que há massa segurando.

### Condições de Disparo
1. **Regime TSUNAMI** ativo (`regime ≠ 0`) com `conf ≥ 80`
2. **QHO n = 2 ou 3** (preço no shell harmônico intermediário)
3. **LBM** compatível: Rupture alinhado, Laminar, ou Squeeze
4. **[LIVE]** `QGC Pull ≥ 1.5` + `QDD fidelidade alinhada (|f| > 0.5)`
5. **[BACKFILL]** Regime + QHO shell alinhados basta

### Confiança
Backfill: 2 | Live: 2-3 (3 se `|QDD| > 0.7`)

---

## 24. SETUP S5 — COLAPSO TOPOLÓGICO ☠️

| Campo | Valor |
|-------|-------|
| **ID** | `S5_TOPOLOGICAL_COLLAPSE` |
| **Tipo** | Reversão Macro Rara (Evento de Singularidade) |
| **Modo** | ✅ LIVE + BACKFILL |
| **Cor HUD** | `RGB(255, 0, 85)` — Rosa Choque |

### Tese Física
A malha topológica do espaço-tempo do mercado (CYT) colapsa. A fidelidade dimensional (QDD) inverte o sinal. É o evento mais raro e violento: uma reversão de regime completa.

### Condições de Disparo
1. **QHO n ≥ 5** — sistema em exaustão energética crítica
2. **KSI Filter:** Coerência caótica (`< 0.4`) OU super-esticada (`> 0.90`)
3. **[LIVE]** CYT `is_collapsed = true` + QDD flip (`prev_sign ≠ curr_sign`)
4. **[BACKFILL]** `Ricci > 3.0` + LBM Rupture ou regime invertido

### State Tracking
`self.prev_qdd_sign` — Monitora a inversão de polaridade do QDD

### Confiança
Backfill: 2 | Live: 2-4 (bônus por Z-Pinch e Rupture)

---

## 25. SETUP S6 — TUNELAMENTO INSTITUCIONAL 🔮

| Campo | Valor |
|-------|-------|
| **ID** | `S6_INSTITUTIONAL_TUNNELING` |
| **Tipo** | Breakout Carry (Travessia de Barreira) |
| **Modo** | 🔴 LIVE ONLY (requer QTE + RMT) |
| **Cor HUD** | `RGB(0, 200, 255)` — Azul Claro |

### Tese Física
O efeito de **Tunelamento Quântico** — o preço atravessa uma barreira de liquidez "impossível". O QTE confirma probabilidade > 80% de travessia. O RMT filtra o sinal puro do ruído.

### Condições de Disparo
1. **QTE Prob ≥ 0.80** — alta probabilidade de tunelamento
2. **RMT Pure Signal** ativo — sinal institucional limpo (Marchenko-Pastur)
3. **QCD Fissão** ativa — energia direcional confirmada
4. QRW Skew adiciona confiança se alinhado

### Confiança
2 (sem QRW) | 3 (com QRW alinhado)

---

## 26. SETUP S7 — ONDA TSUNAMI MACRO 🌊🌊

| Campo | Valor |
|-------|-------|
| **ID** | `S7_TSUNAMI_MACRO` |
| **Tipo** | Position Trade de Semanas |
| **Modo** | ✅ LIVE + BACKFILL |
| **Cor HUD** | `RGB(0, 255, 255)` — Ciano |

### Tese Física
O setup mais poderoso e raro. Todos os sistemas convergem para o mesmo vetor direcional por barras consecutivas. É o equivalente a uma onda tsunami institucional de semanas.

### Condições de Disparo (LIVE)
1. **Regime TSUNAMI** com `conf ≥ 100`
2. **KSI ≥ 0.5** — coerência macro alta
3. **RHT Heat Streak ≥ 10** barras consecutivas na mesma direção
4. **QDD Streak ≥ 5** barras com fidelidade > 0.6 na mesma direção
5. **Ricci ≤ 1.5** — topologia estável
6. **QHO n ≤ 2** — sistema com energia baixa (calmo, sem exaustão)

### Condições de Disparo (BACKFILL)
1. **Regime TSUNAMI** com `conf ≥ 100`
2. **Regime Streak ≥ 8** barras consecutivas na mesma direção
3. **Ricci ≤ 1.5** + **QHO n ≤ 2**

### State Tracking
`rht_heat_streak`, `qdd_streak`, `qrw_streak`, `regime_streak`, `prev_regime_dir`

### Confiança
Backfill: `1 + (regime_streak // 8)` (max 3) | Live: `2 + (rht_streak // 10)` (max 5)

---

## 27. VISUAL DOS SETUPS NO MT5

### Sinais no Gráfico
| Elemento | Tipo | Descrição |
|----------|------|-----------|
| Diamante Atual | `OBJ_ARROW` (Wingdings 117/118) | Seta no candle ativo |
| Label do Setup | `OBJ_TEXT` | Ex: `BOSONIC`, `TSUNAMI` |
| Histórico | `OBJ_ARROW` (Wingdings 117/118) | Setas menores nos candles passados |

### Cores por Setup
| Setup | Cor | Visual |
|-------|-----|--------|
| S1 | `RGB(255, 165, 0)` | 🟠 Laranja |
| S2 | `RGB(255, 50, 50)` | 🔴 Vermelho |
| S3 | `RGB(255, 215, 0)` | 🟡 Ouro |
| S4 | `RGB(0, 255, 180)` | 🟢 Verde Neon |
| S5 | `RGB(255, 0, 85)` | 🩷 Rosa Choque |
| S6 | `RGB(0, 200, 255)` | 🔵 Azul Claro |
| S7 | `RGB(0, 255, 255)` | 🩵 Ciano |

### Histórico de Setups (Cache)
O Swarm mantém um array `setup_cache` com até 500 posições. Cada posição armazena o setup mais forte do tick como `±N` (positivo = LONG, negativo = SHORT, N = número do setup). O MQL5 lê isso via `parts[40]` e renderiza as setas históricas em cada candle.

---

> [!NOTE]
> **Hierarquia de Avaliação:** Os setups são avaliados na ordem: S3 → S4 → S1 → S6 → S7 → S2 → S5. Múltiplos setups podem disparar no mesmo tick (o `get_strongest_signal()` seleciona o de maior confiança para gestão ANZ).
