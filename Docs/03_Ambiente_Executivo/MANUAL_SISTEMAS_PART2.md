# 🧬 MANUAL DE SISTEMAS AETHELGARD — PARTE 2
**RMT · QRW · RHT · QDD · QHO · QTE**

---

## 6. RMT — RANDOM MATRIX THEORY (Filtro Espectral)

| Campo | Valor |
|-------|-------|
| **C++** | `src/rmt/rmt_engine.cpp` (127 linhas) |
| **Python** | `random_matrix.py` (93 linhas) |
| **Teoria** | Decomposição Espectral + Distribuição Marchenko-Pastur |
| **Objetivo** | Separar sinal institucional genuíno do ruído aleatório do varejo |

### O Que Faz
Constrói uma **Matriz de Covariância** 8×8 a partir de features do mercado (retornos, spreads, volume, body, pavios, entropia, LBM velocity). Extrai o **autovalor dominante** via Método da Potência e compara com o **limite teórico de Marchenko-Pastur** para determinar se existe um sinal institucional real ou se é apenas ruído estocástico.

### Features da Matriz (8 Dimensões)
1. Returns (retorno percentual)
2. Spreads (high - low)
3. Volume (tick_volume)
4. Bodies (|close - open|)
5. Upper Wicks
6. Lower Wicks
7. Volatility Entropy (ATR normalizado)
8. LBM Velocity (feedback do fluido)

### Como Calcula (C++)
1. **Normalização Z-Score** por série (média 0, desvio 1)
2. **Covariância:** `C = (1/T) × X × Xᵀ` com OpenMP `collapse(2)`
3. **Método da Potência:** Iterações até convergência `|λ_new - λ_old| < 10⁻⁹`
4. **Marchenko-Pastur:** `λ_max_MP = 1 + 1/Q + 2√(1/Q)` onde `Q = T/N`
5. **Signal Power:** `ratio = λ_dominant / λ_max_MP`

### Sinais
| Resultado | Significado |
|-----------|-------------|
| `power_ratio > 2.5` | **PURE_SIGNAL** — Institucional genuíno detectado |
| `power_ratio ≤ 2.5` | Ruído aleatório (varejo/HFT) |

### Visual MT5
Telemetria no HUD: `RMT: PURE_SIGNAL` ou `RMT: NOISE`. Sem renderização gráfica.

---

## 7. QRW — QUANTUM RANDOM WALK (Motor Preditivo)

| Campo | Valor |
|-------|-------|
| **C++** | `src/qrw/qrw_engine.cpp` (191 linhas) |
| **Python** | `quantum_walk.py` (107 linhas) |
| **Teoria** | Passeio Quântico em Linha + Moeda de Hadamard Assimétrica |
| **Objetivo** | Mapear a assimetria probabilística do fluxo futuro |

### O Que Faz
Executa um **Quantum Random Walk** em grid de 401 posições com spin (up/down). O "bias" da moeda quântica é modulado pelo delta de preço real. A **assimetria (skewness)** da distribuição resultante indica a direção preferencial do mercado.

### Como Calcula (C++)
1. **Estado Inicial:** Centro do grid, superposição `|↑⟩ + |↓⟩` / √2
2. **Moeda Assimétrica:** `C = [[cos(θ), i·sin(θ)·e^(i·bias)], [i·sin(θ)·e^(-i·bias), cos(θ)]]`
3. **Bias:** `θ_bias = π/4 - tanh(Δ × scale × 2) × π/4` — Delta de preço modula o operador
4. **Decoerência Dinâmica:** `deco = 0.9992 × (1 - |tanh(Δ × scale × 0.01)|)` — Absorção quadrática nas bordas
5. **Shift:** `|↑⟩` move para esquerda, `|↓⟩` move para direita. Normalização unitária
6. **Skewness:** `⟨x⟩ = Σ(i - center) × P(i) / Σ P(i)` normalizado pelo centro

### Motor de PreCognition (C++)
**`simulate_future_collapse`**: Roda 500 simulações Monte Carlo paralelas (OpenMP) projetando o preço futuro via random walk estocástico:
- Detecta se o preço está em modo "Contenção" ou "Fuga"
- Retorna vetor de breach_levels para cálculo de SL de singularidade

### Sinais
| Skewness | Significado |
|----------|-------------|
| > 0.08 | `QRW_BULL_DRIFT` — Acúmulo institucional de alta |
| < -0.08 | `QRW_BEAR_DRIFT` — Distribuição institucional de baixa |
| ±0.08 | `QUANTUM_STABILITY` — Equilíbrio |

### Visual MT5
Telemetria no HUD: `QRW: BULL_DRIFT` / `BEAR_DRIFT`. Skew history transmitido como cache.

---

## 8. RHT — RESONANCE HEAT TENSOR (Termodinâmica Multi-TF)

| Campo | Valor |
|-------|-------|
| **C++** | `src/rht/rht_engine.cpp` (206 linhas) |
| **Python** | `live_rht.py` (137 linhas) |
| **Teoria** | Entropia de Shannon + Coerência de Fase + Inércia Térmica |
| **Objetivo** | Detectar alinhamento termodinâmico entre múltiplos timeframes |

### O Que Faz
Injeta tensores de momentum de 5 timeframes (M5, M15, H1, H2, D1) no motor C++. Calcula a **Coerência de Fase** (todos concordam em direção?), a **Entropia de Shannon** (desordem) e o **Calor Acumulado** (inércia direcional). Quando todos os TFs alinham com baixa entropia → **Flash Ignition** (sinal forte).

### Como Calcula (C++)
1. **Momentum Tensores:** Z-Score local (rolling 20) dos retornos de cada TF
2. **Coerência:** `|Σval| / Σ|val|` — Quão unânimes são os TFs (0.0 a 1.0)
3. **Entropia Shannon:** `-Σ(p × log₂(p))` onde p = proporção buy/sell
4. **Calor Instantâneo:** `direction × coherence^2.5 × energy × (1 - entropy) × purity`
5. **Acumulador de Inércia:** `heat = heat × decay + instant × (1 - decay)` com `decay = 0.92`
6. **Gravidade Macro:** Média de H1+H2+D1 com memória EMA. Bloqueio total se gravidade contra-regime
7. **Flash Ignition:** `coherence > 0.85 AND |heat| > threshold AND entropy < 0.22 AND consensus ≥ 0.8`

### Sinais
| Flag | Significado |
|------|-------------|
| `+1.0` | **Bull Ignition** — Todos TFs alinhados para alta com baixa entropia |
| `-1.0` | **Bear Ignition** — Todos TFs alinhados para baixa com baixa entropia |
| `0.0` | Purificando (sem alinhamento suficiente) |

### Visual MT5
**Setas (Wingdings 233/234)** nos pontos de Flash Ignition:
- Teal `(38,166,154)` = Bull Flash
- Red `(239,83,80)` = Bear Flash

---

## 9. QDD — QUANTUM DECOHERENCE DYNAMICS (Rede Tensorial)

| Campo | Valor |
|-------|-------|
| **C++** | `src/qdd/qdd_engine.cpp` (244 linhas) |
| **Python** | `tensor_network.py` (73 linhas) + `quantum_indicators.py` (474 linhas) |
| **Teoria** | Grupo de Renormalização (Haar Wavelets) + Emaranhamento Quântico |
| **Objetivo** | Medir coerência dimensional entre timeframes e quantizar regimes |

### O Que Faz
Dois papéis críticos:
1. **Quantização de Regime:** Aplica RG Flow (wavelets) para filtrar ruído UV e medir energia cinética macro
2. **Fidelidade de Emaranhamento:** Calcula `F = |⟨ψ_macro|ψ_micro⟩|²` entre TFs para medir alinhamento dimensional

### Como Calcula (C++)
1. **Renormalization Flow (Haar):** Reduce série temporal via low-pass `(a[i] + a[i+1]) / √2` em `uv_cutoff` níveis
2. **Energia Eigen:** `E = Σ(Δp²) / 2N` — energia cinética do estado macro
3. **Decoerência:** `E_final = E × e^(-γ)` com `γ = 0.05`
4. **Fidelidade Bilateral:** Normaliza momentums de macro e micro, produto interno `⟨p_macro|p_micro⟩²`. Negativo = Efeito Estilingue (pullback)
5. **Contração Tensorial N-D:** Média de todos os pares `(i,j)` de TFs

### Sinais
| Fidelidade | Estado |
|------------|--------|
| > 0.8 | `QUANTUM_ENTANGLEMENT_BULL` |
| < -0.8 | `QUANTUM_ENTANGLEMENT_BEAR` |
| |F| < 0.2 | `DIMENSIONAL_DECOHERENCE (NOISE)` |
| outros | `SUPERPOSITION_STATE` |

### Visual MT5
Telemetria HUD: `QDD Fidelity: 0.XXXX`. Sem renderização gráfica direta.

---

## 10. QHO — QUANTUM HARMONIC OSCILLATOR

| Campo | Valor |
|-------|-------|
| **C++** | `src/qho/qho_engine.cpp` (76 linhas) |
| **Python** | `quantum_oscillator.py` (76 linhas) |
| **Teoria** | Oscilador Harmônico Quântico + Polinômios de Hermite |
| **Objetivo** | Quantizar a distância do preço ao Fair Value em níveis de energia |

### O Que Faz
Mapeia o Z-Score do preço (distância do IFV — Institutional Fair Value) em **estados de energia quantizados** (n = 0, 1, 2, ...). Estados altos = preço muito longe do equilíbrio = sobre-excitação.

### Como Calcula (C++)
1. **Polinômios de Hermite:** Recursão `H_n(x) = 2xH_{n-1} - 2(n-1)H_{n-2}`
2. **Função de Onda:** `ψ_n(x) = N × e^(-x²/2) × H_n(x)` onde `N = 1/√(2ⁿ × n! × √π)`
3. **Nível de Energia:** `n = floor(x²/2)` — quantização direta do Z-Score
4. **Estabilidade:** `|ψ₀(z)|² × √π` — probabilidade de estar no ground state

### Estados
| n | Status |
|---|--------|
| 0 | `GROUND_STATE` — Preço no equilíbrio |
| 1-2 | `STABLE_EXCITATION` — Desvio normal |
| 3-5 | `HIGH_ENERGY_ALERT` — Atenção |
| > 5 | `CRITICAL_EXHAUSTION` ou `CRITICAL_DEPRESSION` |

### Visual MT5
**Shells (cascas de energia)** — Linhas horizontais no preço do IFV ± `i × 0.25σ` para i = -5 a +5. Telemetria: `n=X`, `stability=0.XXXX`.

---

## 11. QTE — QUANTUM TUNNELING ENGINE

| Campo | Valor |
|-------|-------|
| **C++** | `src/qte/qte_engine.cpp` (63 linhas) |
| **Python** | `quantum_tunneling.py` (69 linhas) |
| **Teoria** | Aproximação WKB + Efeito Josephson |
| **Objetivo** | Calcular Take Profit via probabilidade de tunelamento |

### O Que Faz
Calcula se o preço tem "energia cinética" suficiente para **tunelar** através de uma barreira de liquidez (resistência/suporte). Se sim → HOLD. Se não → TAKE PROFIT.

### Como Calcula (C++)
1. **Coeficiente WKB:** `T = e^(-2 × ∫κ(x)dx)` onde `κ = √(2m(V-E)) / ħ`
2. **Integral de Ação:** Soma `κ` apenas onde `V(x) > E` (região classicamente proibida)
3. **Corrente de Josephson:** `I = I_c × sin(φ)` — sincronia bid/ask

### Sinais
| T_prob | Conselho |
|--------|----------|
| > 0.85 | `HOLD_FOR_TUNNELING` — Preço vai atravessar |
| < 0.15 | `QUANTUM_EXIT_NOW` — Preço vai ricochetear |
| 0.15-0.85 | `STABLE_ORBIT` — Manter posição |
| ≤ 0 | `SCANNING_BARRIER` |

### Visual MT5
Telemetria HUD: `QTE: 0.XXXX` + `HOLD/EXIT/ORBIT`. Sem renderização gráfica direta.
