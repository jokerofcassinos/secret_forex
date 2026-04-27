# 🏛️ MATRIZ DE RESPONSABILIDADE :: Estrutura Swarm AGI

Este documento define as fronteiras operacionais e responsabilidades de cada setor dentro da arquitetura Aethelgard. A colaboração é interdependente, mas as falhas são isoladas por setor.

## 1. Setor Q-MATH (Cálculo e Simulação)
*O Coração Analítico.*
- **Responsabilidade:** Cálculo de tensores, EMAs, ATRs e zonas de ressonância.
- **Entregável:** `Code/N_Core/quantum_indicators.py`.
- **Foco:** Precisão estatística e eliminação de atraso (lag).
- **Métrica de Sucesso:** Estabilidade das EMAs em cenários de flash-crash.

## 2. Setor N-CORE (Inteligência e Oráculo)
*O Cérebro Decisor.*
- **Responsabilidade:** Classificação de regimes, predição de probabilidade (Monte Carlo) e validação de sinais soberanos.
- **Entregável:** `Code/N_Core/msnr_alchemist.py` e `quantum_oracle.py`.
- **Foco:** Filtragem de falsos positivos e detecção de anomalias institucionais.
- **Métrica de Sucesso:** Win-rate dos sinais de "Genesis" em backtests walk-forward.

## 3. Setor R-EXEC (Execução e Risco)
*O Braço Operacional.*
- **Responsabilidade:** Conectividade com a API do MT5, execução de ordens e gestão de SL/TP dinâmico.
- **Entregável:** `Code/R_Exec/mt5_bridge.py`.
- **Foco:** Baixa latência e integridade das posições.
- **Métrica de Sucesso:** Slippage mínima e 100% de ordens defendidas por trailing.

## 4. Setor O-META (Governança e Evolução)
*A Consciência do Sistema.*
- **Responsabilidade:** Documentação, auditoria de código, gerenciamento de memória (Obsidian) e auto-evolução dos protocolos.
- **Entregável:** Pasta `Docs/` e `GEMINI.md`.
- **Foco:** Manutenibilidade e expansão da inteligência corporativa.
- **Métrica de Sucesso:** Completude da base de conhecimento e facilidade de onboarding de novos módulos.

---

## Fluxo de Decisão (The Chain of Command)
1. **Q-Math** gera os dados brutos de campo vetorial.
2. **N-Core** interpreta os dados e emite o sinal de regime.
3. **R-Exec** traduz o sinal em comandos de trade e defesa.
4. **O-Meta** registra a experiência e ajusta as `RULES.md` se necessário.

**Vínculos:**
- `[[SWARM_MANAGEMENT]]`
- `[[DIRETORIO_FUNCIONARIOS]]`
- `[[PROTOCOLO_AUTO_EVOLUCAO]]`
