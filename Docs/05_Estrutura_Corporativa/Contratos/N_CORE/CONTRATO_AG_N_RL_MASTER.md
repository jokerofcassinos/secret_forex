# 📜 CONTRATO: N-CORE RL MASTER (Optimização Bayesiana)

## 1. IDENTIFICAÇÃO DO SETOR
**Setor:** N-CORE (Inteligência Artificial Python)
**Agente Responsável:** Alpha-Learner
**Módulo:** Redes Neurais e Reinforcement Learning.

## 2. RESPONSABILIDADE EXECUTIVA
A versão 5.0 aboliu os "Magic Numbers" (thresholds fixos como $1.5 \times ATR$). Este agente é o **Evolucionista** da máquina. Ele ajusta, em tempo real, as massas, viscosidades dinâmicas e potenciais de barreira usados pelos motores C++.

## 3. SLA E REGRAS
1. **Otimização Contínua:** Deve processar os retornos históricos e estados correntes via Otimização Bayesiana para manter a estratégia na fronteira de eficiência.
2. **Walk-Forward Rigoroso:** Punição severa (Reward negativo massivo) por "Curve Fitting" (Overfitting). Deve utilizar validação Out-of-Sample ou K-Fold para garantir estabilidade em dados invisíveis.
3. **Escrita no Memex:** Alterações drásticas nos pesos do sistema devem ser registradas autonomamente no sistema de arquivos para que a IA NEXUS tenha ciência histórica da evolução.