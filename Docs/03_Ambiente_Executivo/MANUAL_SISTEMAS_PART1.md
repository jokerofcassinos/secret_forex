# 🧬 MANUAL DE SISTEMAS AETHELGARD — CÓDICE OPERACIONAL ASI v1.0
**Classificação: Ph.D. Level · Documento Forense Completo**

---

## 1. ARQUITETURA GERAL

```
┌────────────────────────────────────────────────────────┐
│              AETHELGARD SWARM (Python)                  │
│  N-Core (Decisão) ─ Q-Math (Física) ─ R-Exec (MT5)    │
│                      │                                  │
│              ZMQ Router (PUB/SUB)                       │
│                      │                                  │
│    ┌─────────────────┴─────────────────────┐            │
│    │     C++ ENGINE LAYER (.pyd DLLs)      │            │
│    │  CYT LBM SCH QGC RMT QRW RHT        │            │
│    │  QDD QHO QTE MHD                      │            │
│    │  OpenMP · GIL Release · pybind11      │            │
│    └───────────────────────────────────────┘            │
└────────────────────┬───────────────────────────────────┘
                     │ Raw TCP Socket
              ┌──────┴──────┐
              │ MetaTrader 5 │
              │ Nexus_Observer.mq5
              └─────────────┘
```

**Stack:** Python 3.11 + C++17 + MQL5
**Comunicação:** ZeroMQ PUB/SUB + REQ/REP + Raw TCP Socket
**Compilação C++:** MinGW64 + pybind11 → `.pyd`
**Paralelismo:** OpenMP em todos os motores C++

---

## 2. CYT — TOPOLOGIA CALABI-YAU (Ricci Flow)

| Campo | Valor |
|-------|-------|
| **C++** | `src/cyt/cyt_engine.cpp` (227 linhas) |
| **Python** | `yield_governor.py` (109 linhas) |
| **Teoria** | Ricci Flow + AdS/CFT Holográfico |
| **Objetivo** | Detectar deformações topológicas na estrutura de mercado |

### O Que Faz
Modela o mercado como **Variedade Riemanniana 10D**. Calcula o **Tensor de Ricci** para detectar rasgos na geometria — estresse extremo que pode causar colapso.

### Como Calcula (C++)
1. **Normalização L2:** Cada dimensão normalizada via Z-Score independente (Volume não esmaga Preço)
2. **Ricci Flow:** `deformation[i] = √(Σ Δ²)` sobre 10 dimensões
3. **Determinante Métrico:** `Π(1 + |Δ|)` — volume da variedade. Se < 0.05 → Colapso
4. **Danger Zones:** Z-Score janelado + EMA (α=0.15). Scores 0-100
5. **Entropia Bekenstein-Hawking:** `S = (A × G_ef) / (4 × L_planck²)`

### Retorno
- `deformation[]`, `determinant[]`, `danger_zones[]` (0-100), `is_collapsed` (bool), `holographic_entropy`

### Visual MT5
Caixas Dark Red `RGB(35,5,8)` no fundo. Intensidade proporcional ao danger_score.

---

## 3. LBM — LATTICE BOLTZMANN METHOD

| Campo | Valor |
|-------|-------|
| **C++** | `src/lbm/lbm_engine.cpp` (149 linhas) |
| **Python** | `fluid_dynamics.py` (148 linhas) |
| **Teoria** | Navier-Stokes + Lattice Boltzmann D1Q3 |
| **Objetivo** | Modelar mercado como fluido viscoelástico |

### O Que Faz
Grid 1D de 200 bins (faixa de preço). Cada vela injeta massa (volume) e momentum (direção do corpo). Fluido evolui via colisão BGK com **viscosidade dinâmica** responsiva à turbulência.

### Como Calcula (C++)
1. **D1Q3:** `f0` (estático), `f1` (bull/direita), `f2` (bear/esquerda)
2. **Injeção:** `inject_liquidity(idx, mass, momentum)` — momentum clampado ±0.3
3. **τ Dinâmico:** `τ_dyn = τ × (1 + e^(-KE_avg))`. Turbulência↑ → τ↓ → fluido ferve
4. **Decaimento:** `mass_decay = 0.995` por step
5. **Deborah Number:** `De = τ / t_anomalia`. Se `De > 1.2`: absorção viscoelástica

### Sinais
| Sinal | Condição |
|-------|----------|
| `FLUID_RUPTURE_BULL` | Z(ρ) > 3.5, velocity > 0.05, price > mid-range |
| `FLUID_RUPTURE_BEAR` | Z(ρ) > 3.5, velocity < -0.05, price < mid-range |
| `BOSONIC_SQUEEZE` | Z(ρ) > 3.2, |velocity| < 0.03 |
| `LAMINAR_FLOW` | Neutro |

### Visual MT5
Mini-círculos Wingdings: Teal `(38,166,154)` = Bull, Red `(239,83,80)` = Bear, Amber `(255,193,7)` = Squeeze.

---

## 4. SCHRÖDINGER — NUVEM DE PROBABILIDADE

| Campo | Valor |
|-------|-------|
| **C++** | `src/schrodinger/schrodinger_engine.cpp` (287 linhas) |
| **Python** | `quantum_clouds.py` (225 linhas) |
| **Teoria** | Eq. Schrödinger + Thomas Algorithm + PML + S-Matrix |
| **Objetivo** | Mapear distribuição de probabilidade do preço futuro |

### O Que Faz
Resolve a **Eq. de Schrödinger dependente do tempo** em grid 512-bin. Potencial V(x) gerado do perfil de volume (alto volume = poço gravitacional). `|ψ|²` = densidade de probabilidade do preço.

### Como Calcula (C++)
1. **Gaussiana Inicial:** Centrada no preço atual, `σ = dx × 12`
2. **Crank-Nicolson:** Método implícito 2ª ordem via Thomas Algorithm. Sub-steps adaptativos
3. **PML:** Bordas absorventes cúbicas `100 × frac³`
4. **Drift (Advecção):** `i·ħ·v_drift·∂ψ/∂x` empurra onda na direção do momentum
5. **Massa Espacial:** Zonas alto-volume → maior massa → onda desacelera
6. **Constante de Planck Dinâmica:** Baseada no ATR (evita underflow `exp(-600)`)
7. **S-Matrix:** `|S_fi|² = (coupling / (ΔE + coupling))²` — aniquilação de vácuos

### Métricas
- `singularity_strength` — Concentração máxima vs total
- `schwarzschild_radius` — Raio do horizonte de eventos
- `peak_price` — Preço no pico de probabilidade
- `tunneling_probability` — WKB de atravessar barreira

### Visual MT5
Heatmap de linhas horizontais: Crimson/Teal sutil. Largura = `density × 8`.

---

## 5. QGC — QUANTUM GRAVITY CONDENSATE

| Campo | Valor |
|-------|-------|
| **C++** | `src/qgc/qgc_engine.cpp` (83 linhas) |
| **Python** | `quantum_glass.py` (61 linhas) |
| **Teoria** | Quantum Liquidity Glass + Radiação Hawking |
| **Objetivo** | Mapear zonas de liquidez institucional que decaem no tempo |

### O Que Faz
"Order Blocks" são **Condensados de Vidro Amorfo** com **Radiação Hawking** (decaimento exponencial). Massa inicial ∝ volume. Evaporação acelerada se preço se afasta.

### Como Calcula (C++)
1. **Criação:** `add_zone(price, mass, time)`. Merge se já existir zona ±5 pts
2. **Evaporação:** `M(t) = M₀ × e^(-0.0002 × Δt × (1 + dist/100))`
3. **Poda:** Remove se `mass < 10%` da original
4. **Gravidade Plummer:** `pull = Σ(mass_i / √(dist² + 1.5²))`

### Scanner Python
- Z-Score volume > 1.5σ → nova zona
- Boot: scan 200 barras históricas para popular

### Visual MT5
Retângulos ultra-sutis `RGB(35,5,8)` com fitas de evaporação. Z-Order 0 (fundo).
