# 🧬 MANUAL DE SISTEMAS AETHELGARD — PARTE 3
**MHD · QCD · Regime · PreCognition · Nexus Observer · Fluxo**

---

## 12. MHD — MAGNETOHYDRODYNAMICS (Z-Pinch)

| Campo | Valor |
|-------|-------|
| **C++** | `src/mhd/mhd_engine.cpp` (113 linhas) |
| **Python** | `plasma_market.py` (145 linhas) |
| **Teoria** | Relação de Bennett + Z-Pinch + Forças de Lorentz |
| **Objetivo** | Detectar Stop Hunts institucionais como compressão de plasma magnético |

### O Que Faz
Modela zonas de liquidez (topos/fundos) como **membranas de plasma**. Quando o preço entra na zona, a "corrente institucional" (volume × momentum) comprime o plasma. Se a Pressão Magnética `B²/2μ` vence a Pressão Térmica `nkT`, ocorre **Z-Pinch** (colapso do plasma → reversão violenta).

### Como Calcula (C++)
1. **Corrente J:** `|Δprice| × (volume / volume_ema)` com suavização `0.7 × J_old + 0.3 × J_new`
2. **Força de Lorentz:** `F_L = μ₀ × J²`
3. **Raio do Plasma:** `dr = (P - F_L) × 0.01`. Clampado [0.01, 2.0]
4. **Pressão (Bennett):** `P = density × (1/radius)^(2γ)` com cap 500.0 e log-scaling
5. **Z-Index Contínuo:** `min(80, -ln(radius) × 25)` se comprimido. +20 se detonação (P↑↑, J↓)
6. **Thresholds Adaptativos:** Via EMAs de pressão e corrente (não constantes mágicas)

### Scanner Python
- Identifica zonas via Kernel de densidade ATR sobre os últimos 150 pavios
- Máquina de estado: NEUTRAL → TOP_SWEEP/BOTTOM_SWEEP → reset ao sair

### Visual MT5
Telemetria HUD: `Magnetic Pull: X.XX mT`. Z-Index history. Sem renderização gráfica direta (informação para o SL dinâmico).

---

## 13. QCD — QUANTUM CHROMODYNAMICS (Fissão)

| Campo | Valor |
|-------|-------|
| **C++** | Lógica pura Python (sem engine C++) |
| **Python** | `market_qcd.py` (99 linhas) |
| **Teoria** | Força Forte (Confinamento + Liberdade Assintótica) |
| **Objetivo** | Detectar "explosões" direcionais quando a energia rompe o confinamento |

### O Que Faz
Modela o preço como partícula confinada por uma "corda de liquidez" (VWAP). A força de confinamento **aumenta** com a distância (como a Força Forte nuclear). Quando a energia cinética ultrapassa o threshold → **Fissão** (rompimento explosivo).

### Como Calcula
1. **Cargas de Cor:** `RED` = vendedores × volume, `GREEN` = compradores × volume, `BLUE` = pavios × volume. Normalizado
2. **Força de Confinamento:** `F = k × r` onde `k = std(close)` e `r = |price - VWAP|`
3. **Energia Cinética:** `E = body_atual / mean(bodies_filtrados)`
4. **Fissão:** Se `E > 2.0` E `body_ratio > 0.70` (corpo > 70% da vela) → Fissão

### Sinais — ⚡ OS "SHORTS" QUE VOCÊ GOSTOU
| Sinal | Condição |
|-------|----------|
| `FISSION_EXPANSION_UP` | E > 2.0 + body_ratio > 70% + close > open |
| `FISSION_EXPANSION_DOWN` | E > 2.0 + body_ratio > 70% + close < open |
| `CONFINED_E(X.XX)` | Energia insuficiente para rompimento |

> [!IMPORTANT]
> **Este é o sistema que gera os sinais SHORT/LONG no gráfico.** Ele detecta velas institucionais massivas (corpo > 2x a média E > 70% do range total) — são os movimentos de "canhão" do mercado.

### Visual MT5
Tags TradingView-style: `SHORT 78344.89` em vermelho ou setas teal para Bull. Renderizado via `CreateTradingViewTag()`.

---

## 14. REGIME ENGINE — SOBERANIA DE FLUXO

| Campo | Valor |
|-------|-------|
| **Arquivo** | `quantum_indicators.py` (474 linhas) |
| **Teoria** | Flow Sovereignty (5 camadas EMA + ATR + Pivôs) |
| **Objetivo** | Determinar o regime macro: BULL TSUNAMI / BEAR TSUNAMI / NEUTRAL |

### O Que Faz
O coração decisório da máquina. Usa 5 camadas de EMA (9, 21, 34, 89, 200), ATR, pivôs estruturais e lógica de histerese para classificar o regime macro com **imunidade de 10 velas** contra colapsos triviais.

### Camadas de Decisão
1. **EMAs:** Fast(9), Mid(21), Trend(34), Macro(89), Gravity(200)
2. **Ignição Atômica:** Body > 1.1× ATR + rompimento de high/low de 10 barras
3. **Singularidade Atômica (ARS):** Reversão imediata em extremos absolutos de 120 barras
4. **Exaustão por Sombra:** Pavio > 2× body em topo/fundo local (red em topo, green em fundo)
5. **Momentum Lock:** Regime só colapsa se EMA 9/21 virou contra
6. **Noise Gate:** Saída do neutro exige spread EMA > 0.5× ATR
7. **Imunidade Maturada:** 10 velas de proteção (conf < 110)

### Regime Boxes
- `1` = **TSUNAMI_BULL** — Caixas com borda Teal `(38,166,154)`
- `2` = **TSUNAMI_BEAR** — Caixas com borda Red `(239,83,80)`
- `0` = **SCANNING** — Sem caixa

### Tactical Dots
Mini-triângulos coloridos que indicam a "saúde" do regime em cada vela. Gerados via `calculate_tactical_dots()`.

---

## 15. PRECOGNITION — MOTOR DE VISÃO DE FUTURO

| Campo | Valor |
|-------|-------|
| **Arquivo** | `quantum_projection.py` (62 linhas) |
| **Dependências** | QRW Engine C++ + MHD PlasmaMarket |
| **Objetivo** | Calcular Stop Loss de Singularidade via projeção estocástica |

### O Que Faz
Combina as zonas de plasma (MHD) com simulações Monte Carlo (QRW C++) para projetar 500 caminhos futuros e determinar onde o preço provavelmente colapsa.

### Como Calcula
1. Obtém zonas de plasma atuais (top_level, bottom_level) via MHD
2. Executa `simulate_future_collapse()` no C++ (OpenMP, 500 paths, 40 steps)
3. Calcula `sl_bull = percentil(5%)` e `sl_bear = percentil(95%)` dos breach levels

### Retorno
- `sl_bull_singular` — SL para posições de compra
- `sl_bear_singular` — SL para posições de venda
- `breach_prob` — Probabilidade de ruptura

---

## 16. YIELD GOVERNOR — ESCUDO TOPOLÓGICO

| Campo | Valor |
|-------|-------|
| **Arquivo** | `yield_governor.py` (109 linhas) |
| **Dependência** | CYT Engine C++ |
| **Objetivo** | Monitorar saúde topológica e detectar Bull/Bear Traps |

### Funções
- **`monitor_topology`** — Calcula deformação e ativa escudo se `avg_deformation > threshold`
- **`analyze_historical_danger`** — Gera mapa completo de danger zones históricas
- **`detect_topological_trap`** — Divergência entre price_slope e determinant_slope
  - Preço↑ + Determinante↓ = `BULL_TRAP`
  - Preço↓ + Determinante↑ = `BEAR_TRAP`
- **`evaluate_dimensional_collapse`** — Verifica se a malha colapsou (invalidando a tese)

---

## 17. NEXUS OBSERVER — DASHBOARD HFT (MQL5)

| Campo | Valor |
|-------|-------|
| **Arquivo** | `Code/MQL5/Nexus_Observer.mq5` (~1012 linhas) |
| **Comunicação** | Raw TCP Socket (porta dinâmica) |
| **Função** | Renderização visual + Execução de ordens + HUD |

### Componentes Visuais
| Componente | Tipo de Objeto | Cor |
|------------|---------------|-----|
| Regime Boxes | `OBJ_RECTANGLE` | Teal/Red TV palette |
| LBM Dots | `OBJ_ARROW` (Wingdings 159) | Teal/Red/Amber |
| RHT Sparks | `OBJ_ARROW` (Wingdings 233/234) | Teal/Red |
| CYT Danger | `OBJ_RECTANGLE` | Dark Red ultra-sutil |
| QGC Gravity | Retângulos evaporação | Dark Red |
| QCD Tags | `CreateTradingViewTag()` | Teal/Red com preço |
| Schrödinger Heatmap | `OBJ_TREND` horizontal | Crimson/Teal gradual |
| QHO Shells | `OBJ_TREND` horizontal | Dotted lines |
| HUD Panel | `OBJ_RECTANGLE_LABEL` + `OBJ_LABEL` | Ebony Stealth |

### HUD Panel (Telemetria)
```
AETHELGARD :: QUANTUM CORE
─────────────────────────
Regime          Bull Tsunami
Confidence      87%
RHT Heat        BHT_LAMINAR
R-H Flesh       LAMINAR
LBM Fluid       Laminar Flow
AdS/CFT Bulk    PLASMA_BULL
QRW Hike        Anti-phase/ON
S-Matrix Amp    S-MaT:e3.1
Ricci Flow/AdS  1.2978 sigma
Vol. Avg        80317.83
MSNR Fidelity   0.9990
Dim. Coherence  0.038
Magnetic Pull   10.00 mT
Tunnel Exit P   100.0%
Q-Cloud Density 0.00
S-Cloud Analysis HOLD_FOR_TUNNELING
Energy Level (n) 23
QHO State       CRITICAL_EXHAUSTION
```

---

## 18. FLUXO DE DADOS COMPLETO

```
MT5 (Preço/Volume)
  ↓
q_math_node.py (Coleta + 7 Threads de Física C++)
  ↓ ZMQ PUB
Aethelgard_Swarm.py (N-Core: Regime + Decisão)
  ↓ consulta ZMQ REQ
q_math_node.py (Q-Math: retorna q_state com todos os motores)
  ↓
Aethelgard_Swarm.py (Monta nexus_data_str com ~40 campos)
  ↓ TCP Socket
Nexus_Observer.mq5 (ParseAndDraw: Renderiza tudo + Executa ordens)
```

### Campos da nexus_data_str (separados por `;`)
```
0: unused
1: unused
2: status_final (ex: "TSUNAMI_BULL | CONF: 87%")
3: unused
4: regimes_cache (CSV de "score|conf")
5: inst_avg (preço médio)
6: health (0.0-1.0)
7: signals_cache
8: dots_cache
9: inst_avg (duplicado)
10: cloud_str (Schrödinger heatmap)
11: lbm_signal
12: z_pinch_signal
13: rmt_signal
14: qrw_signal
15: lbm_cache (CSV)
16: ricci_curvature
17: h_entropy
18: cyt_danger_cache (CSV)
19: sec_str (singularity metrics)
20: sec_cache (CSV)
21: rht_status
22: is_collapsed
23: qcd_signal
24: qcd_cache (CSV)
25: qgc_data_str (gravity zones)
26: wyckoff_str (disabled)
27: qrw_history
28: rht_history
29: rht_flash
30: rht_flash_history
31: qdd_fidelity
32: qte_prob
33: qte_advice
34: qho_n
35: qho_stability
36: qho_status
37: qho_shells
38: mhd_strength
39: msnr_telemetry
40: msnr_cache (CSV)
```

---

> [!NOTE]
> **Sobre os Sinais SHORT:** Eles vêm do módulo **QCD (Quantum Chromodynamics)** — `market_qcd.py`. A lógica `detect_fission()` identifica velas institucionais com corpo > 2× a média e > 70% do range total. Esses são os sinais mais puros da máquina: detectam movimentos de canhão institucional sem ruído.
