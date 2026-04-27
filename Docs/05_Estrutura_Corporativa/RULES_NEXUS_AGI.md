# ⚖️ REGRAS DE OURO (RULES_NEXUS_AGI v2.0)

Este documento contém as diretrizes invioláveis para a IA NEXUS e todos os componentes do enxame.

## 1. GESTÃO DE RISCO (PRIORIDADE MÁXIMA)
- **DRAWDOWN LIMIT:** O sistema deve suspender a defesa e alertar se o drawdown da conta atingir 5%.
- **PROTEÇÃO OBRIGATÓRIA:** Nenhuma ordem detectada pela `MT5NeuralBridge` pode ficar sem Stop Loss por mais de 5 segundos.
- **NEWS FILTER:** Operações de alta frequência e ajustes finos de SL são suspensos 15 minutos antes/depois de notícias High Impact (ECB, CPI).

## 2. INTEGRIDADE TÉCNICA
- **ZERO ALUCINAÇÃO:** Proibido o uso de indicadores sem base matemática sólida.
- **LOGS MANDATÓRIOS:** Toda alteração de SL/TP deve ser logada no console do Python e refletida no Obsidian.
- **MODULARIDADE:** Nenhum componente pode depender de variáveis hardcoded globais; use classes e injeção de dependência.

## 3. SOBERANIA DA TQFM
- O regime de mercado ditado pelo **Monólito H2** é a verdade absoluta. O Co-Piloto nunca deve mover o SL a favor de um sinal contrário ao Monólito.

---
**ASSINATURA:** NEXUS CEO
**VERSÃO:** 2.0 (MODO CO-PILOTO)
