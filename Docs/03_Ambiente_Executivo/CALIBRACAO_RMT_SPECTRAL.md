# CALIBRAÇÃO DO RMT SPECTRAL (AJUSTE DE AUTOVALORES)
**Classificação:** Confidencial / Setor Q-Math & R-Exec
**Problema Relatado:** O indicador `RMT Spectral` está exibindo `PURE_SIGNAL` de forma constante e ininterrupta, anulando sua função como filtro de anomalias (Decoerência).

## 1. O Diagnóstico: Vazamento de Marchenko-Pastur
Se o `PURE_SIGNAL` está "sempre ligado", significa que a calibração matemática da nossa Matriz Aleatória está muito frouxa para a volatilidade atual do ativo. 
Na teoria RMT, usamos a **Distribuição de Marchenko-Pastur** para definir uma "fronteira matemática". Tudo que está abaixo dessa fronteira é considerado ruído (HFTs, robôs burros). Tudo que rompe acima dessa fronteira é considerado "Sinal Puro" (Institucionais, dinheiro real). 

Se o sinal está sempre puro, a nossa fronteira (o limite do autovalor) está baixa demais. O ruído normal do mercado está transbordando por cima do muro e sendo lido como "dinheiro real".

## 2. A Solução: Ajuste do Multiplicador de Corte (Sigma Threshold)
Para que o `PURE_SIGNAL` volte a ser um evento raro e valioso (uma verdadeira confirmação de colapso), precisamos "levantar o muro" da equação.

### Ação Necessária (Parametrização Neural / C++):
No código do Q-Math (motor C++), a variável que controla isso é o limite do *Eigenvalue* (Autovalor). Quando o operador atua de forma manual, ele deve fazer a filtragem cognitiva:

*   **O Fator de Multiplicação (x):** Note que o painel exibe `PURE_SIGNAL_x2.6`, `x3.4`, etc. Esse "x" é a magnitude do rompimento. 
*   **Regra de Ouro Manual de Calibração Diária:** Se o painel está passando o dia todo marcando `PURE_SIGNAL_x1.5` ou `x2.0`, você **descarta** essas leituras. Você eleva a sua exigência mental. A partir daquele momento, você só considerará um "Sinal Puro" válido se ele atingir, por exemplo, **`PURE_SIGNAL_x3.5` ou superior**.

## 3. Protocolo Operacional
Até que o Setor N-Core implemente um "Auto-Tuner de Volatilidade" que ajuste o muro do Marchenko-Pastur dinamicamente a cada 4 horas:

1. **Observe a base do dia:** Nos primeiros 30 minutos de operação, veja qual é a média do `PURE_SIGNAL` (Ex: fica sempre em x2.2).
2. **Defina o Threshold Cognitivo:** Adicione +1.0 à média diária. Seu novo filtro de verdade passa a ser `x3.2`.
3. **Execute com Exclusividade:** Ignore o LBM Flow, mesmo que o `PURE_SIGNAL` esteja ligado, se a magnitude dele for menor que o seu Threshold Cognitivo. 

O `PURE_SIGNAL` deve ser a exceção, o grito institucional no meio do silêncio, não a regra. Se está sempre gritando, o microfone está com o ganho muito alto.