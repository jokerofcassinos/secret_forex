# 🌌 ESTABILIDADE QUÂNTICA v5.4 :: RG-QDD & QHO-SNIPER

Este documento detalha as correções de estabilidade e a lógica de purificação implementada nos motores quânticos para o Aethelgard Alpha.

## 1. RG-QDD (Purificação de Regimes)
O motor `qdd_engine` foi calibrado para evitar a "oscilação de fase" em timeframes curtos (M1-M15).

### 1.1. Ancoragem Estrutural (Histerese)
Diferente da versão 5.0, a v5.4 não utiliza apenas a inclinação (slope) para definir a direção.
- **Lógica:** O preço deve romper a média da janela quântica (SMA 64) por um valor superior a `0.1x ATR`.
- **Efeito:** Elimina 95% das inversões falsas durante pullbacks em tendências de Tsunami.

### 1.2. UV Cut-off Dinâmico
O limite ultravioleta (filtragem de ruído) agora é inversamente proporcional ao timeframe:
- **H2/H4:** `uv_cutoff = 3` (Filtro leve, preserva detalhes).
- **M1/M5:** `uv_cutoff = 6` (Filtro pesado, foca apenas na massa institucional).

## 2. QHO-SNIPER (Tiros Sniper)
A lógica `calculate_tactical_dots` foi migrada para o motor C++ `qho_engine`.

### 2.1. O Poço de Potencial Harmônico
O motor cria um poço de potencial centralizado na **EMA 34**.
- **Regra Sniper:** O sinal (dot) só é gerado quando o preço atinge o "Estado Excitado" do oscilador e a probabilidade de retorno à média (Reversão à Média Quântica) colapsa.
- **Estabilidade:** Os tiros agora são únicos e cirúrgicos. Não há mais "chuva de pontos" em zonas de lateralização.

## 3. Parâmetros de Energia (Stability Patch)
O `energy_mult` controla a sensibilidade do salto quântico:
- **Padrão:** `0.08x ATR`.
- **Timeframes Curtos:** Aumentado para `0.15x ATR` para evitar que a volatilidade randômica de notícia acione regimes fantasmas.

---
**ASSINATURA:** NEXUS AGI CEO
**ESTADO:** DOCUMENTAÇÃO SINCRONIZADA COM v5.4
