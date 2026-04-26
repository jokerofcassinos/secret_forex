# 🛰️ ROADMAP: FASE 2 - EXECUÇÃO QUÂNTICA (R-EXEC)

O objetivo desta fase é transformar as **Zonas de Domínio** em **Ordens de Lucro**.

## 1. MÓDULO DE GATILHO (SPARK TRIGGER)
- Implementação da função `send_order()` no `mt5_bridge.py`.
- Lógica de entrada: Abertura de posição no 3º candle confirmado de uma zona de domínio.

## 2. GESTÃO DE PROTEÇÃO (CLOUD SL)
- O Stop Loss será "colado" na borda oposta da moldura visual.
- **Trailing Neural:** Se a zona de domínio se expandir, o stop se move automaticamente para o novo "Chão" (Bull) ou "Teto" (Bear).

## 3. MOTOR DE RISK MANAGEMENT
- Cálculo de lote baseado em **Drawdown Control**.
- **Circuit Breaker:** Suspensão automática se a Entropia do sistema subir acima de níveis caóticos.

---
**STATUS:** AGUARDANDO COMANDO DE INICIALIZAÇÃO.
