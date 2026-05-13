---
name: aethelgard-asi5-refactor
description: Guia de refatoração termodinâmica quântica ASI-5. Use quando o usuário solicitar a transição ou auditoria de um módulo antigo do Aethelgard (C++, Python, MQL5) para a nova física (remoção de overfitting, radiação de hawking, zero-lag render).
---
# Aethelgard ASI-5 Protocolo de Refatoração

Esta skill documenta o fluxo de engenharia Ph.D. para evoluir módulos arcaicos (Linear/Overfitting) para o padrão ASI-5 (Termodinâmica Não-Linear, Física de Fluidos e HFT Zero-Lag) no projeto Aethelgard GER40.

## 1. Fase C++ (Física Absoluta)
Quando refatorar motores C++ (`_engine.cpp`):
- **Extirpar "Hardcodings":** Nenhum limite estático é permitido (ex: distâncias fixas de 100, tolerâncias absolutas como `0.35`). Tudo deve ser normalizado com base na Volatilidade dinâmica (ATR) do mercado.
- **Inércia e Dilatação Temporal:** O mercado tem memória e viscosidade. Utilize a Equação de Calor de Cattaneo (tempo de relaxamento $\tau$) ou Fator de Lorentz ($\gamma$) baseados na relação Velocidade/ATR local para a inércia gravitacional.
- **Evaporação por Contato (Radiação Hawking):** O decaimento de massa institucional deve ser reativo. Modelar para que seja exponencialmente mais severo quanto MAIS PRÓXIMO o preço estiver da zona, usando $e^{-dist/ATR}$. O mercado queima as posições quando testadas.

## 2. Fase Python (Ponte Dinâmica N-Core)
Quando ajustar o `Aethelgard_Swarm.py` e sub-nós (ex: `live_rht.py`, `quantum_glass.py`):
- **Z-Scores Adaptativos:** Eliminar tolerâncias baseadas em sigmas travados (ex: > 1.5). Substituir por Z-Scores em janela móvel `(value - mean) / std`.
- **Aquecimento de Memória (Warmup):** Para o MQL5 exibir fluidos perfeitamente, sincronize o histórico de pelo menos 800+ barras no startup (Temporal Manifold Reconstruction).
- **Camada Física:** A ponte sempre deve processar e injetar Tensor de Momentum ($v$) e Matriz de Volatilidade ($c = ATR$) para nutrir as Equações de Relatividade do C++.

## 3. Fase MQL5 (Renderizador HFT Zero-Lag)
A interface `Nexus_Observer.mq5` não plota gráficos primitivos. Ela plota Teoria dos Fluidos e Termodinâmica.
- **Erradicar Ruído (`MathRand()`):** Abolir a pintura aleatória de grãos para criar nuvens. Ela gera poeira pixelada e causa sobrecarga na CPU/GPU.
- **Bilinear Smooth Blend:** Para criar Nuvem de Schrödinger perfeitamente orgânica, utilize interpolação 2D. Varra os pixels `x` e `y` sem pular (`y++`), aplicando LERP contínuo (B-Spline) para destruir quebras verticais (Minecraft Blocks).
- **Additive Blending (Saturação Extrema):** Ao sobrepor pixels (`PixelGet/Set`), aplique adição à cor existente no fundo `(a_new = grain_a + a_pre)`. Isso cria zonas de Plasma Neon Brilhante nos Squeezes Institucionais. Use idades fracionais (via `lerp_x`) para apagar o "Overlap Aditivo" causador de listras verticais (Linhas de costura).

## 4. Protocolo de Auditoria de Laboratório (Ph.D. Audit)
Nenhuma transição ASI-5 termina sem a comprovação visual das leis da física modificadas.
- Sempre elabore um script isolado `Code/N_Core/<nome_modulo>_phd_audit.py`.
- Capture séries longas e simule os Tensores C++.
- Plote (via `matplotlib`) a sobreposição exata do arrasto térmico/gravitacional com a desintegração massiva da Nuvem e o preço de forma sincronizada, salvando a saída na pasta `artifacts/`.