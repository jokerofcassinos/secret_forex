# BLUEPRINT ARQUITETURAL: DINÂMICA DE FLUIDOS (LATTICE BOLTZMANN)
**Setor:** Q-MATH (Engenharia Quântica & C++)
**Projeto:** Aethelgard (GER40)
**Fase:** V2.0 - Termodinâmica de Ruptura (Squeezes)

## 1. Fundamentação Teórica
O mercado não é apenas uma série temporal de preços, mas um **fluido compressível** confinado em um duto unidimensional (a escala de preço). Compradores e vendedores são partículas colidindo. Quando há muita compressão de liquidez (baixa volatilidade com alto volume) e a pressão direcional aumenta, ocorre o rompimento da tensão superficial. Isso no mercado é chamado de *Squeeze Institucional* ou *Stop Hunt*.

A equação Navier-Stokes tradicional é pesada para cálculos instantâneos. Portanto, utilizaremos a mecânica estatística clássica: o **Lattice Boltzmann Method (LBM)**.

### 1.1. O Modelo D1Q3 (1 Dimensão, 3 Velocidades)
Modelaremos o preço em uma grade unidimensional. Em cada nó (nível de preço), as "partículas de liquidez" têm 3 vetores de velocidade direcional ($e_i$):
*   $e_0 = 0$ (Partículas paradas / Ordens Limit)
*   $e_1 = +1$ (Partículas movendo para cima / Ordens a Mercado Buy)
*   $e_2 = -1$ (Partículas movendo para baixo / Ordens a Mercado Sell)

## 2. A Matemática da Colisão e Propagação (BGK)
A evolução do sistema ocorre em dois passos:
1.  **Colisão (Bhatnagar-Gross-Krook - BGK):** As partículas interagem e tendem ao equilíbrio Maxwelliano. Se entram muitas ordens de compra e venda no mesmo nível, a colisão gera entropia (ruído) e aumenta a densidade local $\rho$.
    $$ f_i(x, t+\Delta t) = f_i(x,t) - \frac{1}{\tau} [f_i(x,t) - f_i^{eq}(x,t)] $$
    *Onde $\tau$ é o tempo de relaxamento (viscosidade do mercado).*
2.  **Streaming (Propagação):** As ordens a mercado ($e_1$ e $e_2$) movem as partículas para os nós de preço adjacentes no próximo passo de tempo.

### 2.1. Variáveis Macroscópicas de Saída
A partir das distribuições microscópicas $f_i$, o C++ calculará variáveis macroscópicas físicas para o Python:
*   **Densidade Local ($\rho$):** $\rho = f_0 + f_1 + f_2$. Análogo ao *Heatmap de Volume*, mas termodinâmico e reativo.
*   **Velocidade Direcional ($u$):** $u = (f_1 - f_2) / \rho$. Mostra o "Vetor de Agressão" do Order Flow.
*   **Pressão ($P$):** Relacionada com a densidade. *Zonas de alta pressão onde a velocidade direcional explode preveem Squeezes letais.*

## 3. Integração (N-Core -> Q-MATH)
1. O N-Core (Python) injeta "massa" $\Delta\rho$ (Tick Volume) nos níveis de preço onde o candle fechou, associando momento direcional dependendo de o candle ser verde ($e_1$) ou vermelho ($e_2$).
2. A Engine C++ (`lbm_engine.cpp`) processa milhares de ciclos de colisão/streaming, simulando como o fluido reage.
3. O N-Core observa picos de $u$ (Velocidade) em zonas de alta $\rho$ (Densidade). O Python retornará o Sinal: **"FLUID_RUPTURE"** apontando a direção da agressão institucional escondida.

---
**Assinado:** NEXUS, AGI CEO
**Aprovação:** Protocolo AGI-5 (Superposição Termodinâmica Validada).
