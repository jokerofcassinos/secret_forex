# ATA DE REUNIÃO EXECUTIVA - UPGRADE TQFM v75 (PROTOCOLO DE COLAPSO DE SOMBRA)

**Data:** 27 de Abril de 2026
**Local:** Ambiente Virtual Aethelgard (NEXUS-QUANT)
**Pauta:** Inércia Estrutural e Falha de Reversão no BTCUSD M1

## 1. Diagnóstico de Falha (NEXUS-AUDIT)
As imagens de satélite (screenshots do usuário) confirmaram que o TQFM v74 sofre de **Inércia Estrutural**. O regime BULL foi mantido durante uma queda de exaustão clara porque o preço permaneceu acima da mínima das últimas 30 velas (`swing_low_30`). O sistema priorizou a continuidade da tendência macro em vez de capturar o colapso da função de onda no topo.

## 2. Deliberação do Swarm

- **Setor Q-Math (Cinética):** Reduzir o horizonte de proteção de 30 para 20 velas. A inércia de 30 minutos em um gráfico de 1 minuto é excessiva para ativos de alta volatilidade.
- **Setor N-Core (Rede Neural):** Implementar o "Gatilho de Morte Súbita". Se o estado for BULL e detectarmos um `is_exhaustion_top` (sombra superior longa em topo local) ou um `bearish_engulfing`, o regime deve ser resetado para 0 (Neutro) imediatamente, preparando o sistema para um possível flip BEAR sem o atraso da confirmação estrutural.
- **Setor R-Exec (Gestão de Risco):** Validar que a saída prematura é preferível a devolver 80% do lucro da perna BULL esperando por uma quebra de suporte que só ocorre na base do movimento.

## 3. Ações Implementadas (v75)
1. **Refatoração:** `advanced_regime_score` no arquivo `quantum_indicators.py`.
2. **Novo Parâmetro de Horizonte:** `swing_low_20` e `swing_high_20` substituem os de 30 velas na lógica de manutenção de estado.
3. **Injeção de Colapso de Sombra:**
   - No estado BULL: Se (`is_exhaustion_top` OR `bearish_engulfing`) -> Retornar Neutro (0).
   - No estado BEAR: Se (`is_exhaustion_bottom` OR `bullish_engulfing`) -> Retornar Neutro (0).
4. **Refinamento do Flip:** O `flip_to_bear` agora aceita candles atômicos (1.1x ATR) se o momentum já for negativo, não exigindo apenas o super atômico (1.6x ATR).

## 4. Próximos Passos
Monitorar a agressividade das saídas. O objetivo é "matar" a operação no topo local, antes que o lucro evapore.

---
**Assinado:** NEXUS, AGI CEO