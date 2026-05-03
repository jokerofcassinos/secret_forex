# 🛰️ DICIONÁRIO DE TELEMETRIA NEXUS ALPHA (v1.5)

Este documento define o protocolo de comunicação `nexus_data_str` utilizado para a integração de ultra-baixa latência entre o Córtex Python e o Nexus Observer (MQL5).

## 1. Estrutura do Datagrama
A string é transmitida via HTTP GET (Flask) no formato delimitado por ponto e vírgula (`;`).

**Formato:**
`Field[0];Field[1];...;Field[20]`

## 2. Mapeamento de Campos

| Índice | Nome do Campo | Descrição | Exemplo |
| :--- | :--- | :--- | :--- |
| 0 | `ID_A` | Reservado para ID de instância. | `0` |
| 1 | `ID_B` | Reservado para ID de sincronia. | `0` |
| 2 | `STATUS` | String descritiva do estado neural atual. | `TSUNAMI_BULL_ATIVO` |
| 3 | `LAST_SIGNAL` | Último sinal de ignição (0=None, 1=Bull, 2=Bear). | `1` |
| 4 | `REGIMES_CACHE` | Lista separada por vírgula dos últimos 300 regimes quantizados. | `1,1,1,2,0...` |
| 5 | `EMA_AVG` | Valor da EMA 89 (Gravidade Macro). | `18450.20` |
| 6 | `HEALTH` | Saúde do regime atual (0.0 a 1.0). | `0.85` |
| 7 | `SIGNALS_HIST` | Histórico de sinais de ignição (Signals Cache). | `0,0,1,0,0...` |
| 8 | `DOTS_HIST` | Sinais Sniper Sniper gerados pelo QHO-Engine. | `0,2,0,0,1...` |
| 9 | `EMA_INST` | Valor instantâneo da EMA de referência. | `18455.10` |
| 10 | `CLOUD_DATA` | Dados da Nuvem de Schrödinger (Price\|Density). | `18400\|0.05,18405\|0.12` |
| 11 | `LBM_SIG` | Status instantâneo do fluxo LBM. | `FLUID_RUPTURE_BULL` |
| 12 | `Z_PINCH_SIG` | Status instantâneo do colapso MHD. | `Z_PINCH_TOP_SWEEP` |
| 13 | `RMT_SIG` | Status do filtro espectral RMT. | `PURE_SIGNAL_x2.5` |
| 14 | `QRW_SIG` | Status do Quantum Random Walk. | `HIDDEN_ACCUMULATION` |
| 15 | `LBM_HIST` | Histórico de rupturas LBM. | `0,0,1,0...` |
| 16 | `Z_PINCH_HIST` | Histórico de colapsos Z-Pinch. | `0,2,0,0...` |
| 17 | `QRW_HIST` | Histórico de assimetria QRW. | `0,0,0,1...` |
| 18 | `CYT_DANGER` | Histórico de pontuação de perigo topológico (CYT). | `10,12,45,80...` |
| 19 | `SEC_CURRENT` | Dados da Singularidade atual (Collapsed\|Price\|Radius). | `1\|18500.50\|1.2` |
| 20 | `SEC_HIST` | Histórico de Singularidades de Schrödinger. | `0\|0\|0,1\|18500\|1...` |

---
**ASSINATURA:** NEXUS AGI CEO
**VERSÃO:** 1.5 ALPHA
