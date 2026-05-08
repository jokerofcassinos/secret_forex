//+------------------------------------------------------------------+
//|                                              Nexus_Observer.mq5 |
//|                                  Copyright 2026, NEXUS AGI CEO |
//+------------------------------------------------------------------+
#property copyright "NEXUS AGI CEO"
#property version   "114.00"
#property strict

// Memória de Estado
string last_payload = "";

//+------------------------------------------------------------------+
int OnInit() { 
    EventSetTimer(1); 
    ChartSetInteger(0, CHART_SHOW_TRADE_LEVELS, false); // Esconde as setas nativas feias do MT5
    ObjectsDeleteAll(0, "NEXUS_"); // LIMPEZA DE SEGURO AO CARREGAR
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
   // PROTOCOLO DE PURIFICAÇÃO GLOBAL (Anti-Fantasmas)
   ObjectsDeleteAll(0, "NEXUS_DOT_");
   ObjectsDeleteAll(0, "NEXUS_QCD_");
   ObjectsDeleteAll(0, "NEXUS_QGC_"); // Garante limpeza de traços evaporados
   
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
   string cytDanger = (ArraySize(parts) > 18) ? parts[18] : "";
   string secData = (ArraySize(parts) > 19) ? parts[19] : "0|0|0";
   string secHistory = (ArraySize(parts) > 20) ? parts[20] : "";
   string rhtStatus = (ArraySize(parts) > 21) ? parts[21] : "PURIFYING";
   string rhtHistory = (ArraySize(parts) > 22) ? parts[22] : "";
   string qcdSignal = (ArraySize(parts) > 23) ? parts[23] : "CONFINED";
   string qcdHistory = (ArraySize(parts) > 24) ? parts[24] : "";

   // Limpa as antigas poluições textuais
   ObjectDelete(0, "NEXUS_HEADER");
   // ... (rest of deletions)

   DrawModernDashboard(statusTxt, instAvgPrice, health, qddMsg, lbm_signal, z_signal, qrw_signal, secData, rmt_signal);

   // 1. ATUALIZAÇÃO DAS CAIXAS (Apenas Bordas - Revertido)
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
         
         if(ObjectFind(0, bName) < 0) ObjectCreate(0, bName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
         ObjectSetInteger(0, bName, OBJPROP_TIME, 0, iTime(_Symbol, _Period, start));
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 0, maxH);
         ObjectSetInteger(0, bName, OBJPROP_TIME, 1, iTime(_Symbol, _Period, end));
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 1, minL);
         ObjectSetInteger(0, bName, OBJPROP_COLOR, zClr);
         ObjectSetInteger(0, bName, OBJPROP_WIDTH, 2);
         ObjectSetInteger(0, bName, OBJPROP_FILL, false); // Apenas borda
         ObjectSetInteger(0, bName, OBJPROP_BACK, true);
         
         boxIdx++;
         i = end + 1;
      } else i++;
   }
   for(int k=boxIdx; k<100; k++) ObjectDelete(0, "NEXUS_ZONE_"+IntegerToString(k));

   // 1.5 ATUALIZAÇÃO ZONAS DE PERIGO CALABI-YAU (ZONAS HOLOGRÁFICAS)
   if (StringLen(cytDanger) > 0) {
      string hCyt[]; StringSplit(cytDanger, ',', hCyt);
      int totalCyt = ArraySize(hCyt);
      int boxIdxCyt = 0;
      
      for(int c=0; c < totalCyt && c < iBars(_Symbol, _Period); c++) {
         int cytScore = (int)StringToInteger(hCyt[totalCyt - 1 - c]);
         string cName = "NEXUS_CYT_HIST_" + IntegerToString(c);
         if(cytScore > 50) { 
             double pHigh = iHigh(_Symbol, _Period, c);
             double pLow = iLow(_Symbol, _Period, c);
             double atr_offset = (iHigh(_Symbol, _Period, iHighest(_Symbol, _Period, MODE_HIGH, 20, c)) - iLow(_Symbol, _Period, iLowest(_Symbol, _Period, MODE_LOW, 20, c))) * 0.05;
             if(atr_offset < 100 * _Point) atr_offset = 100 * _Point;
             
             bool isHighDanger = (iClose(_Symbol, _Period, c) > iOpen(_Symbol, _Period, c));
             
             if(ObjectFind(0, cName) < 0) ObjectCreate(0, cName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
             ObjectSetInteger(0, cName, OBJPROP_TIME, 0, iTime(_Symbol, _Period, c) - PeriodSeconds(_Period)*1);
             ObjectSetDouble(0, cName, OBJPROP_PRICE, 0, isHighDanger ? pHigh + atr_offset * 2.5 : pLow - atr_offset);
             ObjectSetInteger(0, cName, OBJPROP_TIME, 1, iTime(_Symbol, _Period, c) + PeriodSeconds(_Period)*1);
             ObjectSetDouble(0, cName, OBJPROP_PRICE, 1, isHighDanger ? pHigh + atr_offset : pLow - atr_offset * 2.5);
             
             ObjectSetInteger(0, cName, OBJPROP_COLOR, RGB(229, 57, 53)); // Vermelho mais vivo
             ObjectSetInteger(0, cName, OBJPROP_FILL, false); // APENAS BORDA para não confundir
             ObjectSetInteger(0, cName, OBJPROP_WIDTH, 2);
             ObjectSetInteger(0, cName, OBJPROP_BACK, false); // À frente do fundo, mas sem cobrir velas
             boxIdxCyt++;
          } else {
              ObjectDelete(0, cName);
          }
       }
       for(int k=boxIdxCyt; k<2000; k++) ObjectDelete(0, "NEXUS_CYT_HIST_"+IntegerToString(k));
      for(int k=0; k<100; k++) ObjectDelete(0, "NEXUS_CYT_ZONE_"+IntegerToString(k));
   }

   // 1.7 ATUALIZAÇÃO HISTÓRICA SEC (DESATIVADO)
   ObjectsDeleteAll(0, "NEXUS_SEC_H_");
   ObjectsDeleteAll(0, "NEXUS_SEC_S_");
   ObjectDelete(0, "NEXUS_SEC_HORIZON");

   // 2. ATUALIZAÇÃO DOS TACTICAL DOTS (MSNR - LONG SIGNALS)
   string hDots[]; StringSplit(historyDots, ',', hDots);
   int totalD = ArraySize(hDots);
   for(int d=0; d < totalD && d < iBars(_Symbol, _Period); d++) {
      int dotVal = (int)StringToInteger(hDots[totalD - 1 - d]);
      string dName = "NEXUS_DOT_" + IntegerToString(d);
      
      if(dotVal == 0) { ObjectDelete(0, dName); continue; }
      
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
      
      double pHigh = iHigh(_Symbol, _Period, d);
      double pLow = iLow(_Symbol, _Period, d);
      double atr_offset = (iHigh(_Symbol, _Period, iHighest(_Symbol, _Period, MODE_HIGH, 20, d)) - iLow(_Symbol, _Period, iLowest(_Symbol, _Period, MODE_LOW, 20, d))) * 0.05;
      if(atr_offset < 150 * _Point) atr_offset = 150 * _Point;

      if(ObjectFind(0, dName) < 0) ObjectCreate(0, dName, OBJ_ARROW, 0, 0, 0);
      ObjectSetInteger(0, dName, OBJPROP_TIME, iTime(_Symbol, _Period, d));
      ObjectSetDouble(0, dName, OBJPROP_PRICE, isAbove ? pHigh + atr_offset : pLow - atr_offset);
      ObjectSetInteger(0, dName, OBJPROP_ARROWCODE, isAbove ? 234 : 233);
      ObjectSetInteger(0, dName, OBJPROP_COLOR, dClr);
      ObjectSetInteger(0, dName, OBJPROP_WIDTH, 1); 
      ObjectSetInteger(0, dName, OBJPROP_ANCHOR, isAbove ? ANCHOR_BOTTOM : ANCHOR_TOP);
      ObjectSetInteger(0, dName, OBJPROP_BACK, false);
   }

   // 3. ATUALIZAÇÃO DOS SINAIS DE VOLUME
   string hSig[]; StringSplit(historySignals, ',', hSig);
   int totalS = ArraySize(hSig);
   for(int j=0; j < totalS && j < iBars(_Symbol, _Period); j++) {
      int sVal = (int)StringToInteger(hSig[totalS - 1 - j]);
      string sName = "NEXUS_SIG_" + IntegerToString(j);
      string sTextName = "NEXUS_SIG_TXT_" + IntegerToString(j);
      string sBoxName = "NEXUS_SIG_BOX_" + IntegerToString(j);
      
      if(sVal == 0) { ObjectDelete(0, sName); ObjectDelete(0, sTextName); ObjectDelete(0, sBoxName); continue; }
      
      color sClr = (sVal == 1) ? RGB(66, 165, 245) : RGB(255, 167, 38);
      double pHigh = iHigh(_Symbol, _Period, j);
      double pLow = iLow(_Symbol, _Period, j);
      bool isBuy = (sVal == 1);
      
      double atr_offset = (iHigh(_Symbol, _Period, iHighest(_Symbol, _Period, MODE_HIGH, 20, j)) - iLow(_Symbol, _Period, iLowest(_Symbol, _Period, MODE_LOW, 20, j))) * 0.05;
      if(atr_offset < 100 * _Point) atr_offset = 100 * _Point;

      if(ObjectFind(0, sName) < 0) ObjectCreate(0, sName, OBJ_ARROW, 0, 0, 0);
      ObjectSetInteger(0, sName, OBJPROP_TIME, iTime(_Symbol, _Period, j));
      ObjectSetDouble(0, sName, OBJPROP_PRICE, isBuy ? pLow - atr_offset * 1.5 : pHigh + atr_offset * 1.5);
      ObjectSetInteger(0, sName, OBJPROP_ARROWCODE, isBuy ? 233 : 234);
      ObjectSetInteger(0, sName, OBJPROP_COLOR, sClr);
      ObjectSetInteger(0, sName, OBJPROP_WIDTH, 2);
      ObjectSetInteger(0, sName, OBJPROP_ANCHOR, (isBuy ? ANCHOR_TOP : ANCHOR_BOTTOM));
      
      // Texto Minimalista para Sinais de Volume
      if(ObjectFind(0, sTextName) < 0) ObjectCreate(0, sTextName, OBJ_TEXT, 0, 0, 0);
      ObjectSetInteger(0, sTextName, OBJPROP_TIME, iTime(_Symbol, _Period, j));
      ObjectSetDouble(0, sTextName, OBJPROP_PRICE, isBuy ? pLow - atr_offset * 2.5 : pHigh + atr_offset * 2.5);
      ObjectSetString(0, sTextName, OBJPROP_TEXT, (isBuy ? "BUY " : "SELL "));
      ObjectSetString(0, sTextName, OBJPROP_FONT, "Consolas");
      ObjectSetInteger(0, sTextName, OBJPROP_FONTSIZE, 7);
      ObjectSetInteger(0, sTextName, OBJPROP_COLOR, sClr);
      ObjectSetInteger(0, sTextName, OBJPROP_ANCHOR, isBuy ? ANCHOR_TOP : ANCHOR_BOTTOM);
      
      ObjectDelete(0, sBoxName);
   }
   
   // 4. ATUALIZAÇÃO DA NUVEM QUÂNTICA (Revertido para cinemático)
   if(ArraySize(parts) > 10 && parts[10] != "") {
      string cloudParts[]; StringSplit(parts[10], ':', cloudParts);
      if(ArraySize(cloudParts) == 2) {
         double dx_val = StringToDouble(cloudParts[0]);
         string cloudBins[]; StringSplit(cloudParts[1], ',', cloudBins);
         int tCloud = ArraySize(cloudBins);
         double maxDensity = 0.0001;
         for(int b=0; b<tCloud; b++) {
            string cVal[]; StringSplit(cloudBins[b], '|', cVal);
            if(ArraySize(cVal) == 2) { double den = StringToDouble(cVal[1]); if(den > maxDensity) maxDensity = den; }
         }
         // Suavização Visual: Redução da extensão horizontal para não cobrir o gráfico todo
         datetime tStart = iTime(_Symbol, _Period, 0); // Começa no candle atual
         datetime tEnd = TimeCurrent() + PeriodSeconds(_Period) * 10; // Projeta um pouco para frente
         double dx = dx_val;
         double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         for(int b=0; b<tCloud; b++) {
            string cVal[]; StringSplit(cloudBins[b], '|', cVal);
            if(ArraySize(cVal) != 2) continue;
            double pLevel = StringToDouble(cVal[0]);
            double den = StringToDouble(cVal[1]);
            string bName = "NEXUS_QC_" + IntegerToString(b);
            string tagName = "NEXUS_QCTAG_" + IntegerToString(b);
            
            // Filtro mais rigoroso: Mostra apenas nuvens com >30% da densidade máxima
            if(den < maxDensity * 0.30) { ObjectDelete(0, bName); ObjectDelete(0, tagName); continue; }
            
            double ratio = den / maxDensity;
            ratio = MathPow(ratio, 3.0); if(ratio > 1.0) ratio = 1.0;
            uchar rVal, gVal, bVal;
            
            // Cores mais escuras e discretas para o fundo
            if(pLevel > currentPrice) { 
                rVal = (uchar)(10 + (80 - 10) * ratio); gVal = (uchar)(12 + (15 - 12) * ratio); bVal = (uchar)(18 + (15 - 18) * ratio); 
            } else { 
                rVal = (uchar)(10 + (5 - 10) * ratio); gVal = (uchar)(12 + (60 - 12) * ratio); bVal = (uchar)(18 + (80 - 18) * ratio); 
            }
            
            if(ObjectFind(0, bName) < 0) ObjectCreate(0, bName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
            ObjectSetInteger(0, bName, OBJPROP_TIME, 0, tStart);
            ObjectSetDouble(0, bName, OBJPROP_PRICE, 0, pLevel + (dx/2.0));
            ObjectSetInteger(0, bName, OBJPROP_TIME, 1, tEnd);
            ObjectSetDouble(0, bName, OBJPROP_PRICE, 1, pLevel - (dx/2.0));
            ObjectSetInteger(0, bName, OBJPROP_COLOR, RGB(rVal, gVal, bVal));
            ObjectSetInteger(0, bName, OBJPROP_FILL, true);
            ObjectSetInteger(0, bName, OBJPROP_BACK, true);
            if(ratio > 0.95) {
                if(ObjectFind(0, tagName) < 0) ObjectCreate(0, tagName, OBJ_ARROW_RIGHT_PRICE, 0, 0, 0);
                ObjectSetInteger(0, tagName, OBJPROP_TIME, 0, tEnd);
                ObjectSetDouble(0, tagName, OBJPROP_PRICE, 0, pLevel);
                ObjectSetInteger(0, tagName, OBJPROP_COLOR, clrGold);
            } else ObjectDelete(0, tagName);
         }
         for(int k=tCloud; k<200; k++) ObjectDelete(0, "NEXUS_QC_"+IntegerToString(k));
      }
   }

   // 5. ATUALIZAÇÃO DA CROMODINÂMICA (MARKET QCD - SHORT SIGNALS)
   if(StringLen(qcdHistory) > 0) {
      string hQcd[]; StringSplit(qcdHistory, ',', hQcd);
      int tQcd = ArraySize(hQcd);
      for(int q=0; q < tQcd && q < iBars(_Symbol, _Period); q++) {
         int qVal = (int)StringToInteger(hQcd[tQcd - 1 - q]);
         string qName = "NEXUS_QCD_" + IntegerToString(q);
         string qTextName = "NEXUS_QCD_TXT_" + IntegerToString(q);
         string qBoxName = "NEXUS_QCD_BOX_" + IntegerToString(q);
         
         if(qVal == 0) { ObjectDelete(0, qName); ObjectDelete(0, qTextName); ObjectDelete(0, qBoxName); continue; }
         
         color corporateClr = (qVal == 1) ? RGB(38, 166, 154) : RGB(239, 83, 80);
         double pHigh = iHigh(_Symbol, _Period, q);
         double pLow = iLow(_Symbol, _Period, q);
         bool isBuy = (qVal == 1);
         
         double atr_offset = (iHigh(_Symbol, _Period, iHighest(_Symbol, _Period, MODE_HIGH, 20, q)) - iLow(_Symbol, _Period, iLowest(_Symbol, _Period, MODE_LOW, 20, q))) * 0.05;
         if(atr_offset < 150 * _Point) atr_offset = 150 * _Point;

         double symPrice, boxCenterPrice;
         if(isBuy) {
            symPrice = pLow - atr_offset * 2.5;         // Símbolo ABAIXO da vela
            boxCenterPrice = pLow - atr_offset * 6.5;    // Caixa ABAIXO do símbolo
         } else {
            symPrice = pHigh + atr_offset * 2.5;        // Símbolo ACIMA da vela
            boxCenterPrice = pHigh + atr_offset * 6.5;   // Caixa ACIMA do símbolo
         }
         
         if(ObjectFind(0, qName) < 0) ObjectCreate(0, qName, OBJ_ARROW, 0, 0, 0);
         ObjectSetInteger(0, qName, OBJPROP_TIME, iTime(_Symbol, _Period, q));
         ObjectSetDouble(0, qName, OBJPROP_PRICE, symPrice);
         ObjectSetInteger(0, qName, OBJPROP_ARROWCODE, isBuy ? 233 : 234); 
         ObjectSetInteger(0, qName, OBJPROP_COLOR, corporateClr);
         ObjectSetInteger(0, qName, OBJPROP_WIDTH, 2); // Símbolo sutil
         ObjectSetInteger(0, qName, OBJPROP_ANCHOR, (isBuy ? ANCHOR_TOP : ANCHOR_BOTTOM));
         ObjectSetInteger(0, qName, OBJPROP_BACK, false);
         
         string labelTxt = (isBuy ? "▲ SHORT " : "▼ SHORT ") + DoubleToString(iClose(_Symbol, _Period, q), _Digits);
         
         // Remove a caixa antiga se existir
         ObjectDelete(0, qBoxName);
         
         // Linha guia conectando o texto ao preço
         string qLineName = "NEXUS_QCD_LINE_" + IntegerToString(q);
         if(ObjectFind(0, qLineName) < 0) ObjectCreate(0, qLineName, OBJ_TREND, 0, 0, 0, 0, 0);
         ObjectSetInteger(0, qLineName, OBJPROP_TIME, 0, iTime(_Symbol, _Period, q));
         ObjectSetDouble(0, qLineName, OBJPROP_PRICE, 0, isBuy ? symPrice - atr_offset : symPrice + atr_offset);
         ObjectSetInteger(0, qLineName, OBJPROP_TIME, 1, iTime(_Symbol, _Period, q));
         ObjectSetDouble(0, qLineName, OBJPROP_PRICE, 1, boxCenterPrice);
         ObjectSetInteger(0, qLineName, OBJPROP_COLOR, corporateClr);
         ObjectSetInteger(0, qLineName, OBJPROP_STYLE, STYLE_DOT);
         ObjectSetInteger(0, qLineName, OBJPROP_RAY_RIGHT, false);
         ObjectSetInteger(0, qLineName, OBJPROP_BACK, true);

         // Texto Minimalista
         if(ObjectFind(0, qTextName) < 0) ObjectCreate(0, qTextName, OBJ_TEXT, 0, 0, 0);
         ObjectSetInteger(0, qTextName, OBJPROP_TIME, iTime(_Symbol, _Period, q));
         ObjectSetDouble(0, qTextName, OBJPROP_PRICE, isBuy ? boxCenterPrice - atr_offset : boxCenterPrice + atr_offset);
         ObjectSetString(0, qTextName, OBJPROP_TEXT, labelTxt);
         ObjectSetString(0, qTextName, OBJPROP_FONT, "Consolas");
         ObjectSetInteger(0, qTextName, OBJPROP_FONTSIZE, 8);
         ObjectSetInteger(0, qTextName, OBJPROP_COLOR, corporateClr);
         ObjectSetInteger(0, qTextName, OBJPROP_ANCHOR, isBuy ? ANCHOR_TOP : ANCHOR_BOTTOM);
         ObjectSetInteger(0, qTextName, OBJPROP_BACK, false);
      }
   }

   // 6. ATUALIZAÇÃO DA DINÂMICA DE FLUIDOS (LBM ZONAS DE SQUEEZE/COMPRESSÃO)
   string hLbm[]; StringSplit(parts[15], ',', hLbm);
   int tLbm = ArraySize(hLbm);
   for(int k=0; k < tLbm && k < iBars(_Symbol, _Period); k++) {
      int lVal = (int)StringToInteger(hLbm[tLbm - 1 - k]);
      string lName = "NEXUS_LBM_" + IntegerToString(k);
      
      if(lVal == 0) { ObjectDelete(0, lName); continue; }
      
      color lClr = (lVal == 1) ? RGB(66, 165, 245) : (lVal == 2 ? RGB(171, 71, 188) : clrGold); 
      double pHigh = iHigh(_Symbol, _Period, k);
      double pLow = iLow(_Symbol, _Period, k);
      
      double atr_offset = (iHigh(_Symbol, _Period, iHighest(_Symbol, _Period, MODE_HIGH, 20, k)) - iLow(_Symbol, _Period, iLowest(_Symbol, _Period, MODE_LOW, 20, k))) * 0.05;
      if(atr_offset < 100 * _Point) atr_offset = 100 * _Point;

      if(ObjectFind(0, lName) < 0) ObjectCreate(0, lName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
      ObjectSetInteger(0, lName, OBJPROP_TIME, 0, iTime(_Symbol, _Period, k) - PeriodSeconds(_Period)*1);
      ObjectSetInteger(0, lName, OBJPROP_TIME, 1, iTime(_Symbol, _Period, k) + PeriodSeconds(_Period)*1);
      
      if(lVal == 1) { // Rupture Bull (Blue)
          ObjectSetDouble(0, lName, OBJPROP_PRICE, 0, pLow - atr_offset);
          ObjectSetDouble(0, lName, OBJPROP_PRICE, 1, pLow - atr_offset * 3.0);
      } else if(lVal == 2) { // Rupture Bear (Purple)
          ObjectSetDouble(0, lName, OBJPROP_PRICE, 0, pHigh + atr_offset * 3.0);
          ObjectSetDouble(0, lName, OBJPROP_PRICE, 1, pHigh + atr_offset);
      } else if(lVal == 3) { // Quantum Squeeze (Gold)
          ObjectSetDouble(0, lName, OBJPROP_PRICE, 0, pHigh + atr_offset * 1.5);
          ObjectSetDouble(0, lName, OBJPROP_PRICE, 1, pLow - atr_offset * 1.5);
      }
      
      ObjectSetInteger(0, lName, OBJPROP_COLOR, lClr);
      ObjectSetInteger(0, lName, OBJPROP_FILL, true);
      ObjectSetInteger(0, lName, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, lName, OBJPROP_BACK, true);
   }

   // 7. DECAIMENTO HAWKING (QGC) - ZONAS DE EVAPORAÇÃO
   string qgcData = (ArraySize(parts) > 25) ? parts[25] : "";
   int qgcBoxIdx = 0;
   if(StringLen(qgcData) > 0) {
      string qgcLines[]; StringSplit(qgcData, ',', qgcLines);
      for(int q=0; q < ArraySize(qgcLines); q++) {
         string qParts[]; StringSplit(qgcLines[q], '|', qParts);
         if(ArraySize(qParts) == 3) {
            int age = (int)StringToInteger(qParts[0]);
            double centerPrice = StringToDouble(qParts[1]);
            double massNorm = StringToDouble(qParts[2]);
            
            string qLineName = "NEXUS_QGC_" + IntegerToString(qgcBoxIdx);
            
            ObjectDelete(0, qLineName); // Força limpeza 
            if(ObjectFind(0, qLineName) < 0) ObjectCreate(0, qLineName, OBJ_TREND, 0, 0, 0, 0, 0);
            
            ObjectSetInteger(0, qLineName, OBJPROP_TIME, 0, iTime(_Symbol, _Period, age));
            ObjectSetDouble(0, qLineName, OBJPROP_PRICE, 0, centerPrice);
            ObjectSetInteger(0, qLineName, OBJPROP_TIME, 1, iTime(_Symbol, _Period, 0));
            ObjectSetDouble(0, qLineName, OBJPROP_PRICE, 1, centerPrice);
            
            ObjectSetInteger(0, qLineName, OBJPROP_COLOR, RGB(0, 255, 255)); // Neon Cyan
            ObjectSetInteger(0, qLineName, OBJPROP_STYLE, STYLE_SOLID);
            ObjectSetInteger(0, qLineName, OBJPROP_WIDTH, (int)MathMax(1, MathMin(10, massNorm * 2.0))); 
            ObjectSetInteger(0, qLineName, OBJPROP_RAY_RIGHT, true); 
            ObjectSetInteger(0, qLineName, OBJPROP_BACK, true);
            
            qgcBoxIdx++;
         }
      }
   }
   // 9. QUANTUM DENSITY CLOUDS (SOMBREAMENTO DE FUNDO - HEATMAP v4.2)
   string lbmHist = parts[15];
   string lParts[]; StringSplit(lbmHist, ',', lParts);
   int totalL = ArraySize(lParts);
   int cloudIdx = 0;
   
   for(int k=0; k < totalL && k < iBars(_Symbol, _Period); k++) {
      int lVal = (int)StringToInteger(lParts[totalL - 1 - k]);
      if(lVal == 0) continue;
      
      // Fusão Visual: Tenta agrupar candles com a mesma polaridade em um bloco único
      int startK = k;
      int endK = k;
      while(endK + 1 < totalL && endK + 1 < iBars(_Symbol, _Period)) {
         int nextVal = (int)StringToInteger(lParts[totalL - 1 - (endK + 1)]);
         if(nextVal == lVal) endK++; else break;
      }
      
      string cName = "NEXUS_CLOUD_" + IntegerToString(cloudIdx);
      color cClr = (lVal == 1) ? RGB(0, 25, 20) : (lVal == 2 ? RGB(35, 8, 15) : RGB(35, 35, 8));
      
      if(ObjectFind(0, cName) < 0) ObjectCreate(0, cName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
      ObjectSetInteger(0, cName, OBJPROP_TIME, 0, iTime(_Symbol, _Period, startK) + PeriodSeconds(_Period)/2);
      ObjectSetDouble(0, cName, OBJPROP_PRICE, 0, ChartGetDouble(0, CHART_PRICE_MAX));
      ObjectSetInteger(0, cName, OBJPROP_TIME, 1, iTime(_Symbol, _Period, endK) - PeriodSeconds(_Period)/2);
      ObjectSetDouble(0, cName, OBJPROP_PRICE, 1, ChartGetDouble(0, CHART_PRICE_MIN));
      
      ObjectSetInteger(0, cName, OBJPROP_COLOR, cClr);
      ObjectSetInteger(0, cName, OBJPROP_FILL, true);
      ObjectSetInteger(0, cName, OBJPROP_BACK, true);
      ObjectSetInteger(0, cName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
      
      cloudIdx++;
      k = endK; // Pula para o fim do bloco fundido
   }
   for(int k=cloudIdx; k<500; k++) ObjectDelete(0, "NEXUS_CLOUD_"+IntegerToString(k));

   ChartRedraw(0);
}

void DrawWyckoffHUD(string score, string phase, string div, string strength)
{
    int panelW = 220; int panelH = 140; int corner = CORNER_RIGHT_LOWER; 
    int baseX = 50; int baseY = 100; // AFSTADO DO CANTO PARA NÃO BATER NAS ABAS
    string bgName = "NEXUS_WYCKOFF_BG"; if(ObjectFind(0, bgName) < 0) ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, bgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, baseX); ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, baseY);
    ObjectSetInteger(0, bgName, OBJPROP_XSIZE, panelW); ObjectSetInteger(0, bgName, OBJPROP_YSIZE, panelH);
    ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, RGB(15, 18, 25));
    ObjectSetInteger(0, bgName, OBJPROP_COLOR, RGB(45, 50, 65));
    ObjectSetInteger(0, bgName, OBJPROP_ZORDER, 200); // SEMPRE NO TOPO

    DrawHUDText("W_TITLE", "WYCKOFF PRECISION", baseX + 15, baseY + panelH - 25, RGB(38, 166, 154), 9, true, corner);
    
    int rowY = baseY + 100; int rowH = 18;
    DrawHUDRowWyck("W_SCORE", "NEXUS Score", score + " (Optimal)", RGB(66, 165, 245), baseX, rowY, panelW, corner); rowY -= rowH;
    DrawHUDRowWyck("W_PHASE", "Phase", phase, RGB(255, 213, 79), baseX, rowY, panelW, corner); rowY -= rowH;
    DrawHUDRowWyck("W_DIV", "Divergence", div, (div == "None" ? clrGray : RGB(239, 83, 80)), baseX, rowY, panelW, corner); rowY -= rowH;
    DrawHUDRowWyck("W_STR", "Strength", strength, clrWhite, baseX, rowY, panelW, corner);
}

void DrawHUDRowWyck(string id, string label, string val, color valClr, int baseX, int y, int panelW, int corner)
{
    DrawHUDText(id + "_L", label, baseX + panelW - 15, y, RGB(140, 140, 145), 8, true, corner); 
    DrawHUDText(id + "_V", val, baseX + 15, y, valClr, 8, false, corner);
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
            ObjectSetInteger(0, inName, OBJPROP_ARROWCODE, 119);
            ObjectSetInteger(0, inName, OBJPROP_COLOR, (type == DEAL_TYPE_BUY) ? RGB(66, 165, 245) : RGB(171, 71, 188));
            ObjectSetInteger(0, inName, OBJPROP_WIDTH, 2);
            ObjectSetInteger(0, inName, OBJPROP_ANCHOR, (type == DEAL_TYPE_BUY) ? ANCHOR_TOP : ANCHOR_BOTTOM);
            ObjectSetInteger(0, inName, OBJPROP_BACK, false);
        }
    }
    HistorySelect(start_time, TimeCurrent());
    for(int i=0; i<total; i++) {
        ulong ticket = HistoryDealGetTicket(i);
        if(HistoryDealGetString(ticket, DEAL_SYMBOL) != _Symbol) continue;
        long entry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
        if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_INOUT) {
            ulong pos_id = HistoryDealGetInteger(ticket, DEAL_POSITION_ID);
            double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
            string outName = "NEXUS_TOUT_" + IntegerToString(ticket);
            if(ObjectFind(0, outName) >= 0) continue;
            if(HistorySelectByPosition(pos_id)) {
                int pTotal = HistoryDealsTotal();
                datetime in_time = 0; double in_price = 0;
                for(int j=0; j<pTotal; j++) {
                    ulong p_ticket = HistoryDealGetTicket(j);
                    if(HistoryDealGetInteger(p_ticket, DEAL_ENTRY) == DEAL_ENTRY_IN) { in_time = (datetime)HistoryDealGetInteger(p_ticket, DEAL_TIME); in_price = HistoryDealGetDouble(p_ticket, DEAL_PRICE); break; }
                }
                if(in_time != 0) {
                    datetime out_time = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
                    double out_price = HistoryDealGetDouble(ticket, DEAL_PRICE);
                    string lineName = "NEXUS_TLINE_" + IntegerToString(ticket);
                    ObjectCreate(0, lineName, OBJ_TREND, 0, in_time, in_price, out_time, out_price);
                    ObjectSetInteger(0, lineName, OBJPROP_COLOR, (profit > 0) ? RGB(38, 166, 154) : RGB(239, 83, 80));
                    ObjectSetInteger(0, lineName, OBJPROP_STYLE, STYLE_SOLID);
                    ObjectSetInteger(0, lineName, OBJPROP_WIDTH, 2);
                    ObjectSetInteger(0, lineName, OBJPROP_RAY_RIGHT, false);
                    ObjectSetInteger(0, lineName, OBJPROP_BACK, true);
                    ObjectCreate(0, outName, OBJ_ARROW, 0, out_time, out_price);
                    ObjectSetInteger(0, outName, OBJPROP_ARROWCODE, 162);
                    ObjectSetInteger(0, outName, OBJPROP_COLOR, (profit > 0) ? RGB(38, 166, 154) : RGB(239, 83, 80));
                    ObjectSetInteger(0, outName, OBJPROP_WIDTH, 3);
                    ObjectSetInteger(0, outName, OBJPROP_ANCHOR, ANCHOR_CENTER);
                    ObjectSetInteger(0, outName, OBJPROP_BACK, false);
                    datetime box_start = out_time + PeriodSeconds(_Period) * 1;
                    datetime box_end = out_time + PeriodSeconds(_Period) * 6;
                    double box_margin = out_price * 0.0004;
                    string boxName = "NEXUS_TBOX_" + IntegerToString(ticket);
                    ObjectCreate(0, boxName, OBJ_RECTANGLE, 0, box_start, out_price + box_margin, box_end, out_price - box_margin);
                    ObjectSetInteger(0, boxName, OBJPROP_COLOR, (profit > 0) ? RGB(0, 105, 92) : RGB(183, 28, 28));
                    ObjectSetInteger(0, boxName, OBJPROP_FILL, true);
                    ObjectSetInteger(0, boxName, OBJPROP_BACK, true);
                    string textName = "NEXUS_TTEXT_" + IntegerToString(ticket);
                    ObjectCreate(0, textName, OBJ_TEXT, 0, box_start + PeriodSeconds(_Period) * 1, out_price);
                    ObjectSetString(0, textName, OBJPROP_TEXT, (profit > 0 ? "+" : "") + DoubleToString(profit, 2));
                    ObjectSetInteger(0, textName, OBJPROP_COLOR, clrWhite);
                    ObjectSetInteger(0, textName, OBJPROP_FONTSIZE, 9);
                    ObjectSetInteger(0, textName, OBJPROP_ANCHOR, ANCHOR_LEFT);
                    ObjectSetInteger(0, textName, OBJPROP_BACK, true);
                }
            }
        }
    }
    HistorySelect(start_time, TimeCurrent());
}

string GetStatusShort(string status) {
    string res = "Neutral Regime";
    if(StringFind(status, "TSUNAMI_BULL") >= 0) res = "Bull Tsunami";
    else if(StringFind(status, "TSUNAMI_BEAR") >= 0) res = "Bear Tsunami";
    else if(StringFind(status, "BULL_PREVISAO") >= 0) res = "Bull Pre-Ignition";
    else if(StringFind(status, "BEAR_PREVISAO") >= 0) res = "Bear Pre-Ignition";
    if(StringFind(status, "ALERTA TOPOL") >= 0) res += " [!]";
    if(StringFind(status, "TRAP") >= 0) res += " [TRAP]";
    return res;
}
color GetStatusColor(string status) {
    if(StringFind(status, "ALERTA TOPOL") >= 0) return RGB(255, 82, 82);
    if(StringFind(status, "TRAP") >= 0) return RGB(255, 202, 40);
    if(StringFind(status, "BULL") >= 0) return RGB(38, 166, 154);
    if(StringFind(status, "BEAR") >= 0) return RGB(239, 83, 80);
    return RGB(120, 123, 134);
}
color GetHealthColor(double h) { return (h < 0.3) ? RGB(239, 83, 80) : (h < 0.6 ? RGB(255, 167, 38) : RGB(38, 166, 154)); }
string GetLBMShort(string lbm) { 
    if(lbm == "FLUID_RUPTURE_BULL") return "Rupture Bull"; 
    if(lbm == "FLUID_RUPTURE_BEAR") return "Rupture Bear"; 
    if(lbm == "BOSONIC_SQUEEZE") return "Quantum Squeeze";
    return "Laminar Flow"; 
}
color GetLBMColor(string lbm) { 
    if(lbm == "FLUID_RUPTURE_BULL") return RGB(66, 165, 245); 
    if(lbm == "FLUID_RUPTURE_BEAR") return RGB(171, 71, 188); 
    if(lbm == "BOSONIC_SQUEEZE") return clrGold;
    return RGB(120, 123, 134); 
}
string GetZPShort(string zp) { if(zp == "NEUTRAL" || zp == "") return "Neutral"; if(StringFind(zp, "Z_PINCH_") >= 0) { string sub[]; StringSplit(zp, '_', sub); if(ArraySize(sub) >= 3) return sub[2] + " " + sub[3]; } return zp; }
color GetZPColor(string zp) { return (zp == "NEUTRAL" || zp == "") ? RGB(120, 123, 134) : RGB(255, 202, 40); }
string GetQRWShort(string qrw) { if(qrw == "NEUTRAL" || qrw == "") return "No Interf."; if(qrw == "HIDDEN_ACCUMULATION_BULL") return "Accumulation"; if(qrw == "HIDDEN_DISTRIBUTION_BEAR") return "Distribution"; return qrw; }
color GetQRWColor(string qrw) { if(qrw == "HIDDEN_ACCUMULATION_BULL") return RGB(38, 198, 218); if(qrw == "HIDDEN_DISTRIBUTION_BEAR") return RGB(255, 167, 38); return RGB(120, 123, 134); }
string GetRMTShort(string rmt) { 
    if(StringFind(rmt, "PURE_SIGNAL") >= 0) {
        string res = rmt;
        StringReplace(res, "PURE_SIGNAL_", "Pure ");
        return res;
    }
    return "Noise"; 
}
color GetRMTColor(string rmt) { if(StringFind(rmt, "PURE_SIGNAL") >= 0) return RGB(255, 213, 79); return RGB(120, 123, 134); }
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
    ObjectSetInteger(0, name, OBJPROP_ZORDER, 100);
    ObjectSetInteger(0, name, OBJPROP_BACK, false);
}
color RGB(uchar r, uchar g, uchar b) { return (color)((b << 16) | (g << 8) | r); }
void DrawHUDRow(string id, string label, string val, color valClr, int baseX, int y, int panelW, int corner=CORNER_LEFT_UPPER)
{
    DrawHUDText(id + "_L", label, baseX + 15, y, RGB(140, 140, 145), 9, false, corner); 
    DrawHUDText(id + "_V", val, baseX + panelW - 15, y, valClr, 9, true, corner);
}
void DrawModernDashboard(string status, double instAvg, double health, string qdd, string lbm, string zp, string qrw, string sec, string rmt)
{
    int panelW = 280; int panelH = 285; int corner = CORNER_LEFT_UPPER; int baseX = 20; int baseY = 30;
    string bgName = "NEXUS_HUD_BASE"; if(ObjectFind(0, bgName) < 0) ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, bgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, baseX); ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, baseY);
    ObjectSetInteger(0, bgName, OBJPROP_XSIZE, panelW); ObjectSetInteger(0, bgName, OBJPROP_YSIZE, panelH); 
    color mainBg = RGB(15, 18, 25);
    ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, mainBg);
    ObjectSetInteger(0, bgName, OBJPROP_COLOR, RGB(45, 50, 65)); // Borda sutil
    ObjectSetInteger(0, bgName, OBJPROP_BORDER_TYPE, BORDER_FLAT); 
    ObjectSetInteger(0, bgName, OBJPROP_ZORDER, 90);

    string hBgName = "NEXUS_HUD_HEADER_BG"; if(ObjectFind(0, hBgName) < 0) ObjectCreate(0, hBgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, hBgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, hBgName, OBJPROP_XDISTANCE, baseX); ObjectSetInteger(0, hBgName, OBJPROP_YDISTANCE, baseY);
    ObjectSetInteger(0, hBgName, OBJPROP_XSIZE, panelW); ObjectSetInteger(0, hBgName, OBJPROP_YSIZE, 35); 
    color headBg = RGB(25, 30, 42);
    ObjectSetInteger(0, hBgName, OBJPROP_BGCOLOR, headBg);
    ObjectSetInteger(0, hBgName, OBJPROP_COLOR, RGB(0, 150, 136)); // Acento teal superior
    ObjectSetInteger(0, hBgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, hBgName, OBJPROP_ZORDER, 95);

    DrawHUDText("NEXUS_HUD_TITLE", "AETHELGARD :: QUANTUM CORE", baseX + 15, baseY + 10, RGB(220, 225, 235), 10, false, corner);
    
    int rowY = baseY + 45; int rowH = 19;
    for(int k=0; k<12; k++) { // Força atualização das propriedades de todas as 12 linhas
        string rBgName = "NEXUS_HUD_ROW_BG_" + IntegerToString(k); if(ObjectFind(0, rBgName) < 0) ObjectCreate(0, rBgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, rBgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, rBgName, OBJPROP_XDISTANCE, baseX); ObjectSetInteger(0, rBgName, OBJPROP_YDISTANCE, baseY + 36 + (k * rowH));
        ObjectSetInteger(0, rBgName, OBJPROP_XSIZE, panelW); ObjectSetInteger(0, rBgName, OBJPROP_YSIZE, rowH);
        color rCol = (k % 2 == 0) ? RGB(20, 24, 32) : RGB(15, 18, 25);
        ObjectSetInteger(0, rBgName, OBJPROP_BGCOLOR, rCol); 
        ObjectSetInteger(0, rBgName, OBJPROP_COLOR, rCol); 
        ObjectSetInteger(0, rBgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, rBgName, OBJPROP_ZORDER, 92);
    }

    string sSub[]; StringSplit(sec, '|', sSub);
    bool isSing = (ArraySize(sSub) >= 1 && StringToInteger(sSub[0]) == 1);

    DrawHUDRow("NEXUS_HUD_L_1", "Regime", GetStatusShort(status), GetStatusColor(status), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_2", "Confidence", DoubleToString(health * 100, 1) + "%", GetHealthColor(health), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_3", "Entanglement", qdd, (qdd == "PURIFYING" ? RGB(38, 166, 154) : clrGray), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_4", "LBM Fluid", GetLBMShort(lbm), GetLBMColor(lbm), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_5", "AdS/CFT Bulk", GetZPShort(zp), GetZPColor(zp), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_6", "QRW Flux", GetQRWShort(qrw), GetQRWColor(qrw), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_7", "S-Matrix Amp", GetRMTShort(rmt), GetRMTColor(rmt), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_8", "Inst. Avg", DoubleToString(instAvg, 2), RGB(200, 200, 200), baseX, rowY, panelW, corner);

    // Limpar objetos de alerta residuais se existirem
    ObjectDelete(0, "NEXUS_SEC_ICON");
    ObjectDelete(0, "NEXUS_SEC_ALERT");
}
