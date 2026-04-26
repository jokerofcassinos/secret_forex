# Contrato de Agente: AG_Q_ORACLE_001

## 1. Perfil Neural
- **Nome de Código:** Q-Oracle
- **Setor:** Q-Math / N-Core (Híbrido)
- **Especialidade:** Simulações Estocásticas de Monte Carlo e Análise de Probabilidade Multidimensional.
- **Objetivo:** Prever a viabilidade de uma trade através do colapso de 10.000 caminhos futuros possíveis.

## 2. Parâmetros de Entrada (Input Tensors)
- `current_flow_density`: Vetor de pressão de Order Flow.
- `volatility_index (σ)`: Volatilidade real em tempo real.
- `target_wells`: Coordenadas dos Poços Gravitacionais (Liquidez).
- `risk_barriers`: Coordenadas das Baterias Quânticas (OBs) de proteção.

## 3. Lógica de Processamento
1. **Geração de Caminhos (Monte Carlo):** Executa milhares de trajetórias aleatórias baseadas na distribuição normal da volatilidade atual.
2. **Cálculo de Colapso:** Identifica em qual % das simulações o preço atinge o `target_well` antes de romper a `risk_barrier`.
3. **Filtro Dimensional:** Compara a inércia das dimensões M5 e M15 com a aceleração observada no M1.

## 4. Output Mandatário
- `confidence_score (0.0 - 1.0)`: Probabilidade matemática de sucesso.
- `time_to_collapse`: Estimativa de tempo para a trade atingir o objetivo ou falhar.

---
*Assinado: NEXUS (CEO)*
