# ðŸ§¬ MANUAL DE SISTEMAS AETHELGARD â€” CÃ“DICE OPERACIONAL ASI v1.0
**ClassificaÃ§Ã£o: Ph.D. Level Â· Documento Forense Completo**

---

## 1. ARQUITETURA GERAL

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚              AETHELGARD SWARM (Python)                  â”‚
â”‚  N-Core (DecisÃ£o) â”€ Q-Math (FÃ­sica) â”€ R-Exec (MT5)    â”‚
â”‚                      â”‚                                  â”‚
â”‚              ZMQ Router (PUB/SUB)                       â”‚
â”‚                      â”‚                                  â”‚
â”‚    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”            â”‚
â”‚    â”‚     C++ ENGINE LAYER (.pyd DLLs)      â”‚            â”‚
â”‚    â”‚  CYT LBM SCH QGC RMT QRW RHT        â”‚            â”‚
â”‚    â”‚  QDD QHO QTE MHD                      â”‚            â”‚
â”‚    â”‚  OpenMP Â· GIL Release Â· pybind11      â”‚            â”‚
â”‚    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜            â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                     â”‚ Raw TCP Socket
              â”Œâ”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”
              â”‚ MetaTrader 5 â”‚
              â”‚ Nexus_Observer.mq5
              â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

**Stack:** Python 3.11 + C++17 + MQL5
**ComunicaÃ§Ã£o:** ZeroMQ PUB/SUB + REQ/REP + Raw TCP Socket
**CompilaÃ§Ã£o C++:** MinGW64 + pybind11 â†’ `.pyd`
**Paralelismo:** OpenMP em todos os motores C++

---

## 2. CYT â€” TOPOLOGIA CALABI-YAU (Ricci Flow)

| Campo | Valor |
|-------|-------|
| **C++** | `src/cyt/cyt_engine.cpp` (227 linhas) |
| **Python** | `yield_governor.py` (109 linhas) |
| **Teoria** | Ricci Flow + AdS/CFT HologrÃ¡fico |
| **Objetivo** | Detectar deformaÃ§Ãµes topolÃ³gicas na estrutura de mercado |

### O Que Faz
Modela o mercado como **Variedade Riemanniana 10D**. Calcula o **Tensor de Ricci** para detectar rasgos na geometria â€” estresse extremo que pode causar colapso.

### Como Calcula (C++)
1. **NormalizaÃ§Ã£o L2:** Cada dimensÃ£o normalizada via Z-Score independente (Volume nÃ£o esmaga PreÃ§o)
2. **Ricci Flow:** `deformation[i] = âˆš(Î£ Î”Â²)` sobre 10 dimensÃµes
3. **Determinante MÃ©trico:** `Î (1 + |Î”|)` â€” volume da variedade. Se < 0.05 â†’ Colapso
4. **Danger Zones:** Z-Score janelado + EMA (Î±=0.15). Scores 0-100
5. **Entropia Bekenstein-Hawking:** `S = (A Ã— G_ef) / (4 Ã— L_planckÂ²)`

### Retorno
- `deformation[]`, `determinant[]`, `danger_zones[]` (0-100), `is_collapsed` (bool), `holographic_entropy`

### Visual MT5
Caixas Dark Red `RGB(35,5,8)` no fundo. Intensidade proporcional ao danger_score.

---

## 3. LBM â€” LATTICE BOLTZMANN METHOD

| Campo | Valor |
|-------|-------|
| **C++** | `src/lbm/lbm_engine.cpp` (149 linhas) |
| **Python** | `fluid_dynamics.py` (148 linhas) |
| **Teoria** | Navier-Stokes + Lattice Boltzmann D1Q3 |
| **Objetivo** | Modelar mercado como fluido viscoelÃ¡stico |

### O Que Faz
Grid 1D de 200 bins (faixa de preÃ§o). Cada vela injeta massa (volume) e momentum (direÃ§Ã£o do corpo). Fluido evolui via colisÃ£o BGK com **viscosidade dinÃ¢mica** responsiva Ã  turbulÃªncia.

### Como Calcula (C++)
1. **D1Q3:** `f0` (estÃ¡tico), `f1` (bull/direita), `f2` (bear/esquerda)
2. **InjeÃ§Ã£o:** `inject_liquidity(idx, mass, momentum)` â€” momentum clampado Â±0.3
3. **Ï„ DinÃ¢mico:** `Ï„_dyn = Ï„ Ã— (1 + e^(-KE_avg))`. TurbulÃªnciaâ†‘ â†’ Ï„â†“ â†’ fluido ferve
4. **Decaimento:** `mass_decay = 0.995` por step
5. **Deborah Number:** `De = Ï„ / t_anomalia`. Se `De > 1.2`: absorÃ§Ã£o viscoelÃ¡stica

### Sinais
| Sinal | CondiÃ§Ã£o |
|-------|----------|
| `FLUID_RUPTURE_BULL` | Z(Ï) > 3.5, velocity > 0.05, price > mid-range |
| `FLUID_RUPTURE_BEAR` | Z(Ï) > 3.5, velocity < -0.05, price < mid-range |
| `BOSONIC_SQUEEZE` | Z(Ï) > 3.2, |velocity| < 0.03 |
| `LAMINAR_FLOW` | Neutro |

### Visual MT5
Mini-cÃ­rculos Wingdings: Teal `(38,166,154)` = Bull, Red `(239,83,80)` = Bear, Amber `(255,193,7)` = Squeeze.

---

## 4. SCHRÃ–DINGER â€” NUVEM DE PROBABILIDADE

| Campo | Valor |
|-------|-------|
| **C++** | `src/schrodinger/schrodinger_engine.cpp` (287 linhas) |
| **Python** | `quantum_clouds.py` (225 linhas) |
| **Teoria** | Eq. SchrÃ¶dinger + Thomas Algorithm + PML + S-Matrix |
| **Objetivo** | Mapear distribuiÃ§Ã£o de probabilidade do preÃ§o futuro |

### O Que Faz
Resolve a **Eq. de SchrÃ¶dinger dependente do tempo** em grid 512-bin. Potencial V(x) gerado do perfil de volume (alto volume = poÃ§o gravitacional). `|Ïˆ|Â²` = densidade de probabilidade do preÃ§o.

### Como Calcula (C++)
1. **Gaussiana Inicial:** Centrada no preÃ§o atual, `Ïƒ = dx Ã— 12`
2. **Crank-Nicolson:** MÃ©todo implÃ­cito 2Âª ordem via Thomas Algorithm. Sub-steps adaptativos
3. **PML:** Bordas absorventes cÃºbicas `100 Ã— fracÂ³`
4. **Drift (AdvecÃ§Ã£o):** `iÂ·Ä§Â·v_driftÂ·âˆ‚Ïˆ/âˆ‚x` empurra onda na direÃ§Ã£o do momentum
5. **Massa Espacial:** Zonas alto-volume â†’ maior massa â†’ onda desacelera
6. **Constante de Planck DinÃ¢mica:** Baseada no ATR (evita underflow `exp(-600)`)
7. **S-Matrix:** `|S_fi|Â² = (coupling / (Î”E + coupling))Â²` â€” aniquilaÃ§Ã£o de vÃ¡cuos

### MÃ©tricas
- `singularity_strength` â€” ConcentraÃ§Ã£o mÃ¡xima vs total
- `schwarzschild_radius` â€” Raio do horizonte de eventos
- `peak_price` â€” PreÃ§o no pico de probabilidade
- `tunneling_probability` â€” WKB de atravessar barreira

### Visual MT5
Heatmap de linhas horizontais: Crimson/Teal sutil. Largura = `density Ã— 8`.

---

## 5. QGC â€” QUANTUM GRAVITY CONDENSATE

| Campo | Valor |
|-------|-------|
| **C++** | `src/qgc/qgc_engine.cpp` (83 linhas) |
| **Python** | `quantum_glass.py` (61 linhas) |
| **Teoria** | Quantum Liquidity Glass + RadiaÃ§Ã£o Hawking |
| **Objetivo** | Mapear zonas de liquidez institucional que decaem no tempo |

### O Que Faz
"Order Blocks" sÃ£o **Condensados de Vidro Amorfo** com **RadiaÃ§Ã£o Hawking** (decaimento exponencial). Massa inicial âˆ volume. EvaporaÃ§Ã£o acelerada se preÃ§o se afasta.

### Como Calcula (C++)
1. **CriaÃ§Ã£o:** `add_zone(price, mass, time)`. Merge se jÃ¡ existir zona Â±5 pts
2. **EvaporaÃ§Ã£o:** `M(t) = Mâ‚€ Ã— e^(-0.0002 Ã— Î”t Ã— (1 + dist/100))`
3. **Poda:** Remove se `mass < 10%` da original
4. **Gravidade Plummer:** `pull = Î£(mass_i / âˆš(distÂ² + 1.5Â²))`

### Scanner Python
- Z-Score volume > 1.5Ïƒ â†’ nova zona
- Boot: scan 200 barras histÃ³ricas para popular

### Visual MT5
RetÃ¢ngulos ultra-sutis `RGB(35,5,8)` com fitas de evaporaÃ§Ã£o. Z-Order 0 (fundo).
# ðŸ§¬ MANUAL DE SISTEMAS AETHELGARD â€” PARTE 2
**RMT Â· QRW Â· RHT Â· QDD Â· QHO Â· QTE**

---

## 6. RMT â€” RANDOM MATRIX THEORY (Filtro Espectral)

| Campo | Valor |
|-------|-------|
| **C++** | `src/rmt/rmt_engine.cpp` (127 linhas) |
| **Python** | `random_matrix.py` (93 linhas) |
| **Teoria** | DecomposiÃ§Ã£o Espectral + DistribuiÃ§Ã£o Marchenko-Pastur |
| **Objetivo** | Separar sinal institucional genuÃ­no do ruÃ­do aleatÃ³rio do varejo |

### O Que Faz
ConstrÃ³i uma **Matriz de CovariÃ¢ncia** 8Ã—8 a partir de features do mercado (retornos, spreads, volume, body, pavios, entropia, LBM velocity). Extrai o **autovalor dominante** via MÃ©todo da PotÃªncia e compara com o **limite teÃ³rico de Marchenko-Pastur** para determinar se existe um sinal institucional real ou se Ã© apenas ruÃ­do estocÃ¡stico.

### Features da Matriz (8 DimensÃµes)
1. Returns (retorno percentual)
2. Spreads (high - low)
3. Volume (tick_volume)
4. Bodies (|close - open|)
5. Upper Wicks
6. Lower Wicks
7. Volatility Entropy (ATR normalizado)
8. LBM Velocity (feedback do fluido)

### Como Calcula (C++)
1. **NormalizaÃ§Ã£o Z-Score** por sÃ©rie (mÃ©dia 0, desvio 1)
2. **CovariÃ¢ncia:** `C = (1/T) Ã— X Ã— Xáµ€` com OpenMP `collapse(2)`
3. **MÃ©todo da PotÃªncia:** IteraÃ§Ãµes atÃ© convergÃªncia `|Î»_new - Î»_old| < 10â»â¹`
4. **Marchenko-Pastur:** `Î»_max_MP = 1 + 1/Q + 2âˆš(1/Q)` onde `Q = T/N`
5. **Signal Power:** `ratio = Î»_dominant / Î»_max_MP`

### Sinais
| Resultado | Significado |
|-----------|-------------|
| `power_ratio > 2.5` | **PURE_SIGNAL** â€” Institucional genuÃ­no detectado |
| `power_ratio â‰¤ 2.5` | RuÃ­do aleatÃ³rio (varejo/HFT) |

### Visual MT5
Telemetria no HUD: `RMT: PURE_SIGNAL` ou `RMT: NOISE`. Sem renderizaÃ§Ã£o grÃ¡fica.

---

## 7. QRW â€” QUANTUM RANDOM WALK (Motor Preditivo)

| Campo | Valor |
|-------|-------|
| **C++** | `src/qrw/qrw_engine.cpp` (191 linhas) |
| **Python** | `quantum_walk.py` (107 linhas) |
| **Teoria** | Passeio QuÃ¢ntico em Linha + Moeda de Hadamard AssimÃ©trica |
| **Objetivo** | Mapear a assimetria probabilÃ­stica do fluxo futuro |

### O Que Faz
Executa um **Quantum Random Walk** em grid de 401 posiÃ§Ãµes com spin (up/down). O "bias" da moeda quÃ¢ntica Ã© modulado pelo delta de preÃ§o real. A **assimetria (skewness)** da distribuiÃ§Ã£o resultante indica a direÃ§Ã£o preferencial do mercado.

### Como Calcula (C++)
1. **Estado Inicial:** Centro do grid, superposiÃ§Ã£o `|â†‘âŸ© + |â†“âŸ©` / âˆš2
2. **Moeda AssimÃ©trica:** `C = [[cos(Î¸), iÂ·sin(Î¸)Â·e^(iÂ·bias)], [iÂ·sin(Î¸)Â·e^(-iÂ·bias), cos(Î¸)]]`
3. **Bias:** `Î¸_bias = Ï€/4 - tanh(Î” Ã— scale Ã— 2) Ã— Ï€/4` â€” Delta de preÃ§o modula o operador
4. **DecoerÃªncia DinÃ¢mica:** `deco = 0.9992 Ã— (1 - |tanh(Î” Ã— scale Ã— 0.01)|)` â€” AbsorÃ§Ã£o quadrÃ¡tica nas bordas
5. **Shift:** `|â†‘âŸ©` move para esquerda, `|â†“âŸ©` move para direita. NormalizaÃ§Ã£o unitÃ¡ria
6. **Skewness:** `âŸ¨xâŸ© = Î£(i - center) Ã— P(i) / Î£ P(i)` normalizado pelo centro

### Motor de PreCognition (C++)
**`simulate_future_collapse`**: Roda 500 simulaÃ§Ãµes Monte Carlo paralelas (OpenMP) projetando o preÃ§o futuro via random walk estocÃ¡stico:
- Detecta se o preÃ§o estÃ¡ em modo "ContenÃ§Ã£o" ou "Fuga"
- Retorna vetor de breach_levels para cÃ¡lculo de SL de singularidade

### Sinais
| Skewness | Significado |
|----------|-------------|
| > 0.08 | `QRW_BULL_DRIFT` â€” AcÃºmulo institucional de alta |
| < -0.08 | `QRW_BEAR_DRIFT` â€” DistribuiÃ§Ã£o institucional de baixa |
| Â±0.08 | `QUANTUM_STABILITY` â€” EquilÃ­brio |

### Visual MT5
Telemetria no HUD: `QRW: BULL_DRIFT` / `BEAR_DRIFT`. Skew history transmitido como cache.

---

## 8. RHT â€” RESONANCE HEAT TENSOR (TermodinÃ¢mica Multi-TF)

| Campo | Valor |
|-------|-------|
| **C++** | `src/rht/rht_engine.cpp` (206 linhas) |
| **Python** | `live_rht.py` (137 linhas) |
| **Teoria** | Entropia de Shannon + CoerÃªncia de Fase + InÃ©rcia TÃ©rmica |
| **Objetivo** | Detectar alinhamento termodinÃ¢mico entre mÃºltiplos timeframes |

### O Que Faz
Injeta tensores de momentum de 5 timeframes (M5, M15, H1, H2, D1) no motor C++. Calcula a **CoerÃªncia de Fase** (todos concordam em direÃ§Ã£o?), a **Entropia de Shannon** (desordem) e o **Calor Acumulado** (inÃ©rcia direcional). Quando todos os TFs alinham com baixa entropia â†’ **Flash Ignition** (sinal forte).

### Como Calcula (C++)
1. **Momentum Tensores:** Z-Score local (rolling 20) dos retornos de cada TF
2. **CoerÃªncia:** `|Î£val| / Î£|val|` â€” QuÃ£o unÃ¢nimes sÃ£o os TFs (0.0 a 1.0)
3. **Entropia Shannon:** `-Î£(p Ã— logâ‚‚(p))` onde p = proporÃ§Ã£o buy/sell
4. **Calor InstantÃ¢neo:** `direction Ã— coherence^2.5 Ã— energy Ã— (1 - entropy) Ã— purity`
5. **Acumulador de InÃ©rcia:** `heat = heat Ã— decay + instant Ã— (1 - decay)` com `decay = 0.92`
6. **Gravidade Macro:** MÃ©dia de H1+H2+D1 com memÃ³ria EMA. Bloqueio total se gravidade contra-regime
7. **Flash Ignition:** `coherence > 0.85 AND |heat| > threshold AND entropy < 0.22 AND consensus â‰¥ 0.8`

### Sinais
| Flag | Significado |
|------|-------------|
| `+1.0` | **Bull Ignition** â€” Todos TFs alinhados para alta com baixa entropia |
| `-1.0` | **Bear Ignition** â€” Todos TFs alinhados para baixa com baixa entropia |
| `0.0` | Purificando (sem alinhamento suficiente) |

### Visual MT5
**Setas (Wingdings 233/234)** nos pontos de Flash Ignition:
- Teal `(38,166,154)` = Bull Flash
- Red `(239,83,80)` = Bear Flash

---

## 9. QDD â€” QUANTUM DECOHERENCE DYNAMICS (Rede Tensorial)

| Campo | Valor |
|-------|-------|
| **C++** | `src/qdd/qdd_engine.cpp` (244 linhas) |
| **Python** | `tensor_network.py` (73 linhas) + `quantum_indicators.py` (474 linhas) |
| **Teoria** | Grupo de RenormalizaÃ§Ã£o (Haar Wavelets) + Emaranhamento QuÃ¢ntico |
| **Objetivo** | Medir coerÃªncia dimensional entre timeframes e quantizar regimes |

### O Que Faz
Dois papÃ©is crÃ­ticos:
1. **QuantizaÃ§Ã£o de Regime:** Aplica RG Flow (wavelets) para filtrar ruÃ­do UV e medir energia cinÃ©tica macro
2. **Fidelidade de Emaranhamento:** Calcula `F = |âŸ¨Ïˆ_macro|Ïˆ_microâŸ©|Â²` entre TFs para medir alinhamento dimensional

### Como Calcula (C++)
1. **Renormalization Flow (Haar):** Reduce sÃ©rie temporal via low-pass `(a[i] + a[i+1]) / âˆš2` em `uv_cutoff` nÃ­veis
2. **Energia Eigen:** `E = Î£(Î”pÂ²) / 2N` â€” energia cinÃ©tica do estado macro
3. **DecoerÃªncia:** `E_final = E Ã— e^(-Î³)` com `Î³ = 0.05`
4. **Fidelidade Bilateral:** Normaliza momentums de macro e micro, produto interno `âŸ¨p_macro|p_microâŸ©Â²`. Negativo = Efeito Estilingue (pullback)
5. **ContraÃ§Ã£o Tensorial N-D:** MÃ©dia de todos os pares `(i,j)` de TFs

### Sinais
| Fidelidade | Estado |
|------------|--------|
| > 0.8 | `QUANTUM_ENTANGLEMENT_BULL` |
| < -0.8 | `QUANTUM_ENTANGLEMENT_BEAR` |
| |F| < 0.2 | `DIMENSIONAL_DECOHERENCE (NOISE)` |
| outros | `SUPERPOSITION_STATE` |

### Visual MT5
Telemetria HUD: `QDD Fidelity: 0.XXXX`. Sem renderizaÃ§Ã£o grÃ¡fica direta.

---

## 10. QHO â€” QUANTUM HARMONIC OSCILLATOR

| Campo | Valor |
|-------|-------|
| **C++** | `src/qho/qho_engine.cpp` (76 linhas) |
| **Python** | `quantum_oscillator.py` (76 linhas) |
| **Teoria** | Oscilador HarmÃ´nico QuÃ¢ntico + PolinÃ´mios de Hermite |
| **Objetivo** | Quantizar a distÃ¢ncia do preÃ§o ao Fair Value em nÃ­veis de energia |

### O Que Faz
Mapeia o Z-Score do preÃ§o (distÃ¢ncia do IFV â€” Institutional Fair Value) em **estados de energia quantizados** (n = 0, 1, 2, ...). Estados altos = preÃ§o muito longe do equilÃ­brio = sobre-excitaÃ§Ã£o.

### Como Calcula (C++)
1. **PolinÃ´mios de Hermite:** RecursÃ£o `H_n(x) = 2xH_{n-1} - 2(n-1)H_{n-2}`
2. **FunÃ§Ã£o de Onda:** `Ïˆ_n(x) = N Ã— e^(-xÂ²/2) Ã— H_n(x)` onde `N = 1/âˆš(2â¿ Ã— n! Ã— âˆšÏ€)`
3. **NÃ­vel de Energia:** `n = floor(xÂ²/2)` â€” quantizaÃ§Ã£o direta do Z-Score
4. **Estabilidade:** `|Ïˆâ‚€(z)|Â² Ã— âˆšÏ€` â€” probabilidade de estar no ground state

### Estados
| n | Status |
|---|--------|
| 0 | `GROUND_STATE` â€” PreÃ§o no equilÃ­brio |
| 1-2 | `STABLE_EXCITATION` â€” Desvio normal |
| 3-5 | `HIGH_ENERGY_ALERT` â€” AtenÃ§Ã£o |
| > 5 | `CRITICAL_EXHAUSTION` ou `CRITICAL_DEPRESSION` |

### Visual MT5
**Shells (cascas de energia)** â€” Linhas horizontais no preÃ§o do IFV Â± `i Ã— 0.25Ïƒ` para i = -5 a +5. Telemetria: `n=X`, `stability=0.XXXX`.

---

## 11. QTE â€” QUANTUM TUNNELING ENGINE

| Campo | Valor |
|-------|-------|
| **C++** | `src/qte/qte_engine.cpp` (63 linhas) |
| **Python** | `quantum_tunneling.py` (69 linhas) |
| **Teoria** | AproximaÃ§Ã£o WKB + Efeito Josephson |
| **Objetivo** | Calcular Take Profit via probabilidade de tunelamento |

### O Que Faz
Calcula se o preÃ§o tem "energia cinÃ©tica" suficiente para **tunelar** atravÃ©s de uma barreira de liquidez (resistÃªncia/suporte). Se sim â†’ HOLD. Se nÃ£o â†’ TAKE PROFIT.

### Como Calcula (C++)
1. **Coeficiente WKB:** `T = e^(-2 Ã— âˆ«Îº(x)dx)` onde `Îº = âˆš(2m(V-E)) / Ä§`
2. **Integral de AÃ§Ã£o:** Soma `Îº` apenas onde `V(x) > E` (regiÃ£o classicamente proibida)
3. **Corrente de Josephson:** `I = I_c Ã— sin(Ï†)` â€” sincronia bid/ask

### Sinais
| T_prob | Conselho |
|--------|----------|
| > 0.85 | `HOLD_FOR_TUNNELING` â€” PreÃ§o vai atravessar |
| < 0.15 | `QUANTUM_EXIT_NOW` â€” PreÃ§o vai ricochetear |
| 0.15-0.85 | `STABLE_ORBIT` â€” Manter posiÃ§Ã£o |
| â‰¤ 0 | `SCANNING_BARRIER` |

### Visual MT5
Telemetria HUD: `QTE: 0.XXXX` + `HOLD/EXIT/ORBIT`. Sem renderizaÃ§Ã£o grÃ¡fica direta.
# ðŸ§¬ MANUAL DE SISTEMAS AETHELGARD â€” PARTE 3
**MHD Â· QCD Â· Regime Â· PreCognition Â· Nexus Observer Â· Fluxo**

---

## 12. MHD â€” MAGNETOHYDRODYNAMICS (Z-Pinch)

| Campo | Valor |
|-------|-------|
| **C++** | `src/mhd/mhd_engine.cpp` (113 linhas) |
| **Python** | `plasma_market.py` (145 linhas) |
| **Teoria** | RelaÃ§Ã£o de Bennett + Z-Pinch + ForÃ§as de Lorentz |
| **Objetivo** | Detectar Stop Hunts institucionais como compressÃ£o de plasma magnÃ©tico |

### O Que Faz
Modela zonas de liquidez (topos/fundos) como **membranas de plasma**. Quando o preÃ§o entra na zona, a "corrente institucional" (volume Ã— momentum) comprime o plasma. Se a PressÃ£o MagnÃ©tica `BÂ²/2Î¼` vence a PressÃ£o TÃ©rmica `nkT`, ocorre **Z-Pinch** (colapso do plasma â†’ reversÃ£o violenta).

### Como Calcula (C++)
1. **Corrente J:** `|Î”price| Ã— (volume / volume_ema)` com suavizaÃ§Ã£o `0.7 Ã— J_old + 0.3 Ã— J_new`
2. **ForÃ§a de Lorentz:** `F_L = Î¼â‚€ Ã— JÂ²`
3. **Raio do Plasma:** `dr = (P - F_L) Ã— 0.01`. Clampado [0.01, 2.0]
4. **PressÃ£o (Bennett):** `P = density Ã— (1/radius)^(2Î³)` com cap 500.0 e log-scaling
5. **Z-Index ContÃ­nuo:** `min(80, -ln(radius) Ã— 25)` se comprimido. +20 se detonaÃ§Ã£o (Pâ†‘â†‘, Jâ†“)
6. **Thresholds Adaptativos:** Via EMAs de pressÃ£o e corrente (nÃ£o constantes mÃ¡gicas)

### Scanner Python
- Identifica zonas via Kernel de densidade ATR sobre os Ãºltimos 150 pavios
- MÃ¡quina de estado: NEUTRAL â†’ TOP_SWEEP/BOTTOM_SWEEP â†’ reset ao sair

### Visual MT5
Telemetria HUD: `Magnetic Pull: X.XX mT`. Z-Index history. Sem renderizaÃ§Ã£o grÃ¡fica direta (informaÃ§Ã£o para o SL dinÃ¢mico).

---

## 13. QCD â€” QUANTUM CHROMODYNAMICS (FissÃ£o)

| Campo | Valor |
|-------|-------|
| **C++** | LÃ³gica pura Python (sem engine C++) |
| **Python** | `market_qcd.py` (99 linhas) |
| **Teoria** | ForÃ§a Forte (Confinamento + Liberdade AssintÃ³tica) |
| **Objetivo** | Detectar "explosÃµes" direcionais quando a energia rompe o confinamento |

### O Que Faz
Modela o preÃ§o como partÃ­cula confinada por uma "corda de liquidez" (VWAP). A forÃ§a de confinamento **aumenta** com a distÃ¢ncia (como a ForÃ§a Forte nuclear). Quando a energia cinÃ©tica ultrapassa o threshold â†’ **FissÃ£o** (rompimento explosivo).

### Como Calcula
1. **Cargas de Cor:** `RED` = vendedores Ã— volume, `GREEN` = compradores Ã— volume, `BLUE` = pavios Ã— volume. Normalizado
2. **ForÃ§a de Confinamento:** `F = k Ã— r` onde `k = std(close)` e `r = |price - VWAP|`
3. **Energia CinÃ©tica:** `E = body_atual / mean(bodies_filtrados)`
4. **FissÃ£o:** Se `E > 2.0` E `body_ratio > 0.70` (corpo > 70% da vela) â†’ FissÃ£o

### Sinais â€” âš¡ OS "SHORTS" QUE VOCÃŠ GOSTOU
| Sinal | CondiÃ§Ã£o |
|-------|----------|
| `FISSION_EXPANSION_UP` | E > 2.0 + body_ratio > 70% + close > open |
| `FISSION_EXPANSION_DOWN` | E > 2.0 + body_ratio > 70% + close < open |
| `CONFINED_E(X.XX)` | Energia insuficiente para rompimento |

> [!IMPORTANT]
> **Este Ã© o sistema que gera os sinais SHORT/LONG no grÃ¡fico.** Ele detecta velas institucionais massivas (corpo > 2x a mÃ©dia E > 70% do range total) â€” sÃ£o os movimentos de "canhÃ£o" do mercado.

### Visual MT5
Tags TradingView-style: `SHORT 78344.89` em vermelho ou setas teal para Bull. Renderizado via `CreateTradingViewTag()`.

---

## 14. REGIME ENGINE â€” SOBERANIA DE FLUXO

| Campo | Valor |
|-------|-------|
| **Arquivo** | `quantum_indicators.py` (474 linhas) |
| **Teoria** | Flow Sovereignty (5 camadas EMA + ATR + PivÃ´s) |
| **Objetivo** | Determinar o regime macro: BULL TSUNAMI / BEAR TSUNAMI / NEUTRAL |

### O Que Faz
O coraÃ§Ã£o decisÃ³rio da mÃ¡quina. Usa 5 camadas de EMA (9, 21, 34, 89, 200), ATR, pivÃ´s estruturais e lÃ³gica de histerese para classificar o regime macro com **imunidade de 10 velas** contra colapsos triviais.

### Camadas de DecisÃ£o
1. **EMAs:** Fast(9), Mid(21), Trend(34), Macro(89), Gravity(200)
2. **IgniÃ§Ã£o AtÃ´mica:** Body > 1.1Ã— ATR + rompimento de high/low de 10 barras
3. **Singularidade AtÃ´mica (ARS):** ReversÃ£o imediata em extremos absolutos de 120 barras
4. **ExaustÃ£o por Sombra:** Pavio > 2Ã— body em topo/fundo local (red em topo, green em fundo)
5. **Momentum Lock:** Regime sÃ³ colapsa se EMA 9/21 virou contra
6. **Noise Gate:** SaÃ­da do neutro exige spread EMA > 0.5Ã— ATR
7. **Imunidade Maturada:** 10 velas de proteÃ§Ã£o (conf < 110)

### Regime Boxes
- `1` = **TSUNAMI_BULL** â€” Caixas com borda Teal `(38,166,154)`
- `2` = **TSUNAMI_BEAR** â€” Caixas com borda Red `(239,83,80)`
- `0` = **SCANNING** â€” Sem caixa

### Tactical Dots
Mini-triÃ¢ngulos coloridos que indicam a "saÃºde" do regime em cada vela. Gerados via `calculate_tactical_dots()`.

---

## 15. PRECOGNITION â€” MOTOR DE VISÃƒO DE FUTURO

| Campo | Valor |
|-------|-------|
| **Arquivo** | `quantum_projection.py` (62 linhas) |
| **DependÃªncias** | QRW Engine C++ + MHD PlasmaMarket |
| **Objetivo** | Calcular Stop Loss de Singularidade via projeÃ§Ã£o estocÃ¡stica |

### O Que Faz
Combina as zonas de plasma (MHD) com simulaÃ§Ãµes Monte Carlo (QRW C++) para projetar 500 caminhos futuros e determinar onde o preÃ§o provavelmente colapsa.

### Como Calcula
1. ObtÃ©m zonas de plasma atuais (top_level, bottom_level) via MHD
2. Executa `simulate_future_collapse()` no C++ (OpenMP, 500 paths, 40 steps)
3. Calcula `sl_bull = percentil(5%)` e `sl_bear = percentil(95%)` dos breach levels

### Retorno
- `sl_bull_singular` â€” SL para posiÃ§Ãµes de compra
- `sl_bear_singular` â€” SL para posiÃ§Ãµes de venda
- `breach_prob` â€” Probabilidade de ruptura

---

## 16. YIELD GOVERNOR â€” ESCUDO TOPOLÃ“GICO

| Campo | Valor |
|-------|-------|
| **Arquivo** | `yield_governor.py` (109 linhas) |
| **DependÃªncia** | CYT Engine C++ |
| **Objetivo** | Monitorar saÃºde topolÃ³gica e detectar Bull/Bear Traps |

### FunÃ§Ãµes
- **`monitor_topology`** â€” Calcula deformaÃ§Ã£o e ativa escudo se `avg_deformation > threshold`
- **`analyze_historical_danger`** â€” Gera mapa completo de danger zones histÃ³ricas
- **`detect_topological_trap`** â€” DivergÃªncia entre price_slope e determinant_slope
  - PreÃ§oâ†‘ + Determinanteâ†“ = `BULL_TRAP`
  - PreÃ§oâ†“ + Determinanteâ†‘ = `BEAR_TRAP`
- **`evaluate_dimensional_collapse`** â€” Verifica se a malha colapsou (invalidando a tese)

---

## 17. NEXUS OBSERVER â€” DASHBOARD HFT (MQL5)

| Campo | Valor |
|-------|-------|
| **Arquivo** | `Code/MQL5/Nexus_Observer.mq5` (~1012 linhas) |
| **ComunicaÃ§Ã£o** | Raw TCP Socket (porta dinÃ¢mica) |
| **FunÃ§Ã£o** | RenderizaÃ§Ã£o visual + ExecuÃ§Ã£o de ordens + HUD |

### Componentes Visuais
| Componente | Tipo de Objeto | Cor |
|------------|---------------|-----|
| Regime Boxes | `OBJ_RECTANGLE` | Teal/Red TV palette |
| LBM Dots | `OBJ_ARROW` (Wingdings 159) | Teal/Red/Amber |
| RHT Sparks | `OBJ_ARROW` (Wingdings 233/234) | Teal/Red |
| CYT Danger | `OBJ_RECTANGLE` | Dark Red ultra-sutil |
| QGC Gravity | RetÃ¢ngulos evaporaÃ§Ã£o | Dark Red |
| QCD Tags | `CreateTradingViewTag()` | Teal/Red com preÃ§o |
| SchrÃ¶dinger Heatmap | `OBJ_TREND` horizontal | Crimson/Teal gradual |
| QHO Shells | `OBJ_TREND` horizontal | Dotted lines |
| HUD Panel | `OBJ_RECTANGLE_LABEL` + `OBJ_LABEL` | Ebony Stealth |

### HUD Panel (Telemetria)
```
AETHELGARD :: QUANTUM CORE
â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
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
MT5 (PreÃ§o/Volume)
  â†“
q_math_node.py (Coleta + 7 Threads de FÃ­sica C++)
  â†“ ZMQ PUB
Aethelgard_Swarm.py (N-Core: Regime + DecisÃ£o)
  â†“ consulta ZMQ REQ
q_math_node.py (Q-Math: retorna q_state com todos os motores)
  â†“
Aethelgard_Swarm.py (Monta nexus_data_str com ~40 campos)
  â†“ TCP Socket
Nexus_Observer.mq5 (ParseAndDraw: Renderiza tudo + Executa ordens)
```

### Campos da nexus_data_str (separados por `;`)
```
0: unused
1: unused
2: status_final (ex: "TSUNAMI_BULL | CONF: 87%")
3: unused
4: regimes_cache (CSV de "score|conf")
5: inst_avg (preÃ§o mÃ©dio)
6: health (0.0-1.0)
7: signals_cache
8: dots_cache
9: inst_avg (duplicado)
10: cloud_str (SchrÃ¶dinger heatmap)
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
> **Sobre os Sinais SHORT:** Eles vÃªm do mÃ³dulo **QCD (Quantum Chromodynamics)** â€” `market_qcd.py`. A lÃ³gica `detect_fission()` identifica velas institucionais com corpo > 2Ã— a mÃ©dia e > 70% do range total. Esses sÃ£o os sinais mais puros da mÃ¡quina: detectam movimentos de canhÃ£o institucional sem ruÃ­do.
