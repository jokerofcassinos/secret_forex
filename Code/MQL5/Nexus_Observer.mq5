//+------------------------------------------------------------------+
//|                                              Nexus_Observer.mq5 |
//|                                  Copyright 2026, NEXUS AGI CEO |
//+------------------------------------------------------------------+
#property copyright "NEXUS AGI CEO"
#property version   "113.00"
#property strict

// Memória de Estado
string last_payload = "";

//+------------------------------------------------------------------+
int OnInit() { 
    EventSetTimer(1); 
    ChartSetInteger(0, CHART_SHOW_TRADE_LEVELS, false); // Esconde as setas nativas feias do MT5
    return(INIT_SUCCEEDED); 
}
void OnDeinit(const int reason) { EventKillTimer(); ObjectsDeleteAll(0, "NEXUS_"); }
void OnTick() { UpdateDashboard(); DrawModernTradeHistory(); }
void OnTimer() { UpdateDashboard(); DrawModernTradeHistory(); }

void UpdateDashboard()
{
   string url = "http://127.0.0.1:5000/nexus?tf=" + IntegerToString(_Period);
   string cookie=NULL,headers;
   char post[],result[];
   int res;
   
   res = WebRequest("GET", url, cookie, NULL, 50, post, 0, result, headers);
   if(res == 200) {
      string response = CharArrayToString(result);
      if(response != last_payload) { // Só processa se houver mudança real
         ParseAndDraw(response);
         last_payload = response;
      }
   }
}

void ParseAndDraw(string data)
{
   string parts[];
   StringSplit(data, ';', parts);
   if(ArraySize(parts) < 10) return;

   string statusTxt = parts[2];
   string historyRegimes = parts[4]; 
   double instAvgPrice = StringToDouble(parts[5]);
   double health = StringToDouble(parts[6]);
   string historySignals = parts[7];
   string historyDots = parts[8];
   
   bool qddActive = (StringFind(statusTxt, "AGUARDANDO_IGNICAO") < 0 && StringFind(statusTxt, "INIT") < 0);
   string qddMsg = qddActive ? "PURIFYING" : "SCANNING";

   string lbm_signal = (ArraySize(parts) > 11) ? parts[11] : "LAMINAR_FLOW";
   string z_signal = (ArraySize(parts) > 12) ? parts[12] : "NEUTRAL";
   string rmt_signal = (ArraySize(parts) > 13) ? parts[13] : "NOISE";
   string qrw_signal = (ArraySize(parts) > 14) ? parts[14] : "NEUTRAL";

   // Limpa as antigas poluições textuais
   ObjectDelete(0, "NEXUS_HEADER");
   ObjectDelete(0, "NEXUS_QDD_STATUS");
   ObjectDelete(0, "NEXUS_STATUS");
   ObjectDelete(0, "NEXUS_INST_AVG");
   ObjectDelete(0, "NEXUS_LBM_WARNING");
   ObjectDelete(0, "NEXUS_ZPINCH_WARNING");
   ObjectDelete(0, "NEXUS_RMT_WARNING");
   ObjectDelete(0, "NEXUS_QRW_WARNING");

   DrawModernDashboard(statusTxt, instAvgPrice, health, qddMsg, lbm_signal, z_signal, rmt_signal, qrw_signal);

   // 1. ATUALIZAÇÃO DAS CAIXAS (SEM DELETAR TUDO)
   string hReg[]; StringSplit(historyRegimes, ',', hReg);
   int totalR = ArraySize(hReg);
   
   int i = 0; int boxIdx = 0;
   while(i < totalR && i < iBars(_Symbol, _Period)) {
      string val = hReg[totalR - 1 - i];
      string sub[]; StringSplit(val, '|', sub);
      int r = (int)StringToInteger(sub[0]);
      
      if(r != 0) {
         int start = i; int end = i;
         while(end + 1 < totalR && end + 1 < iBars(_Symbol, _Period)) {
            string nextVal = hReg[totalR - 1 - (end + 1)];
            string nSub[]; StringSplit(nextVal, '|', nSub);
            if((int)StringToInteger(nSub[0]) == r) end++; else break;
         }
         
         double maxH = 0; double minL = 9999999;
         for(int k=start; k<=end; k++) {
            maxH = MathMax(maxH, iHigh(_Symbol, _Period, k));
            minL = MathMin(minL, iLow(_Symbol, _Period, k));
         }
         
         string bName = "NEXUS_ZONE_" + IntegerToString(boxIdx);
         color zClr = (r == 1) ? RGB(38, 166, 154) : RGB(239, 83, 80);
         
         // ObjectCreate em objeto existente apenas atualiza as coordenadas (Sem Flicker)
         if(ObjectFind(0, bName) < 0) ObjectCreate(0, bName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
         ObjectSetInteger(0, bName, OBJPROP_TIME, 0, iTime(_Symbol, _Period, start));
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 0, maxH);
         ObjectSetInteger(0, bName, OBJPROP_TIME, 1, iTime(_Symbol, _Period, end));
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 1, minL);
         ObjectSetInteger(0, bName, OBJPROP_COLOR, zClr);
         ObjectSetInteger(0, bName, OBJPROP_WIDTH, 2);
         ObjectSetInteger(0, bName, OBJPROP_BACK, true);
         
         boxIdx++;
         i = end + 1;
      } else i++;
   }
   // Limpa caixas excedentes da memória
   for(int k=boxIdx; k<100; k++) ObjectDelete(0, "NEXUS_ZONE_"+IntegerToString(k));

   // 2. ATUALIZAÇÃO DOS TACTICAL DOTS (GRADIENTE PERSISTENTE)
   string hDots[]; StringSplit(historyDots, ',', hDots);
   int totalD = ArraySize(hDots);
   
   for(int d=0; d < totalD && d < iBars(_Symbol, _Period); d++) {
      int dotVal = (int)StringToInteger(hDots[totalD - 1 - d]);
      string dName = "NEXUS_DOT_" + IntegerToString(d);
      
      if(dotVal == 0) {
         ObjectDelete(0, dName); continue;
      }
      
      color dClr = clrBlack;
      bool isAbove = (dotVal == 2 || dotVal == 21 || dotVal == 22 || dotVal == 23);

      if(dotVal == 1) dClr = RGB(38, 166, 154);
      else if(dotVal == 11) dClr = RGB(0, 150, 136);
      else if(dotVal == 12) dClr = RGB(0, 121, 107);
      else if(dotVal == 13) dClr = RGB(0, 77, 64);
      else if(dotVal == 2) dClr = RGB(239, 83, 80);
      else if(dotVal == 21) dClr = RGB(229, 57, 53);
      else if(dotVal == 22) dClr = RGB(198, 40, 40);
      else if(dotVal == 23) dClr = RGB(183, 28, 28);

      if(dClr == clrBlack) { ObjectDelete(0, dName); continue; }

      double offset = 140 * _Point; // Mais margem para não poluir os candles
      double dPrice = isAbove ? iHigh(_Symbol, _Period, d) + offset : iLow(_Symbol, _Period, d) - offset;
      
      // Remove o antigo background se existir (Limpeza de versão anterior)
      string dNameBg = dName + "_BG";
      if(ObjectFind(0, dNameBg) >= 0) ObjectDelete(0, dNameBg);

      // Seta Minimalista (Foreground Elegante)
      if(ObjectFind(0, dName) >= 0 && ObjectGetInteger(0, dName, OBJPROP_TYPE) != OBJ_ARROW) ObjectDelete(0, dName);
      if(ObjectFind(0, dName) < 0) ObjectCreate(0, dName, OBJ_ARROW, 0, 0, 0);
      
      ObjectSetInteger(0, dName, OBJPROP_TIME, iTime(_Symbol, _Period, d));
      ObjectSetDouble(0, dName, OBJPROP_PRICE, dPrice);
      ObjectSetInteger(0, dName, OBJPROP_ARROWCODE, isAbove ? 234 : 233); // Seta Moderna (Wingdings)
      ObjectSetInteger(0, dName, OBJPROP_COLOR, dClr);
      ObjectSetInteger(0, dName, OBJPROP_WIDTH, (dotVal < 10 ? 3 : 2)); // Limpo e vísivel
      ObjectSetInteger(0, dName, OBJPROP_ANCHOR, isAbove ? ANCHOR_BOTTOM : ANCHOR_TOP);
      ObjectSetInteger(0, dName, OBJPROP_BACK, true); // Sem sobrepor o HUD
   }

   // 3. ATUALIZAÇÃO DOS SINAIS DE VOLUME
   string hSig[]; StringSplit(historySignals, ',', hSig);
   int totalS = ArraySize(hSig);
   
   for(int j=0; j < totalS && j < iBars(_Symbol, _Period); j++) {
      int sVal = (int)StringToInteger(hSig[totalS - 1 - j]);
      string sName = "NEXUS_SIG_" + IntegerToString(j);
      
      if(sVal == 0) {
         ObjectDelete(0, sName); continue;
      }
      
      double sPrice = (sVal == 1) ? iLow(_Symbol, _Period, j) - 100 * _Point : iHigh(_Symbol, _Period, j) + 100 * _Point;
      color sClr = (sVal == 1) ? RGB(66, 165, 245) : RGB(255, 167, 38);
      
      // Remove o antigo background se existir
      string sNameBg = sName + "_BG";
      if(ObjectFind(0, sNameBg) >= 0) ObjectDelete(0, sNameBg);

      // Texto Minimalista HUD-Like
      if(ObjectFind(0, sName) >= 0 && ObjectGetInteger(0, sName, OBJPROP_TYPE) != OBJ_TEXT) ObjectDelete(0, sName);
      if(ObjectFind(0, sName) < 0) ObjectCreate(0, sName, OBJ_TEXT, 0, 0, 0);
      
      ObjectSetInteger(0, sName, OBJPROP_TIME, iTime(_Symbol, _Period, j));
      ObjectSetDouble(0, sName, OBJPROP_PRICE, sPrice);
      
      string vSymbol = (sVal == 1) ? ShortToString(0x25B2) : ShortToString(0x25BC);
      ObjectSetString(0, sName, OBJPROP_TEXT, vSymbol + " VOL");
      ObjectSetString(0, sName, OBJPROP_FONT, "Segoe UI Bold");
      ObjectSetInteger(0, sName, OBJPROP_COLOR, sClr); // Neon bright colors
      ObjectSetInteger(0, sName, OBJPROP_FONTSIZE, 9);
      ObjectSetInteger(0, sName, OBJPROP_ANCHOR, (sVal == 1 ? ANCHOR_TOP : ANCHOR_BOTTOM));
      ObjectSetInteger(0, sName, OBJPROP_BACK, true); // Prevent HUD overlap
   }
   
   // 4. ATUALIZAÇÃO DA NUVEM QUÂNTICA DE SCHRÖDINGER
   if(ArraySize(parts) > 10 && parts[10] != "") {
      string cloudBins[]; StringSplit(parts[10], ',', cloudBins);
      int tCloud = ArraySize(cloudBins);
      
      // Encontrar a densidade máxima para normalizar a largura (histograma)
      double maxDensity = 0.0001;
      for(int b=0; b<tCloud; b++) {
         string cVal[]; StringSplit(cloudBins[b], '|', cVal);
         if(ArraySize(cVal) == 2) {
             double den = StringToDouble(cVal[1]);
             if(den > maxDensity) maxDensity = den;
         }
      }
      
      datetime tStart = iTime(_Symbol, _Period, MathMin(100, iBars(_Symbol, _Period)-1)); // Cobre o fundo visualmente 100 barras pra trás
      datetime tEnd = TimeCurrent() + PeriodSeconds() * 20; // Avança visualmente pro futuro
      
      // Estima a largura da banda (dx)
      double dx = 10 * _Point; 
      if(tCloud > 1) {
         string cVal0[]; StringSplit(cloudBins[0], '|', cVal0);
         string cVal1[]; StringSplit(cloudBins[1], '|', cVal1);
         if(ArraySize(cVal0) == 2 && ArraySize(cVal1) == 2) {
             dx = MathAbs(StringToDouble(cVal0[0]) - StringToDouble(cVal1[0]));
         }
      }
      
      double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      
      for(int b=0; b<tCloud; b++) {
         string cVal[]; StringSplit(cloudBins[b], '|', cVal);
         if(ArraySize(cVal) != 2) continue;
         
         double pLevel = StringToDouble(cVal[0]);
         double den = StringToDouble(cVal[1]);
         
         string bName = "NEXUS_QC_" + IntegerToString(b);
         string tagName = "NEXUS_QCTAG_" + IntegerToString(b);
         
         if(den < maxDensity * 0.05) { // Threshold dinâmico menor para fade suave
             ObjectDelete(0, bName);
             ObjectDelete(0, tagName);
             continue;
         }
         
         double ratio = den / maxDensity;
         // Curva de intensidade para manter o brilho em high-density e fade natural
         ratio = MathPow(ratio, 1.2); 
         if(ratio > 1.0) ratio = 1.0;
         
         uchar r, g, b;
         // Gradiente TV-Style Termodinâmico (Smooth Lerp)
         if(pLevel > currentPrice) {
             // Red Gradient: From Base(24,24,24) to Hot(239,83,80)
             r = (uchar)(24 + (239 - 24) * ratio);
             g = (uchar)(24 + (83 - 24) * ratio);
             b = (uchar)(24 + (80 - 24) * ratio);
         } else {
             // Teal Gradient: From Base(24,24,24) to Hot(38,166,154)
             r = (uchar)(24 + (38 - 24) * ratio);
             g = (uchar)(24 + (166 - 24) * ratio);
             b = (uchar)(24 + (154 - 24) * ratio);
         }
         color qColor = RGB(r, g, b);
         
         // Cria a Banda Background
         if(ObjectFind(0, bName) < 0) ObjectCreate(0, bName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
         ObjectSetInteger(0, bName, OBJPROP_TIME, 0, tStart);
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 0, pLevel + (dx/2.0));
         ObjectSetInteger(0, bName, OBJPROP_TIME, 1, tEnd);
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 1, pLevel - (dx/2.0));
         ObjectSetInteger(0, bName, OBJPROP_COLOR, qColor);
         ObjectSetInteger(0, bName, OBJPROP_FILL, true);
         ObjectSetInteger(0, bName, OBJPROP_BACK, true); // Essencial: Fica no background igual TradingView
         
         // Desenha a Tag POC/HOTSPOT no eixo de preços
         if(ratio > 0.95) {
             if(ObjectFind(0, tagName) < 0) ObjectCreate(0, tagName, OBJ_ARROW_RIGHT_PRICE, 0, 0, 0);
             ObjectSetInteger(0, tagName, OBJPROP_TIME, 0, tEnd);
             ObjectSetDouble(0, tagName, OBJPROP_PRICE, 0, pLevel);
             ObjectSetInteger(0, tagName, OBJPROP_COLOR, clrGold);
             ObjectSetString(0, tagName, OBJPROP_TEXT, " POC / HOTSPOT");
         } else {
             ObjectDelete(0, tagName);
         }
      }
      
      // Limpa bins extras que podem ter sobrado se o grid diminuir
      for(int k=tCloud; k<200; k++) ObjectDelete(0, "NEXUS_QC_"+IntegerToString(k));
   }
   
   // Os alertas isolados de LBM, Z-PINCH, RMT e QRW foram integrados ao painel do HUD Moderno.

   // 9. ATUALIZAÇÃO DO HISTÓRICO LBM (MARCADORES PERMANENTES)
   if(ArraySize(parts) > 15 && parts[15] != "") {
      string hLbm[]; StringSplit(parts[15], ',', hLbm);
      int tLbm = ArraySize(hLbm);
      for(int j=0; j < tLbm && j < iBars(_Symbol, _Period); j++) {
         int v = (int)StringToInteger(hLbm[tLbm - 1 - j]);
         string name = "NEXUS_LBM_HIST_" + IntegerToString(j);
         if(v == 0) { ObjectDelete(0, name); continue; }
         if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_ARROW, 0, 0, 0);
         double p = (v == 1) ? iLow(_Symbol, _Period, j) - 150 * _Point : iHigh(_Symbol, _Period, j) + 150 * _Point;
         ObjectSetInteger(0, name, OBJPROP_TIME, iTime(_Symbol, _Period, j));
         ObjectSetDouble(0, name, OBJPROP_PRICE, p);
         ObjectSetInteger(0, name, OBJPROP_ARROWCODE, 108); // Diamond
         ObjectSetInteger(0, name, OBJPROP_COLOR, (v == 1) ? RGB(66, 165, 245) : RGB(171, 71, 188));
         ObjectSetInteger(0, name, OBJPROP_ANCHOR, (v == 1) ? ANCHOR_TOP : ANCHOR_BOTTOM);
         ObjectSetInteger(0, name, OBJPROP_BACK, true);
      }
   }
   
   // 10. ATUALIZAÇÃO DO HISTÓRICO Z-PINCH
   if(ArraySize(parts) > 16 && parts[16] != "") {
      string hZP[]; StringSplit(parts[16], ',', hZP);
      int tZP = ArraySize(hZP);
      for(int j=0; j < tZP && j < iBars(_Symbol, _Period); j++) {
         int v = (int)StringToInteger(hZP[tZP - 1 - j]);
         string name = "NEXUS_ZP_HIST_" + IntegerToString(j);
         if(v == 0) { ObjectDelete(0, name); continue; }
         if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_ARROW, 0, 0, 0);
         double p = (v == 1) ? iLow(_Symbol, _Period, j) - 250 * _Point : iHigh(_Symbol, _Period, j) + 250 * _Point;
         ObjectSetInteger(0, name, OBJPROP_TIME, iTime(_Symbol, _Period, j));
         ObjectSetDouble(0, name, OBJPROP_PRICE, p);
         ObjectSetInteger(0, name, OBJPROP_ARROWCODE, 171); // Star
         ObjectSetInteger(0, name, OBJPROP_COLOR, RGB(255, 202, 40));
         ObjectSetInteger(0, name, OBJPROP_ANCHOR, (v == 1) ? ANCHOR_TOP : ANCHOR_BOTTOM);
         ObjectSetInteger(0, name, OBJPROP_BACK, true);
      }
   }

   // 11. ATUALIZAÇÃO DO HISTÓRICO QRW
   if(ArraySize(parts) > 17 && parts[17] != "") {
      string hQRW[]; StringSplit(parts[17], ',', hQRW);
      int tQRW = ArraySize(hQRW);
      for(int j=0; j < tQRW && j < iBars(_Symbol, _Period); j++) {
         int v = (int)StringToInteger(hQRW[tQRW - 1 - j]);
         string name = "NEXUS_QRW_HIST_" + IntegerToString(j);
         if(v == 0) { ObjectDelete(0, name); continue; }
         if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_ARROW, 0, 0, 0);
         double p = (v == 1) ? iLow(_Symbol, _Period, j) - 350 * _Point : iHigh(_Symbol, _Period, j) + 350 * _Point;
         ObjectSetInteger(0, name, OBJPROP_TIME, iTime(_Symbol, _Period, j));
         ObjectSetDouble(0, name, OBJPROP_PRICE, p);
         ObjectSetInteger(0, name, OBJPROP_ARROWCODE, 233); // Arrow/Checkmark
         ObjectSetInteger(0, name, OBJPROP_COLOR, (v == 1) ? RGB(38, 198, 218) : RGB(255, 167, 38));
         ObjectSetInteger(0, name, OBJPROP_ANCHOR, (v == 1) ? ANCHOR_TOP : ANCHOR_BOTTOM);
         ObjectSetInteger(0, name, OBJPROP_BACK, true);
      }
   }
   
   ChartRedraw(0);
}

void DrawLabel(string name, string text, int x, int y, color clr, int fontSize)
{
   if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
   ObjectSetString(0, name, OBJPROP_TEXT, text);
   ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, name, OBJPROP_FONTSIZE, fontSize);
}

void DrawModernTradeHistory()
{
    datetime start_time = iTime(_Symbol, _Period, MathMin(300, iBars(_Symbol, _Period)-1));
    if(start_time == 0) return;
    
    HistorySelect(start_time, TimeCurrent());
    int total = HistoryDealsTotal();
    
    // Pass 1: Desenhar Entradas (IN)
    for(int i=0; i<total; i++) {
        ulong ticket = HistoryDealGetTicket(i);
        if(HistoryDealGetString(ticket, DEAL_SYMBOL) != _Symbol) continue;
        long entry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
        
        if(entry == DEAL_ENTRY_IN) {
            string inName = "NEXUS_TIN_" + IntegerToString(ticket);
            if(ObjectFind(0, inName) >= 0) continue;
            
            long type = HistoryDealGetInteger(ticket, DEAL_TYPE);
            datetime time = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
            double price = HistoryDealGetDouble(ticket, DEAL_PRICE);
            
            ObjectCreate(0, inName, OBJ_ARROW, 0, time, price);
            ObjectSetInteger(0, inName, OBJPROP_ARROWCODE, 119); // Modern Diamond
            ObjectSetInteger(0, inName, OBJPROP_COLOR, (type == DEAL_TYPE_BUY) ? RGB(66, 165, 245) : RGB(171, 71, 188));
            ObjectSetInteger(0, inName, OBJPROP_WIDTH, 2);
            ObjectSetInteger(0, inName, OBJPROP_ANCHOR, (type == DEAL_TYPE_BUY) ? ANCHOR_TOP : ANCHOR_BOTTOM);
            ObjectSetInteger(0, inName, OBJPROP_BACK, false);
        }
    }
    
    // Pass 2: Desenhar Saídas (OUT) e Linhas de Conexão
    HistorySelect(start_time, TimeCurrent());
    for(int i=0; i<total; i++) {
        ulong ticket = HistoryDealGetTicket(i);
        if(HistoryDealGetString(ticket, DEAL_SYMBOL) != _Symbol) continue;
        long entry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
        
        if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_INOUT) {
            ulong pos_id = HistoryDealGetInteger(ticket, DEAL_POSITION_ID);
            double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
            
            string outName = "NEXUS_TOUT_" + IntegerToString(ticket);
            if(ObjectFind(0, outName) >= 0) continue; // Already processed
            
            // Procura o DEAL_IN desta posição
            if(HistorySelectByPosition(pos_id)) {
                int pTotal = HistoryDealsTotal();
                datetime in_time = 0; double in_price = 0;
                for(int j=0; j<pTotal; j++) {
                    ulong p_ticket = HistoryDealGetTicket(j);
                    if(HistoryDealGetInteger(p_ticket, DEAL_ENTRY) == DEAL_ENTRY_IN) {
                        in_time = (datetime)HistoryDealGetInteger(p_ticket, DEAL_TIME);
                        in_price = HistoryDealGetDouble(p_ticket, DEAL_PRICE);
                        break;
                    }
                }
                
                if(in_time != 0) {
                    datetime out_time = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
                    double out_price = HistoryDealGetDouble(ticket, DEAL_PRICE);
                    
                    // Desenha a Linha Sólida (Restaurada)
                    string lineName = "NEXUS_TLINE_" + IntegerToString(ticket);
                    ObjectCreate(0, lineName, OBJ_TREND, 0, in_time, in_price, out_time, out_price);
                    ObjectSetInteger(0, lineName, OBJPROP_COLOR, (profit > 0) ? RGB(38, 166, 154) : RGB(239, 83, 80));
                    ObjectSetInteger(0, lineName, OBJPROP_STYLE, STYLE_SOLID);
                    ObjectSetInteger(0, lineName, OBJPROP_WIDTH, 2);
                    ObjectSetInteger(0, lineName, OBJPROP_RAY_RIGHT, false);
                    ObjectSetInteger(0, lineName, OBJPROP_BACK, true);
                    
                    // Desenha o Marcador de Saída (Target Circle)
                    ObjectCreate(0, outName, OBJ_ARROW, 0, out_time, out_price);
                    ObjectSetInteger(0, outName, OBJPROP_ARROWCODE, 162); // Circle Target
                    ObjectSetInteger(0, outName, OBJPROP_COLOR, (profit > 0) ? RGB(38, 166, 154) : RGB(239, 83, 80));
                    ObjectSetInteger(0, outName, OBJPROP_WIDTH, 3);
                    ObjectSetInteger(0, outName, OBJPROP_ANCHOR, ANCHOR_CENTER);
                    ObjectSetInteger(0, outName, OBJPROP_BACK, false);
                    
                    // Cria uma "Caixa" (Tooltip) para o texto, com altura auto-ajustável baseada em porcentagem do preço
                    datetime box_start = out_time + PeriodSeconds(_Period) * 1;
                    datetime box_end = out_time + PeriodSeconds(_Period) * 6; // Largura ajustada
                    double box_margin = out_price * 0.0004; // Altura de 0.08% do preço total
                    double box_top = out_price + box_margin;
                    double box_bottom = out_price - box_margin;
                    
                    string boxName = "NEXUS_TBOX_" + IntegerToString(ticket);
                    ObjectCreate(0, boxName, OBJ_RECTANGLE, 0, box_start, box_top, box_end, box_bottom);
                    ObjectSetInteger(0, boxName, OBJPROP_COLOR, (profit > 0) ? RGB(0, 105, 92) : RGB(183, 28, 28));
                    ObjectSetInteger(0, boxName, OBJPROP_FILL, true);
                    ObjectSetInteger(0, boxName, OBJPROP_BACK, true);
                    
                    // Texto do lucro centralizado dentro da caixa
                    string textName = "NEXUS_TTEXT_" + IntegerToString(ticket);
                    ObjectCreate(0, textName, OBJ_TEXT, 0, box_start + PeriodSeconds(_Period) * 1, out_price);
                    ObjectSetString(0, textName, OBJPROP_TEXT, (profit > 0 ? "+" : "") + DoubleToString(profit, 2));
                    ObjectSetInteger(0, textName, OBJPROP_COLOR, clrWhite);
                    ObjectSetInteger(0, textName, OBJPROP_FONTSIZE, 9);
                    ObjectSetInteger(0, textName, OBJPROP_ANCHOR, ANCHOR_LEFT);
                    ObjectSetInteger(0, textName, OBJPROP_BACK, true); // Push to chart layer
                }
            }
        }
    }
    // Restaura a seleção de histórico para a janela principal
    HistorySelect(start_time, TimeCurrent());
}

//+------------------------------------------------------------------+
//| MODERN HUD FUNCTIONS (TRADINGVIEW STYLE)                         |
//+------------------------------------------------------------------+

string GetStatusShort(string status) {
    if(StringFind(status, "TSUNAMI_BULL") >= 0) return "Bull Tsunami";
    if(StringFind(status, "TSUNAMI_BEAR") >= 0) return "Bear Tsunami";
    if(StringFind(status, "BULL_PREVISAO") >= 0) return "Bull Pre-Ignition";
    if(StringFind(status, "BEAR_PREVISAO") >= 0) return "Bear Pre-Ignition";
    return "Neutral Regime";
}
color GetStatusColor(string status) {
    if(StringFind(status, "BULL") >= 0) return RGB(38, 166, 154); // TV Green
    if(StringFind(status, "BEAR") >= 0) return RGB(239, 83, 80); // TV Red
    return RGB(120, 123, 134); // TV Gray
}
color GetHealthColor(double h) { return (h < 0.3) ? RGB(239, 83, 80) : (h < 0.6 ? RGB(255, 167, 38) : RGB(38, 166, 154)); }

string GetLBMShort(string lbm) {
    if(lbm == "FLUID_RUPTURE_BULL") return "Squeeze Bull";
    if(lbm == "FLUID_RUPTURE_BEAR") return "Squeeze Bear";
    return "Laminar Flow";
}
color GetLBMColor(string lbm) {
    if(lbm == "FLUID_RUPTURE_BULL") return RGB(66, 165, 245); // TV Blue
    if(lbm == "FLUID_RUPTURE_BEAR") return RGB(171, 71, 188); // TV Purple
    return RGB(120, 123, 134);
}

string GetZPShort(string zp) {
    if(zp == "NEUTRAL" || zp == "") return "Neutral";
    if(StringFind(zp, "Z_PINCH_") >= 0) {
        string sub[]; StringSplit(zp, '_', sub);
        if(ArraySize(sub) >= 3) return sub[2] + " " + sub[3]; // "BOTTOM SWEEP"
    }
    return zp; 
}
color GetZPColor(string zp) { return (zp == "NEUTRAL" || zp == "") ? RGB(120, 123, 134) : RGB(255, 202, 40); }

string GetRMTShort(string rmt) {
    if(rmt == "NOISE" || rmt == "") return "Noise Filtered";
    return rmt; // PURE_SIGNAL_x2.7
}
color GetRMTColor(string rmt) { return (rmt == "NOISE" || rmt == "") ? RGB(120, 123, 134) : RGB(38, 166, 154); }

string GetQRWShort(string qrw) {
    if(qrw == "NEUTRAL" || qrw == "") return "No Interf.";
    if(qrw == "HIDDEN_ACCUMULATION_BULL") return "Accumulation";
    if(qrw == "HIDDEN_DISTRIBUTION_BEAR") return "Distribution";
    return qrw;
}
color GetQRWColor(string qrw) {
    if(qrw == "HIDDEN_ACCUMULATION_BULL") return RGB(38, 198, 218); // Cyan
    if(qrw == "HIDDEN_DISTRIBUTION_BEAR") return RGB(255, 167, 38); // Orange
    return RGB(120, 123, 134);
}

void DrawHUDText(string name, string text, int x, int y, color clr, int fontSize, bool isRightAligned=false, int corner=CORNER_RIGHT_UPPER)
{
    if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
    ObjectSetInteger(0, name, OBJPROP_CORNER, corner);
    ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
    ObjectSetString(0, name, OBJPROP_TEXT, text);
    ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
    ObjectSetInteger(0, name, OBJPROP_FONTSIZE, fontSize);
    ObjectSetString(0, name, OBJPROP_FONT, "Segoe UI");
    ObjectSetInteger(0, name, OBJPROP_ANCHOR, isRightAligned ? ANCHOR_RIGHT_UPPER : ANCHOR_LEFT_UPPER);
    ObjectSetInteger(0, name, OBJPROP_ZORDER, 100); // Extremely high Z-order to guarantee top rendering
    ObjectSetInteger(0, name, OBJPROP_BACK, false);
}

color RGB(uchar r, uchar g, uchar b) { return (color)((b << 16) | (g << 8) | r); }

void DrawHUDRow(string id, string label, string val, color valClr, int baseX, int y, int panelW, int corner=CORNER_LEFT_UPPER)
{
    DrawHUDText(id + "_L", label, baseX + 15, y, RGB(140, 140, 145), 9, false, corner); 
    DrawHUDText(id + "_V", val, baseX + panelW - 15, y, valClr, 9, true, corner);
}

void DrawModernDashboard(string status, double instAvg, double health, string qdd, string lbm, string zp, string rmt, string qrw)
{
    int panelW = 280;
    int panelH = 200;
    int corner = CORNER_LEFT_UPPER;
    int baseX = 20;
    int baseY = 30;
    
    // Background Rectangle
    string bgName = "NEXUS_HUD_BASE";
    if(ObjectFind(0, bgName) < 0) ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, bgName, OBJPROP_CORNER, corner);
    ObjectSetInteger(0, bgName, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
    ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, baseX);
    ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, baseY);
    ObjectSetInteger(0, bgName, OBJPROP_XSIZE, panelW);
    ObjectSetInteger(0, bgName, OBJPROP_YSIZE, panelH);
    ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, RGB(30, 34, 45)); // Distinct Dark Blue/Grey TV panel
    ObjectSetInteger(0, bgName, OBJPROP_COLOR, RGB(60, 65, 80)); // Light Border
    ObjectSetInteger(0, bgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, bgName, OBJPROP_BACK, false);
    ObjectSetInteger(0, bgName, OBJPROP_ZORDER, 90); // High Z-order
    
    // Title Background
    string hBgName = "NEXUS_HUD_HEADER_BG";
    if(ObjectFind(0, hBgName) < 0) ObjectCreate(0, hBgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, hBgName, OBJPROP_CORNER, corner);
    ObjectSetInteger(0, hBgName, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
    ObjectSetInteger(0, hBgName, OBJPROP_XDISTANCE, baseX);
    ObjectSetInteger(0, hBgName, OBJPROP_YDISTANCE, baseY);
    ObjectSetInteger(0, hBgName, OBJPROP_XSIZE, panelW);
    ObjectSetInteger(0, hBgName, OBJPROP_YSIZE, 35);
    ObjectSetInteger(0, hBgName, OBJPROP_BGCOLOR, RGB(38, 43, 56));
    ObjectSetInteger(0, hBgName, OBJPROP_COLOR, RGB(60, 65, 80));
    ObjectSetInteger(0, hBgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, hBgName, OBJPROP_ZORDER, 95); // High Z-order
    ObjectSetInteger(0, hBgName, OBJPROP_BACK, false);

    DrawHUDText("NEXUS_HUD_TITLE", "HELIX ENSEMBLE", baseX + 15, baseY + 10, RGB(220, 225, 235), 10, false, corner);
    
    // Divider
    string divName = "NEXUS_HUD_DIVIDER";
    if(ObjectFind(0, divName) < 0) ObjectCreate(0, divName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, divName, OBJPROP_CORNER, corner);
    ObjectSetInteger(0, divName, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
    ObjectSetInteger(0, divName, OBJPROP_XDISTANCE, baseX);
    ObjectSetInteger(0, divName, OBJPROP_YDISTANCE, baseY + 35);
    ObjectSetInteger(0, divName, OBJPROP_XSIZE, panelW);
    ObjectSetInteger(0, divName, OBJPROP_YSIZE, 1);
    ObjectSetInteger(0, divName, OBJPROP_BGCOLOR, RGB(60, 65, 80));
    ObjectSetInteger(0, divName, OBJPROP_COLOR, RGB(60, 65, 80));
    ObjectSetInteger(0, divName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, divName, OBJPROP_ZORDER, 96); // High Z-order
    
    int rowY = baseY + 45;
    int rowH = 19;
    
    // Draw row backgrounds
    for(int i=0; i<8; i++) {
        string rBgName = "NEXUS_HUD_ROW_BG_" + IntegerToString(i);
        if(ObjectFind(0, rBgName) < 0) ObjectCreate(0, rBgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, rBgName, OBJPROP_CORNER, corner);
        ObjectSetInteger(0, rBgName, OBJPROP_ANCHOR, ANCHOR_LEFT_UPPER);
        ObjectSetInteger(0, rBgName, OBJPROP_XDISTANCE, baseX);
        ObjectSetInteger(0, rBgName, OBJPROP_YDISTANCE, baseY + 36 + (i * rowH));
        ObjectSetInteger(0, rBgName, OBJPROP_XSIZE, panelW);
        ObjectSetInteger(0, rBgName, OBJPROP_YSIZE, rowH);
        ObjectSetInteger(0, rBgName, OBJPROP_BGCOLOR, (i % 2 == 0) ? RGB(33, 38, 50) : RGB(30, 34, 45));
        ObjectSetInteger(0, rBgName, OBJPROP_COLOR, (i % 2 == 0) ? RGB(33, 38, 50) : RGB(30, 34, 45));
        ObjectSetInteger(0, rBgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, rBgName, OBJPROP_ZORDER, 92); // High Z-order
    }
    
    DrawHUDRow("NEXUS_HUD_L_1", "Regime", GetStatusShort(status), GetStatusColor(status), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_2", "Consensus", DoubleToString(health * 100, 1) + "%", GetHealthColor(health), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_3", "Filters", qdd, (qdd == "PURIFYING" ? RGB(38, 166, 154) : clrGray), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_4", "Strength", GetLBMShort(lbm), GetLBMColor(lbm), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_5", "Agreement", GetZPShort(zp), GetZPColor(zp), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_6", "Slope", GetRMTShort(rmt), GetRMTColor(rmt), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_7", "Last Flip", GetQRWShort(qrw), GetQRWColor(qrw), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_8", "Inst. Avg Price", DoubleToString(instAvg, 2), RGB(200, 200, 200), baseX, rowY, panelW, corner);
}
