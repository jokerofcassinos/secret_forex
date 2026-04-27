# 🌌 TQFM DEEP DIVE :: Teoria Quântica de Fluidos de Mercado (v2.0)

## 1. O Monólito Macro: Inércia Termodinâmica
O **Monólito Macro** é a base da estabilidade do sistema Aethelgard. Diferente de sistemas de cruzamento convencionais, ele utiliza uma ancoragem em **H2 (120 min)** para filtrar o ruído estocástico do mercado.

### 1.1. Equação de Convergência
A detecção de regime ($R$) é definida pela relação entre a Média Móvel Exponencial Rápida ($\text{EMA}_{34}$) e a Média Móvel Exponencial Macro ($\text{EMA}_{89}$).

$$
R(t) = \begin{cases} 
1 \text{ (Bull)} & \text{if } \text{EMA}_{34}(t) > \text{EMA}_{89}(t) + \delta \\
2 \text{ (Bear)} & \text{if } \text{EMA}_{34}(t) < \text{EMA}_{89}(t) - \delta \\
0 \text{ (Neutro)} & \text{otherwise}
\end{cases}
$$

Onde $\delta = 0.5 \times \text{ATR}_{14}$ atua como um **Noise Gate Terminal**, impedindo o *flicker* (oscilação rápida) em zonas de equilíbrio.

### 1.2. Imunidade de Regime (Maturidade)
Para evitar saídas precoces em pullbacks violentos, o Monólito aplica uma **Imunidade de Maturidade** ($\Phi$):
$$ \Phi(c) = \text{True} \iff c > 20 \text{ velas} $$
Durante o período $c \le 20$, o regime é cego a sinais de reversão, a menos que ocorra uma **Singularidade de Velocidade Sideral** ($\text{EMA}_{21}$ cruzando $\text{EMA}_{89}$ com choque $> 1.5\text{x ATR}$).

---

## 2. Atomic Shocks: A Geometria da Ignição
Os **Choques Atômicos** são anomalias institucionais onde o volume e a volatilidade colapsam em uma única direção, criando zonas de desequilíbrio de liquidez.

### 2.1. Thresholds de Massa Crítica
Um choque é classificado pela magnitude do corpo do candle ($B$) em relação à volatilidade média ($\text{ATR}$):
- **Ignition Shock:** $B > 0.9 \times \text{ATR}$
- **Atomic Shock:** $B > 1.1 \times \text{ATR}$
- **Super Atomic Shock:** $B > 1.6 \times \text{ATR}$

### 2.2. Zonas de Ressonância Estacionária (S.R.Z)
Quando um Atomic Shock ocorre, ele gera uma `[[CONCEITO_FRACTAL_SRF|S.R.Z]]`. Esta zona atua como uma muralha de interferência. O regime só é considerado "Soberano" se o preço se mantiver acima/abaixo da zona de choque.

---

## 3. Probability Wave Collapse: Trailing Dinâmico
O fechamento de uma posição não é um evento fixo, mas o **Colapso da Nuvem de Probabilidade**.

### 3.1. Função de Escudo Termodinâmico
O Stop Loss ($SL$) evolui como uma função do tempo e da tendência:
$$ SL_{bull} = \text{EMA}_{34} - (1.5 \times \text{ATR}) $$
$$ SL_{bear} = \text{EMA}_{34} + (1.5 \times \text{ATR}) $$

### 3.2. Colapso de Emergência
Se o regime $R(t)$ inverte contra a posição ativa ($\text{ex: Position=Buy e } R=2$), a função de defesa executa o **Aperto de Sombra**:
$$ SL_{emergency} = P_{current} \pm (0.5 \times \text{ATR}) $$
Isso garante que o lucro acumulado seja protegido antes que a reversão macro se complete.

---

## 4. Conclusão Arquitetural
A TQFM v2.0 transforma o gráfico em um campo vetorial de forças. O Monólito fornece a direção da maré, os Atomic Shocks fornecem os pontos de entrada, e o Trailing dinâmico gerencia a entropia da posição.

**Vínculos:**
- `[[ROADMAP_EXECUCAO]]`
- `[[DIMENSOES_TEMPORAIS]]`
- `[[STATE_GER40_CASH]]`
