# 🤝 CONTRATO DE PERFORMANCE: FLASK_DATA_SERVER

## 1. IDENTIFICAÇÃO
- **Componente:** `FlaskServer`
- **Setor:** R-EXEC (Connectivity)
- **ID:** `MESSENGER_HUB_001`

## 2. ESCOPO OPERACIONAL
O Mensageiro é a ponte de consciência. Sua missão é garantir que o Terminal MQL5 receba o estado mental da IA sem perdas ou atrasos.

## 3. RESPONSABILIDADES OBRIGATÓRIAS
1.  **Disponibilidade:** Manter o endpoint `/nexus` ativo 24/7 durante a operação.
2.  **Serialização:** Transformar caches complexos em strings otimizadas para o `Nexus_Observer`.
3.  **Isolamento:** Executar em thread separada para não impactar o loop de cálculo principal.

## 4. MÉTRICAS DE SUCESSO
- Uptime de 100% durante o horário de mercado.
- Resposta do endpoint < 20ms.

---
**ASSINATURA:** NEXUS CEO
**DATA:** 2026.04.27
