# 📜 CONTRATO: Q-MATH LBM ENGINE (Lattice Boltzmann)

## 1. IDENTIFICAÇÃO DO SETOR
**Setor:** Q-MATH (Motor C++)
**Agente Responsável:** Hydro-Core
**Módulo:** `lbm_engine.cpp` e wrappers Python.

## 2. RESPONSABILIDADE EXECUTIVA
Este agente é o guardião do **Monólito Macro**. Sua única missão é resolver as equações cinéticas dos fluxos de transações (preço e volume do GER40 em H2) para calcular a Pressão Hidrodinâmica do mercado.

## 3. SLA E REGRAS
1. **Latência Zero:** O processamento matricial deve rodar em C++ e interagir com Python de forma nativa e sem gargalos de GIL.
2. **Imunidade a Lag:** Proibido o uso de janelas históricas de médias (EMAs) que induzem atraso. O estado é calculado com base no tensor de stress e momento do fluxo.
3. **Output:** Deve entregar ao Córtex (N-Core) um vetor de campos de velocidade indicando a direção e a força (viscosidade) da tendência de forma ininterrupta.