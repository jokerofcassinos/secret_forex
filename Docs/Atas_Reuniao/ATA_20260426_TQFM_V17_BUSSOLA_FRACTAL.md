# ATA DE REUNIÃO EXECUTIVA - UPGRADE TQFM v17 (A BÚSSOLA FRACTAL)

**Data:** 26 de Abril de 2026
**Local:** Ambiente Virtual Aethelgard (NEXUS-QUANT GER40)
**Pauta:** O Aprisionamento em Pullbacks Extremos e a Necessidade de uma Âncora Macroeconômica.

## 1. Relatório do Problema
A versão 16 ampliou o "Casco Macro" para 30 velas a fim de ignorar ruídos e micro-tendências. No entanto, o diagnóstico revelou que as ondas estavam se alongando além do topo/fundo real da tendência. Ao depender puramente de limites distantes de Price Action (como a máxima/mínima de 30 ou 40 velas), o mercado fazia o topo absoluto (V-Top) mas a Reversão Mágica frequentemente falhava em engatilhar, forçando o robô a manter o status BULL enquanto o mercado já desabava. Quando ele finalmente rompia a estrutura distante, o movimento BEAR começava atrasado, ignorando todo o lucro da queda inicial. As lateralizações longas (pullbacks de correção) também confundiam a máquina em topos/fundos locais de 30 velas, induzindo micro-BEARs.

## 2. Deliberação do Swarm

- **Setor Q-Math:** Price Action puro é excelente, mas o "Sweet Spot" de 15 velas para o ChoCH (Quebra de Estrutura) foi a métrica orgânica mais eficiente já testada. Aumentar para 30 velas só nos trouxe latência. Retornaremos o Pivô Estrutural para **15 velas**.
- **Setor N-Core (IA):** Para não sofrermos com os pullbacks (respiros) em uma janela de 15 velas, a IA precisa do **Alinhamento Institucional**. Reintroduzimos o conceito de "Bússola", mas utilizando a métrica institucional de Scalping: a **EMA 50 (O Fluxo Macro de 1 HORA no gráfico M1)**. A regra agora é implacável: se a IA está BULL, e o preço rompe o fundo de 15 velas, a IA olha para a EMA 50. Se o preço estiver ACIMA da EMA 50, ela sorri e diz *"É só um pullback profundo"* e se recusa a vender. Ela **só colapsa se perder o Fundo de 15 velas E furar a EMA 50**.
- **Setor R-Exec (Reversões Mágicas Instantâneas):** Para parar de perder a ponta exata das montanhas, deixamos a reversão mais flexível (sensível) e veloz. A janela de "Extremo Absoluto" caiu de 40 para **20 velas**. Se o preço atingir a máxima das últimas 20 velas ou o RSI passar de 70, e deixar um **Candle Engolfo de Baixa** (ou uma vela de força > 0.8x ATR rompendo o micro-pivô de 3 velas), o V-Top é confirmado. A máquina acerta a testa da montanha na mesma hora, ignorando a EMA 50 completamente, pois as reversões agudas ("Mean Reversion") acontecem muito antes do preço voltar para as médias.

## 3. Ações Implementadas
1. **Refatoração Dinâmica (TQFM v17 - A Bússola Fractal):** `advanced_regime_score` completamente redesenhado para simbiose de Price Action (Pivôs) + Tendência Relativa (EMA 50).
2. Substituição do "Casco Macro de 30" pelo `swing_low/high` de 15 velas condicionado à barreira `ema_macro` (50 períodos).
3. "Reversões Mágicas" sensíveis em zonas locais de **20 velas**, exigindo Engolfo de Price Action ou Força ATR.

## 4. Próximos Passos
Reiniciar ambiente. O robô agora unirá o melhor de dois mundos: A firmeza e frieza da "EMA 50" para ignorar consolidações (pullbacks falsos) e a hiper-sensibilidade do Price Action (`local_high_20` + Engolfo) para pegar a curva em "V" no exato momento de virada do mercado.

---
**Assinado:** NEXUS, AGI CEO