# 🛡️ MANUAL DE SISTEMAS AETHELGARD — PARTE 5
**Adaptive Neural Zones (ANZ) · Sincronização MT5 · Telemetria Expandida**

---

## 28. ADAPTIVE NEURAL ZONES (ANZ) — GESTÃO DE RISCO QUÂNTICA

| Campo | Valor |
|-------|-------|
| **Arquivo** | `Code/N_Core/virtual_neural_zones.py` (116 linhas) |
| **Classe** | `AdaptiveNeuralZones` |
| **Teoria** | PreCognition Monte Carlo (SL) + QTE Tunneling (TP) + QHO Trailing |
| **Objetivo** | Substituir TP/SL estáticos por zonas de contenção probabilísticas dinâmicas |

### O Que Faz
O Motor ANZ é a **última fronteira antes da execução**. Ele rastreia todas as posições (virtuais e reais) e calcula a cada tick:
- **Stop Loss Absoluto** — via PreCognition (500 simulações Monte Carlo C++)
- **Take Profit Dinâmico** — via probabilidade de Tunelamento Quântico (QTE)
- **Trailing Adaptativo** — via Shells de Energia Harmônica (QHO)
- **Ações de Saída** — quando as barreiras são violadas

### Estrutura de Dados Interna
```python
self.active_positions = {
    "444671590": {     # Ticket real do MT5
        "setup": "S1_GRAVITATIONAL_SLINGSHOT",
        "direction": "LONG",
        "entry_price": 80336.95,
        "highest_price": 80400.00,  # Tracking para trailing
        "lowest_price": 80336.95
    },
    "virt_1746781234": { # Posição virtual (setup detectado)
        "setup": "S7_TSUNAMI_MACRO",
        "direction": "LONG",
        "entry_price": 80279.35,
        ...
    }
}
```

---

## 29. MECÂNICA DE CÁLCULO DO ANZ

### 29.1 Stop Loss — PreCognition (Base Universal)
Para **toda** posição, o SL base vem do PreCognition:
- **LONG:** `precog_sl_long` = percentil 5% de 500 simulações de colapso
- **SHORT:** `precog_sl_short` = percentil 95% de 500 simulações de colapso

> [!IMPORTANT]
> O PreCognition é a "parede absoluta". Nenhum override de setup pode empurrar o SL para ALÉM dele (somente para mais perto, tornando-o mais apertado).

### 29.2 Take Profit — QTE Tunneling (Saída por Exaustão)
O TP não é um "alvo fixo". É a probabilidade de o preço **atravessar** a próxima barreira de liquidez:

| QTE Prob | Interpretação | Ação |
|----------|---------------|------|
| `> 0.85` | Preço com força para atravessar | HOLD |
| `0.15 - 0.85` | Zona de incerteza | HOLD |
| `< 0.15` | Preço vai ricochetear | **EXIT_QTE_BOUNCE** |

### 29.3 Ações de Saída Possíveis
| Ação | Gatilho | Descrição |
|------|---------|-----------|
| `HOLD` | Default | Posição mantida |
| `EXIT_QTE_BOUNCE` | `qte_prob < 0.15` | Tunelamento falhou, fechar com lucro |
| `EXIT_SL_TRAILING` | Preço cruzou SL ajustado | Trailing do QHO shell atingido |
| `EXIT_MACRO_BREAK` | QDD inverteu | Decoerência dimensional (macro virou) |
| `EXIT_QDD_REVERSAL` | `|QDD| > 0.5` contra | Reversão abrupta confirmada por QDD |

---

## 30. OVERRIDES POR SETUP (GESTÃO ESPECÍFICA)

### S7_TSUNAMI_MACRO — Surfar a Onda até Quebrar
```
SL: max(PreCognition, QHO shell n=3)  ← Trailing dinâmico
TP: 0.0 (INFINITO)                    ← Sem alvo fixo, surfa até EXIT_QTE_BOUNCE
Saída Extra: QDD decoerência (EXIT_MACRO_BREAK)
```
O S7 é o mais agressivo. Ele **não tem Take Profit** fixo. A posição fica aberta por dias/semanas até que o QTE sinalize exaustão (`< 0.15`) ou o QDD inverta o emaranhamento dimensional.

O SL usa trailing pelo shell QHO n=3 (o 4º harmônico), que é dinamicamente mais apertado que o PreCognition. Protege o lucro conforme o preço avança.

### S4_HARMONIC_RESONANCE — Pullback Simétrico
```
SL LONG:  max(PreCognition, price - 4×ATR)
SL SHORT: min(PreCognition, price + 4×ATR)
TP LONG:  price + 2×ATR
TP SHORT: price - 2×ATR
```
O S4 é conservador. Usa um TP fixo de 2 ATR (R:R = 1:2 com SL de 4 ATR mínimo). Ideal para entradas em pullback dentro de tendência.

### S5_TOPOLOGICAL_COLLAPSE — Ignição Imediata
```
SL LONG:  max(PreCognition, entry_price - 1.5×ATR)
SL SHORT: min(PreCognition, entry_price + 1.5×ATR)
TP: via QTE bounce
Saída Extra: QDD reversal (|QDD| > 0.5 contra)
```
O S5 é o mais apertado. Confia na ignição imediata pós-colapso topológico. Se não explodir imediatamente, sai rápido.

### S1_GRAVITATIONAL_SLINGSHOT — Gestão Adaptativa QDD
```
SL: PreCognition puro (sem override)
TP LONG:  entry + (3.0 + |QDD| × 4.0) × ATR
TP SHORT: entry - (3.0 + |QDD| × 4.0) × ATR
```
O S1 é aplicado automaticamente a **ordens manuais** do MT5. O TP flutua de 3 a 7 ATR com base na fidelidade do emaranhamento quântico (QDD). Se o mercado estiver coerente (`QDD ≈ 1.0`), o TP expande; se estiver caótico, contrai.

> [!TIP]
> **Ordens manuais** abertas pelo humano no MT5 recebem automaticamente a gestão `S1_GRAVITATIONAL_SLINGSHOT`. O Swarm detecta qualquer ordem real e a injeta na ANZ a cada tick.

---

## 31. SINCRONIZAÇÃO HÍBRIDA MT5 ↔ ANZ

### Fluxo a Cada Tick
```
1. mt5.positions_get(symbol)         → Lista posições REAIS abertas
2. Para cada posição real:
   - Se NÃO está na ANZ → register_position(ticket, "S1_...", dir, open_price)
   - Se JÁ está → mantém (tracking de highest/lowest continua)
3. Para cada posição na ANZ:
   - Se NÃO é virtual E NÃO existe mais no MT5 → remove (já foi fechada)
4. Se Setup Engine disparou novo sinal:
   - register_position("virt_TIMESTAMP", setup_name, dir, current_price)
5. evaluate_zones(ctx, current_price) → calcula SL/TP para TODAS
6. Se action ≠ "HOLD":
   - Virtual: apenas remove da ANZ
   - Real: bridge.close_position(ticket) + remove da ANZ
```

### Segurança
- O Python envia `mt5.order_send()` via `MT5NeuralBridge.close_position()` para fechar ordens reais
- O SL "catastrófico" da corretora (mais largo que o SL quântico) é mantido como backup offline
- Se o computador desligar, a corretora fecha no SL catastrófico; se o Python estiver online, ele fecha antes

---

## 32. TELEMETRIA EXPANDIDA (ANZ → HUD)

### Formato do Payload
```
setupTel = "S3_BOSONIC_IGNITION:LONG:C3|S7_TSUNAMI_MACRO:LONG:C3|78102.97|82679.75"
                                                                    ↑ SL      ↑ TP
```
Os **dois últimos campos** após o último `|` são sempre o SL e TP dinâmicos da ANZ.

### Parsing no MQL5 (Nexus_Observer.mq5)
```cpp
string sParts[]; StringSplit(setupTel, '|', sParts);
int nParts = ArraySize(sParts);
anzSl = StringToDouble(sParts[nParts-2]);  // Penúltimo = SL
anzTp = StringToDouble(sParts[nParts-1]);  // Último = TP

// Reconstrói string limpa para DrawSetupSignal
string cleanSetup = sParts[0];
for(int x=1; x < nParts-2; x++) cleanSetup += "|" + sParts[x];
```

### Renderização Visual
| Objeto | Nome | Tipo | Cor | Estilo |
|--------|------|------|-----|--------|
| Stop Loss Quântico | `NEXUS_ANZ_SL` | `OBJ_HLINE` | `RGB(220, 20, 60)` Crimson | DASHDOT |
| Take Profit Quântico | `NEXUS_ANZ_TP` | `OBJ_HLINE` | `RGB(0, 255, 255)` Cyan | DASHDOT |

As linhas são horizontais infinitas, atualizadas a cada tick. Quando `anzSl < 0.1` ou `anzTp < 0.1`, o objeto é deletado (sem posição ativa).

---

## 33. CAMPOS ADICIONAIS DA nexus_data_str

A parte 3 listou campos 0–38. Os novos campos adicionados:

| Index | Nome | Conteúdo | Exemplo |
|-------|------|----------|---------|
| 39 | `setupTel` | Setups ativos + SL/TP ANZ | `S3_...:LONG:C3\|78102.97\|82679.75` |
| 40 | `setupHistory` | CSV do cache histórico (±N) | `0,0,3,0,-7,0,3,0,...` |

---

## 34. FLUXO COMPLETO COM ANZ

```
MT5 (Preço + Posições Reais)
  ↓
Aethelgard_Swarm.py
  ├─ q_math_node (7 threads C++)
  ├─ QuantumSetupEngine.evaluate()     → Detecta setups ativos
  ├─ mt5.positions_get()               → Sincroniza ordens reais
  ├─ AdaptiveNeuralZones
  │   ├─ register_position()           → Injeta ordens reais/virtuais
  │   ├─ evaluate_zones()              → Calcula SL/TP dinâmicos
  │   └─ action ≠ HOLD?               → Fecha via bridge ou remove virtual
  ├─ MT5NeuralBridge
  │   ├─ thermodynamic_sl_tp()         → SL catastrófico na corretora
  │   └─ close_position()              → Execução de fechamento real
  └─ Monta nexus_data_str (42 campos)
      ↓ TCP Socket
  Nexus_Observer.mq5
    ├─ ParseAndDraw()                  → Renderiza tudo
    ├─ NEXUS_ANZ_SL (Crimson HLINE)    → Stop Loss visual
    ├─ NEXUS_ANZ_TP (Cyan HLINE)       → Take Profit visual
    └─ DrawSetupSignal()               → Diamantes e labels dos setups
```

---

> [!CAUTION]
> **O Motor ANZ opera em modo de GESTÃO, não de EXECUÇÃO automática.** Ele calcula as zonas e fecha posições que violam as barreiras, mas **NÃO abre posições automaticamente.** A abertura de ordens reais é uma prerrogativa exclusiva do operador humano (Diretriz de Segurança de Boot — Modo Manual).

---

> [!NOTE]
> **Versão:** Manual de Sistemas Aethelgard Part 4 + Part 5 — Documentação completa do Quantum Setup Engine v2.0 e Adaptive Neural Zones v1.0. Gerado em 2026-05-09.
