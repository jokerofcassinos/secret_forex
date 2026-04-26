# ATA DE REUNIÃO EXECUTIVA - UPGRADE TQFM v19 (APEX PREDATOR)

**Data:** 26 de Abril de 2026
**Local:** Ambiente Virtual Aethelgard (NEXUS-QUANT GER40)
**Pauta:** Resolução de Atrasos em Topos Arredondados e Otimização do Casco Estrutural.

## 1. Relatório do Problema
O TQFM v18 apresentou excelente estabilidade direcional e imunidade a ruídos curtos. No entanto, as evidências revelaram duas falhas sutis, porém onerosas, de "latência" e excesso de rigidez em inversões:
1. **O Paradoxo dos Topos Arredondados (Rounded Tops):** O gatilho de "Reversão Mágica" exigia que a vela contrária rompesse imediatamente o pivô de 3 velas. Em topos agudos (V-Tops perfeitos), isso funciona maravilhosamente. Porém, se o topo é arredondado ou demora a "virar" (Exaustão Lenta), o pivô de 3 velas se alarga demais e a reversão não engatilha. O resultado era o atraso na saída, forçando o preço a voltar muito antes de reverter a zona.
2. **Casco Excessivo (24 velas):** Em casos onde o topo arredondado não acionava a "Reversão Mágica", a IA tinha que esperar o preço derreter 24 velas para romper a "Estrutura Macro". Isso devolvia muito lucro de volta ao mercado antes da inversão. 

## 2. Deliberação do Swarm

- **Setor Q-Math:** Ajustamos a barreira macro. O Casco (ChoCH) foi reduzido de **24 velas** para **18 velas**. Em gráficos M1 de índices voláteis (GER40/US30), 18 minutos é o *Sweet Spot* definitivo que cria um casco duro contra falsos pullbacks (não quebra em micro ruídos de 15 minutos) mas não é lento como o de 24 velas.
- **Setor N-Core (IA):** Retiramos as "amarras" das Reversões Mágicas! O "Predador de Topos" (Apex Predator) não exige mais a confirmação de quebra de micro-pivôs de 3 velas. A confirmação se tornou **puramente candelástica**. 
- **Setor R-Exec (Risco):** Se o preço tocou no Extremo (máxima de 40) ou a Força subiu ao espaço (RSI > 75 nas últimas 5 velas) e nesse exato cenário o gráfico pintar um autêntico **Engolfo de Baixa** (ou choque brutal > 1.0 ATR), A REVERSÃO É IMEDIATA. O sistema crava o topo no instante em que o *Price Action* denota esgotamento, sem esperar para ver se vai "romper as 3 velas".

## 3. Ações Implementadas
1. **Refatoração (TQFM v19 - Apex Predator):** O arquivo `quantum_indicators.py` foi lapidado.
2. Destruição do gatekeeper `curr['close'] < low_3` para reversões mágicas.
3. Substituição da janela estrutural `swing_high/swing_low` de `[-25:-1]` (24 velas) para `[-19:-1]` (18 velas).
4. Otimização da exaustão térmica para leitura do RSI máximo nas últimas 5 velas (`rsi_max_5 > 75` e `rsi_min_5 < 25`).

## 4. Próximos Passos
O Tsunami agora possui o bote letal. Ao farejar um topo exausto que engolfa para baixo, a onda é quebrada de imediato. E se for um declive sem engolfo (sem Reversão Mágica), a nova estrutura de 18 velas inverterá a polaridade mais rápido, mitigando as perdas excessivas no *lag* estrutural.

---
**Assinado:** NEXUS, AGI CEO