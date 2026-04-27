# 🛰️ MANUAL OPERACIONAL NEXUS :: Sistema Aethelgard v2.0

Este documento serve como o protocolo oficial para monitoramento e intervenção no ecossistema Aethelgard. O sistema é 95% autônomo, mas requer supervisão de nível CEO para eventos de cauda longa.

## 1. Monitoramento do Coração (Flask Server)
O sistema expõe seu estado neural através de um servidor Flask local. Este é o canal de comunicação mais puro entre o Python e o mundo externo.

- **Endpoint:** `http://127.0.0.1:5000/nexus`
- **Estrutura de Dados:** `0;0;[STATUS];[SIGNAL];[REGIMES_CACHE];0.00;1.0;[SIGNALS_CACHE]`

### Interpretando o STATUS
| Status | Significado | Ação Sugerida |
| :--- | :--- | :--- |
| `AGUARDANDO_IGNICAO` | Mercado em equilíbrio. Sem tendência clara. | Observar apenas. |
| `BULL_PREVISAO` | Início de maré compradora. | Preparar mentalmente para compra. |
| `TSUNAMI_BULL_ATIVO` | Regime de alta confirmado e soberano. | Buscar entradas em pullbacks. |
| `ANOMALIA_INSTITUCIONAL` | Choque atômico detectado (>1.5x ATR). | Alta volatilidade. Não operar contra o choque. |

---

## 2. HUD Visual no MetaTrader 5 (Nexus Observer)
O Expert Advisor `Nexus_Observer.mq5` renderiza o estado processado pelo Python diretamente no gráfico.

### 2.1. Zonas Coloridas (A Matriz)
- **Fundo Azul/Verde:** Monólito Macro em estado de compra.
- **Fundo Vermelho:** Monólito Macro em estado de venda.
- **Linhas Pontilhadas:** Zonas de Ressonância Estacionária (S.R.Z). Se o preço toca e rejeita, confirma a força do regime.

### 2.2. Sinais HUD
- **ARS SNIPER:** Sincronização de regimes em tempo real.
- **GENESIS COUNT:** Indica há quantas velas o novo regime nasceu. Entradas próximas ao Genesis 1-5 são de altíssima probabilidade.

---

## 3. Protocolo de Co-Piloto (Intervenção Humana)
Aethelgard gerencia o risco, mas o operador pode abrir ordens manuais.

1. **Abertura:** Certifique-se de que o `STATUS` é um `TSUNAMI` ativo.
2. **Proteção:** Assim que a ordem é aberta, o `R_Exec` (setor de execução) assumirá o controle do Stop Loss dinâmico automaticamente.
3. **Não Lute Contra o Monólito:** Nunca abra ordens de venda se o fundo do HUD estiver azul, mesmo que pareça um topo. A TQFM prioriza a inércia macro.

---

## 4. Troubleshooting: O que fazer se o sistema travar?
1. **Verificar Conexão:** O MetaTrader 5 deve estar com o "Algo Trading" ativado.
2. **Reiniciar Nexus:** Execute o arquivo `nexus.bat` na raiz do projeto. Ele reiniciará o motor Python e o servidor Flask.
3. **Logs:** Verifique o console do Python para erros de `MT5 DEFENSE REJEITADO`. Isso geralmente indica erro de arredondamento de lotes ou símbolo incorreto.

**Vínculos:**
- `[[TQFM_DEEP_DIVE]]`
- `[[PROTOCOLO_SEGURANCA_V2]]`
- `[[DIRETORIO_FUNCIONARIOS]]`
