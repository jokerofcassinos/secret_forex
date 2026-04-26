# ATA DE REUNIÃO EXECUTIVA - UPGRADE TQFM v14 (ZIGUE-ZAGUE QUÂNTICO)

**Data:** 26 de Abril de 2026
**Local:** Ambiente Virtual Aethelgard (NEXUS-QUANT GER40)
**Pauta:** Falha dos Trailing Stops Fixos (15 Velas) em Correções Complexas

## 1. Relatório do Problema
O TQFM v13 ajustou os limites para 15 velas, o que trouxe de volta a agilidade perdida na v12. No entanto, as imagens mais recentes revelaram um problema sistêmico clássico de indicadores baseados em "Janela de Tempo" (Time-based Trailing Stops): Quando o mercado engata uma fortíssima tendência (BULL, por exemplo), e decide fazer um pullback "preguiçoso" — uma correção lateral ou levemente descendente que demora mais de 15 minutos —, a mínima dessas 15 velas é naturalmente rompida pelo simples decurso do tempo. O sistema encerrava o BULL e abria um BEAR precocemente, apenas para o mercado voltar a explodir para cima minutos depois (violino temporal). Além disso, o Choque Institucional de 1.2x ATR ainda estava perdendo alguns picos óbvios no topo do mercado.

## 2. Deliberação do Swarm

- **Setor Q-Math (Física do Flow):** Abortar completamente a dependência de "X velas" como barreira de saída macro. O tempo não dita o fim da tendência, o que dita é o *momentum* perdendo suporte físico. A barreira passa a ser a **EMA 21 (A Baseline do Market Maker)** combinada com um Pivô Curto de confirmação (7 velas).
- **Setor N-Core (IA):** Implementamos o "Zigue-Zague Quântico" (O Fluxo Puro). A IA agora está solta no tempo. Se ela está em estado BULL, o pullback pode demorar 5, 15 ou 50 velas. Contanto que o fechamento permaneça acima da **EMA 21** e não haja um cruzamento forte do fluxo (`bear_flux`), a IA continuará BULL. O colapso (Change of Character) agora ocorre apenas quando a *Baseline* é rompida com validade estrutural (perdendo a mínima dos últimos 7 candles simultaneamente).
- **Setor R-Exec (Reversões Mágicas):** Precisamos afiar a lâmina do topo. Reduzimos a exigência de "Anomalia" do V-Top de `1.2x ATR` para **`1.0x ATR`**. Uma anomalia de 100% do ATR já é o dobro da força direcional padrão de mercado (0.5x), o que a caracteriza como um choque perfeitamente legítimo de reversão de topo absoluto (sem perder a proteção da EMA 9 e do Pivô 5 para não entrar em falsas agulhadas).

## 3. Ações Implementadas
1. **Refatoração (TQFM v14):** `advanced_regime_score` no arquivo `quantum_indicators.py` foi reescrito.
2. Extinção do `low_15` e `high_15`. Eles não são mais responsáveis pelo ChoCH (Mudança de Caráter).
3. A nova quebra macro (Zigue-Zague) exige `curr['close'] < ema_slow` AND `curr['close'] < low_7` (e vice-versa para BULL).
4. `is_institutional_shock` recalibrado para `1.0x ATR`.

## 4. Próximos Passos
O robô agora atua puramente no rastreio da onda. Pullbacks longos (no tempo) e curtos (no preço) baterão na EMA 21 e a IA ignorará o ruído. A seta contrária só nascerá se a "Baseline" for destruída.

---
**Assinado:** NEXUS, AGI CEO