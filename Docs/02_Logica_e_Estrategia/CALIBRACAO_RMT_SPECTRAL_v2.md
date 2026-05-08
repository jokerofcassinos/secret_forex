# 🔬 Calibração Espectral RMT v2.0 (Teoria de Matrizes Aleatórias)
**Módulo: N-Core Spectral Noise Reduction**

## 1. O Paradigma do Ruído (Marchenko-Pastur)
O mercado não é apenas preço; é uma sobreposição de fluxos de informação. O RMT v2.0 utiliza a distribuição de **Marchenko-Pastur** para definir o horizonte de eventos do ruído randômico. 

$$ \lambda_{\pm} = \sigma^2 \left( 1 \pm \sqrt{\frac{1}{Q}} \right)^2 $$

Onde $Q = T/N$ (Tempo / Dimensões). Qualquer autovalor acima de $\lambda_{+}$ é considerado **Sinal Puro (Driver Institucional)**.

## 2. Expansão para 8 Dimensões (v2.0)
Diferente da versão anterior (6D), o RMT v2.0 agora funde a física de fluidos com a estatística espectral:
1.  **Retornos Logarítmicos** (Preço)
2.  **Spread High-Low** (Volatilidade Bruta)
3.  **Tick Volume** (Massa)
4.  **Corpo da Vela** (Momentum)
5.  **Pavios Superiores** (Rejeição de Oferta)
6.  **Pavios Inferiores** (Rejeição de Demanda)
7.  **Entropia de Volatilidade** (Z-Score de ATR) - *NOVO*
8.  **Velocidade Cinética LBM** (Fluxo de Fluido) - *NOVO*

## 3. Aceleração Multi-Core (OpenMP)
Para gerenciar a matriz de correlação 8x8 em tempo real, o motor C++ foi otimizado com diretivas de paralelismo:
- **Cálculo de Covariância**: Paralelizado via `#pragma omp parallel for`.
- **Power Iteration**: Otimizado para convergência em sub-milissegundos.

## 4. Rigor Operacional
O threshold de decisão foi elevado de `2.5x` para `3.0x`. 
- **Noise**: $Power Ratio < 1.0$
- **Weak Signal**: $1.0 < Power Ratio < 3.0$
- **PURE SIGNAL**: $Power Ratio > 3.0$ (Ativação Institucional Confirmada)

## 5. Auditoria Visual (Real-Time)
Abaixo, o registro do espectro capturado durante a calibração final:
![Auditoria RMT v2.0](file:///d:/AI%20Brain/US30/Docs/03_Ambiente_Executivo/RMT_Spectral_Audit_RealTime.png)

---
**NEXUS ONLINE.** *O espectro do mercado foi decodificado.*
