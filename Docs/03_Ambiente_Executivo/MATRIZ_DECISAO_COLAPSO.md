# MATRIZ DE COLAPSO DE FUNÇÃO DE ONDA (Gatilhos BUY / SELL)
**Classificação:** Confidencial / Setor R-Exec & N-Core
**Objetivo:** Definir a lógica booleana exata que determina o sentido do vetor de execução (Comprar ou Vender).

A decisão de apertar o botão não se baseia em adivinhar o mercado, mas em observar o alinhamento de tensores no nosso painel de telemetria. 

O único timeframe que detém a "Autoridade de Colapso" (O gatilho final) é o **H2**. Os outros timeframes (M15, H1) funcionam como sistemas de alerta antecipado.

---

## 1. O VETOR DE COMPRA (BUY SIGNAL / LONG)

Para o sistema (ou você) acionar um `BUY`, o painel deve exibir um dos dois cenários abaixo no fractal **H2**:

### Cenário A: Expansão Laminar Pura (Rompimento a Favor da Correnteza)
Este é o trade direcional clássico, onde não há manipulação detectada.
*   **Regime (H2):** `Bull Tsunami`
*   **Flag TRAP:** Ausente (Não pode haver `[TRAP]`).
*   **Confiança (H2):** Maior que `80%`.
*   **LBM Flow (Q-Math):** `Laminar Flow`.
*   *Lógica:* A macroestrutura está subindo (Bull Tsunami), o fluxo interno de fluidos confirma a direção (Laminar Flow) e as redes neurais confiam no movimento (>80%). 

### Cenário B: Rebote em Anomalia (A Caça aos Ursos)
Este é o trade onde operamos a manipulação institucional. Ocorre geralmente em fundos.
*   **Regime (H2 ou H1):** `Bear Tsunami [TRAP]` (Atenção ao `[TRAP]`).
*   **LBM Flow (Q-Math):** `Squeeze Bull`.
*   **Confiança M15:** Caindo a `0.0%` (A queda perdeu toda a força microscópica).
*   *Lógica:* O mercado aparenta estar derretendo (Bear Tsunami), atraindo vendedores. Contudo, a flag `[TRAP]` acende e a física dos fluidos (Squeeze Bull) revela que a pressão termodinâmica interna é de ALTA. O preço vai explodir para cima para estopar os vendedores. Você executa um **BUY**.

---

## 2. O VETOR DE VENDA (SELL SIGNAL / SHORT)

Para o sistema (ou você) acionar um `SELL`, o painel deve exibir um dos dois cenários abaixo no fractal **H2**:

### Cenário A: Contração Laminar Pura (Queda Livre)
O mercado entra em colapso natural, sem fricção.
*   **Regime (H2):** `Bear Tsunami`
*   **Flag TRAP:** Ausente.
*   **Confiança (H2):** Maior que `80%`.
*   **LBM Flow (Q-Math):** `Laminar Flow`.
*   *Lógica:* Macroestrutura de queda validada termodinamicamente sem anomalias no caminho.

### Cenário B: Rebote em Anomalia (A Caça aos Touros) - *Exemplo do US100 recente*
Operação de manipulação institucional no topo.
*   **Regime (H2 ou H1):** `Bull Tsunami [TRAP]` (Atenção ao `[TRAP]`).
*   **LBM Flow (Q-Math):** `Squeeze Bear`.
*   **Confiança M15:** Caindo a `0.0%` (A subida está vazia por dentro).
*   *Lógica:* Institucionais estão empurrando o preço para cima para induzir compra em topo de varejo (Bull Tsunami aparente). A flag `[TRAP]` detecta a isca. O *LBM Flow* mostra `Squeeze Bear`: internamente, o dinheiro "inteligente" está sendo desovado massivamente (venda). O preço vai desabar. Você executa um **SELL**.

---

## 3. ZONAS DE PURIFICAÇÃO (QUANDO NÃO OPERAR)
Se o status geral (Inst. Avg / RMT Spectral) estiver confuso, ou se houver divergência absurda (Ex: H2 indica Buy, mas o D1 acabou de inverter para forte Bear Tsunami Laminar), o Setor R-Exec entra em estado `PURIFYING`. 

**Regra Dourada Prática:**
1. Olhe para o **H2**. Ele dita a regra.
2. Olhe para o LBM Flow. Ele concorda com o Regime do H2? 
    * Se Sim -> Siga a tendência do Regime.
    * Se Não (Squeeze inverso) -> Espere a armadilha se fechar e opere CONTRA o Regime.