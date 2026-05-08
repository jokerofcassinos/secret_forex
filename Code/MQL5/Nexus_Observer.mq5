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
   
   res = WebRequest("GET", url, cookie, NULL, 500, post, 0, result, headers);
   if(res == 200) {
      string response = CharArrayToString(result);
      if(response != last_payload) { 
         StringTrimRight(response);
         ParseAndDraw(response);
         last_payload = response;
      }
   }
}

void ParseAndDraw(string data)
{
   // PROTOCOLO DE PURIFICAÇÃO SELETIVA (Apenas o que realmente muda muito)
   ObjectsDeleteAll(0, "NEXUS_DOT_");
   ObjectsDeleteAll(0, "NEXUS_QCD_");
   // NEXUS_LBM e NEXUS_CLOUD agora são persistentes para evitar flickering
   
   string parts[];
   StringSplit(data, ';', parts);
   if(ArraySize(parts) < 29) return;


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
   string qrw_signal = "OFFLINE";
   string ricci_c = (ArraySize(parts) > 16) ? parts[16] : "0.00";
   string h_entropy = (ArraySize(parts) > 17) ? parts[17] : "0.00";
   string cytDanger = (ArraySize(parts) > 18) ? parts[18] : "";
   string secData = (ArraySize(parts) > 19) ? parts[19] : "0|0|0";
   string secHistory = (ArraySize(parts) > 20) ? parts[20] : "";
   string rhtStatus = (ArraySize(parts) > 21) ? parts[21] : "PURIFYING";
   string is_collapsed = (ArraySize(parts) > 22) ? parts[22] : "0";
   string qcdSignal = (ArraySize(parts) > 23) ? parts[23] : "CONFINED";
   string qcdHistory = (ArraySize(parts) > 24) ? parts[24] : "";
   string rhtHistory = (ArraySize(parts) > 28) ? parts[28] : "";
   string rhtFlash = (ArraySize(parts) > 29) ? parts[29] : "0";
   string rhtFlashHistory = (ArraySize(parts) > 30) ? parts[30] : "";

   // Limpa as antigas poluições textuais
   ObjectDelete(0, "NEXUS_HEADER");
   // ... (rest of deletions)

   DrawModernDashboard(statusTxt, instAvgPrice, health, rhtStatus, lbm_signal, z_signal, qrw_signal, secData, rmt_signal, ricci_c, h_entropy, (is_collapsed == "1"));

   // --- 1.8 RHT THERMODYNAMIC VISUALS (IGNIÇÕES HISTÓRICAS) ---
   if(StringLen(rhtFlashHistory) > 0) {
      string fSteps[]; StringSplit(rhtFlashHistory, ',', fSteps);
      int totalF = ArraySize(fSteps);
      for(int s=0; s < totalF && s < 100; s++) {
         int fVal = (int)StringToInteger(fSteps[totalF - 1 - s]);
         if(fVal != 0) {
            string fName = "NEXUS_SPARK_HIST_" + IntegerToString(s);
            color fClr = (fVal == 1) ? RGB(0, 255, 255) : RGB(255, 50, 50);
            int arrowCode = (fVal == 1) ? 233 : 234;
            
            double pricePos = (fVal == 1) ? iLow(_Symbol, _Period, s) - 200 * _Point : iHigh(_Symbol, _Period, s) + 200 * _Point;
            if(ObjectFind(0, fName) < 0) ObjectCreate(0, fName, OBJ_ARROW, 0, iTime(_Symbol, _Period, s), pricePos);
            ObjectSetInteger(0, fName, OBJPROP_TIME, 0, iTime(_Symbol, _Period, s));
            ObjectSetDouble(0, fName, OBJPROP_PRICE, 0, pricePos);
            ObjectSetInteger(0, fName, OBJPROP_ARROWCODE, arrowCode);
            ObjectSetInteger(0, fName, OBJPROP_COLOR, fClr);
            ObjectSetInteger(0, fName, OBJPROP_WIDTH, 2);
            ObjectSetInteger(0, fName, OBJPROP_ANCHOR, (fVal == 1) ? ANCHOR_TOP : ANCHOR_BOTTOM);
         } else ObjectDelete(0, "NEXUS_SPARK_HIST_" + IntegerToString(s));
      }
   }

   // 1.9 [HEATMAP DELETED FOR CLARITY]
   ObjectsDeleteAll(0, "NEXUS_HEAT_");

   // --- [QRW & WYCKOFF DISABLED] ---
   ObjectsDeleteAll(0, "NEXUS_SINGULARITY_");
   ObjectsDeleteAll(0, "NEXUS_WYCK_");

   // 1. ATUALIZAÇÃO DAS CAIXAS (Apenas Bordas - Revertido)
   string hReg[]; StringSplit(historyRegimes, ',', hReg);
   int totalR = ArraySize(hReg);
   
   int i = 0; int boxIdx = 0;
   while(i < totalR && i < iBars(_Symbol, _Period)) {
      string val = hReg[totalR - 1 - i];
      string sub[]; StringSplit(val, '|', sub);
      if(ArraySize(sub) < 1) { i++; continue; }
      int r = (int)StringToInteger(sub[0]);
      
      if(r != 0) {
         int start = i; int end = i;
         while(end + 1 < totalR && end + 1 < iBars(_Symbol, _Period)) {
            string nextVal = hReg[totalR - 1 - (end + 1)];
            string nSub[]; StringSplit(nextVal, '|', nSub);
            if(ArraySize(nSub) > 0 && (int)StringToInteger(nSub[0]) == r) end++; else break;
         }
         
         double maxH = 0; double minL = 9999999;
         for(int k=start; k<=end; k++) {
            maxH = MathMax(maxH, iHigh(_Symbol, _Period, k));
            minL = MathMin(minL, iLow(_Symbol, _Period, k));
         }
         
         string bName = "NEXUS_ZONE_" + IntegerToString(boxIdx);
         color zClr = (r == 1) ? RGB(0, 180, 180) : RGB(200, 50, 50);
         
         if(ObjectFind(0, bName) < 0) ObjectCreate(0, bName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
         ObjectSetInteger(0, bName, OBJPROP_TIME, 0, iTime(_Symbol, _Period, start));
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 0, maxH);
         ObjectSetInteger(0, bName, OBJPROP_TIME, 1, iTime(_Symbol, _Period, end));
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 1, minL);
         ObjectSetInteger(0, bName, OBJPROP_COLOR, zClr);
         ObjectSetInteger(0, bName, OBJPROP_WIDTH, 1);
         ObjectSetInteger(0, bName, OBJPROP_FILL, false); 
         ObjectSetInteger(0, bName, OBJPROP_BACK, true); 
         ObjectSetInteger(0, bName, OBJPROP_ZORDER, 0);
         
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
         int cytVal = (int)StringToInteger(hCyt[totalCyt - 1 - c]);
         string cName = "NEXUS_CYT_HIST_" + IntegerToString(c);
         
         // Threshold Alpha: 1.5 sigma (enviado como 150 pelo Python para Histórico)
         if(cytVal >= 150) { 
             datetime tStart = iTime(_Symbol, _Period, c);
             datetime tEnd = tStart + PeriodSeconds(_Period);
             
             if(ObjectFind(0, cName) < 0) ObjectCreate(0, cName, OBJ_RECTANGLE, 0, tStart, 2000000.0, tEnd, 0.0);
             else {
                ObjectSetInteger(0, cName, OBJPROP_TIME, 0, tStart);
                ObjectSetDouble(0, cName, OBJPROP_PRICE, 0, 2000000.0);
                ObjectSetInteger(0, cName, OBJPROP_TIME, 1, tEnd);
                ObjectSetDouble(0, cName, OBJPROP_PRICE, 1, 0.0);
             }
             
             // Estética: Dark Red Translucent (Ebony Stealth Harmonic)
             ObjectSetInteger(0, cName, OBJPROP_COLOR, (cytVal >= 250) ? RGB(255, 30, 30) : RGB(80, 20, 30)); 
             ObjectSetInteger(0, cName, OBJPROP_FILL, false); 
             ObjectSetInteger(0, cName, OBJPROP_BACK, true); 
             ObjectSetInteger(0, cName, OBJPROP_STYLE, STYLE_DOT);
             ObjectSetInteger(0, cName, OBJPROP_WIDTH, 1);
             boxIdxCyt++;
          } else {
              ObjectDelete(0, cName);
          }
       }
        for(int k=totalCyt; k<1000; k++) ObjectDelete(0, "NEXUS_CYT_HIST_"+IntegerToString(k));
      for(int k=0; k<100; k++) ObjectDelete(0, "NEXUS_CYT_ZONE_"+IntegerToString(k));
   }

   // 1.7 ATUALIZAÇÃO HISTÓRICA SEC (DESATIVADO)
   ObjectsDeleteAll(0, "NEXUS_SEC_H_");
   ObjectsDeleteAll(0, "NEXUS_SEC_S_");
   ObjectDelete(0, "NEXUS_SEC_HORIZON");

   // 2. ATUALIZAÇÃO DOS TACTICAL DOTS (DESATIVADO TEMPORARIAMENTE)
   ObjectsDeleteAll(0, "NEXUS_DOT_");
   /*
   string hDots[]; StringSplit(historyDots, ',', hDots);
   int totalD = ArraySize(hDots);
   ...
   */

   // 3. ATUALIZAÇÃO DOS SINAIS DE VOLUME
   string hSig[]; StringSplit(historySignals, ',', hSig);
   int totalS = ArraySize(hSig);
   for(int j=0; j < totalS && j < iBars(_Symbol, _Period); j++) {
      int sVal = (int)StringToInteger(hSig[totalS - 1 - j]);
      string sName = "NEXUS_SIG_" + IntegerToString(j);
      string sTextName = "NEXUS_SIG_TXT_" + IntegerToString(j);
      string sBoxName = "NEXUS_SIG_BOX_" + IntegerToString(j);
      
      if(sVal == 0) { ObjectDelete(0, sName); ObjectDelete(0, sTextName); ObjectDelete(0, sBoxName); continue; }
      
      // Pill-Style Signal para Volume (TradingView Style)
      color pillBg = (sVal == 1) ? RGB(8, 153, 129) : RGB(242, 54, 69);
      double pHigh = iHigh(_Symbol, _Period, j);
      double pLow = iLow(_Symbol, _Period, j);
      bool isBuy = (sVal == 1);
      
      double atr_offset = (iHigh(_Symbol, _Period, iHighest(_Symbol, _Period, MODE_HIGH, 20, j)) - iLow(_Symbol, _Period, iLowest(_Symbol, _Period, MODE_LOW, 20, j))) * 0.05;
      if(atr_offset < 100 * _Point) atr_offset = 100 * _Point;
      ObjectSetString(0, sTextName, OBJPROP_TEXT, (isBuy ? "BUY" : "SELL"));
      ObjectSetString(0, sTextName, OBJPROP_FONT, "Segoe UI Bold");
      ObjectSetInteger(0, sTextName, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, sTextName, OBJPROP_COLOR, clrWhite);
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
         // LUXALGO STYLE HEATMAP: Extensão horizontal ampla e cores profundas
         int barCount = iBars(_Symbol, _Period);
         datetime tStart = iTime(_Symbol, _Period, MathMin(100, barCount-1)); // Cobre 100 velas para o passado
         datetime tEnd = TimeCurrent() + PeriodSeconds(_Period) * 20; // Projeta no futuro
         double dx = dx_val;
         double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         
         for(int b=0; b<tCloud; b++) {
            string cVal[]; StringSplit(cloudBins[b], '|', cVal);
            if(ArraySize(cVal) != 2) continue;
            double pLevel = StringToDouble(cVal[0]);
            double den = StringToDouble(cVal[1]);
            string bName = "NEXUS_QC_" + IntegerToString(b);
            string tagName = "NEXUS_QCTAG_" + IntegerToString(b);
            
            // Filtro de Ruído: Remove densidades irrelevantes para clareza
            if(den < maxDensity * 0.15) { ObjectDelete(0, bName); ObjectDelete(0, tagName); continue; }
            
            double ratio = den / maxDensity;
            // Curva de saturação mais agressiva: Fundo permanece "Ebony" e apenas os picos de liquidez brilham sutilmente
            double satRatio = MathPow(ratio, 2.5); 
            uchar rVal, gVal, bVal;
            
            if(pLevel > currentPrice) { 
                // RESISTANCE: Ebony Maroon -> Deep Crimson (Darker/Shadowy)
                rVal = (uchar)(28 + (100 * satRatio)); 
                gVal = (uchar)(10 + (25 * satRatio)); 
                bVal = (uchar)(12 + (30 * satRatio)); 
            } else { 
                // SUPPORT: Ebony Teal -> Midnight Cyan (Darker/Shadowy)
                rVal = (uchar)(5 + (15 * satRatio)); 
                gVal = (uchar)(28 + (100 * satRatio)); 
                bVal = (uchar)(25 + (90 * satRatio)); 
            }
            
            if(ObjectFind(0, bName) < 0) ObjectCreate(0, bName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
            ObjectSetInteger(0, bName, OBJPROP_TIME, 0, tStart);
            ObjectSetDouble(0, bName, OBJPROP_PRICE, 0, pLevel + (dx * 0.55)); // Ligeiro overlap para suavizar
            
            ObjectSetInteger(0, bName, OBJPROP_TIME, 1, tEnd);
            ObjectSetDouble(0, bName, OBJPROP_PRICE, 1, pLevel - (dx * 0.55));
            ObjectSetInteger(0, bName, OBJPROP_COLOR, RGB(rVal, gVal, bVal));
            ObjectSetInteger(0, bName, OBJPROP_FILL, true);
            ObjectSetInteger(0, bName, OBJPROP_BACK, true);
            ObjectSetInteger(0, bName, OBJPROP_ZORDER, 1); // Acima do grid, abaixo de tudo
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
         ObjectSetDouble(0, qLineName, OBJPROP_PRICE, 0, symPrice - (isBuy ? atr_offset : -atr_offset));
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

   // 6. ATUALIZAÇÃO DA DINÂMICA DE FLUIDOS (LBM ICONS TÁTICOS)
   string hLbm[]; StringSplit(parts[15], ',', hLbm);
   int tLbm = ArraySize(hLbm);
   for(int k=0; k < tLbm && k < iBars(_Symbol, _Period); k++) {
      int lVal = (int)StringToInteger(hLbm[tLbm - 1 - k]);
      string lName = "NEXUS_LBM_ICON_" + IntegerToString(k);
      
      // Limpeza forçada do sistema antigo de faixas para evitar resíduos
      ObjectDelete(0, "NEXUS_LBM_" + IntegerToString(k));
      
      if(lVal == 0) { if(ObjectFind(0, lName) >= 0) ObjectDelete(0, lName); continue; }
      
      // Cores Metálicas (Cyberpunk Palette)
      color lClr = (lVal == 1) ? RGB(0, 255, 255) : (lVal == 2 ? RGB(255, 64, 129) : clrGold); 
      int arrowCode = 159; // Mini-círculo (Wingdings)
      
      double pHigh = iHigh(_Symbol, _Period, k);
      double pLow = iLow(_Symbol, _Period, k);
      double atr_offset = (iHigh(_Symbol, _Period, iHighest(_Symbol, _Period, MODE_HIGH, 15, k)) - iLow(_Symbol, _Period, iLowest(_Symbol, _Period, MODE_LOW, 15, k))) * 0.08;
      if(atr_offset < 100 * _Point) atr_offset = 100 * _Point;

      if(ObjectFind(0, lName) < 0) ObjectCreate(0, lName, OBJ_ARROW, 0, 0, 0);
      ObjectSetInteger(0, lName, OBJPROP_TIME, iTime(_Symbol, _Period, k));
      ObjectSetDouble(0, lName, OBJPROP_PRICE, (lVal == 1) ? pLow - atr_offset : (lVal == 2 ? pHigh + atr_offset : pHigh + atr_offset * 1.2));
      ObjectSetInteger(0, lName, OBJPROP_ARROWCODE, arrowCode);
      ObjectSetInteger(0, lName, OBJPROP_COLOR, lClr);
      ObjectSetInteger(0, lName, OBJPROP_WIDTH, 1); // Círculo minimalista
      ObjectSetInteger(0, lName, OBJPROP_ANCHOR, (lVal == 1) ? ANCHOR_TOP : ANCHOR_BOTTOM);
      ObjectSetInteger(0, lName, OBJPROP_BACK, false);
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
   // 9. QUANTUM DENSITY CLOUDS (DESATIVADO PARA CLAREZA VISUAL)
   ObjectsDeleteAll(0, "NEXUS_CLOUD_");

   ChartRedraw(0);
}

void DrawWyckoffHUD(string score, string phase, string div, string strength)
{
    int chartW = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
    int panelW = 240; int panelH = 135; int corner = CORNER_LEFT_UPPER; 
    int baseX = chartW - panelW - 60; 
    int baseY = 60;
    
    string bgName = "NEXUS_WYCK_BG"; if(ObjectFind(0, bgName) < 0) ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, bgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, baseX); ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, baseY);
    ObjectSetInteger(0, bgName, OBJPROP_XSIZE, panelW); ObjectSetInteger(0, bgName, OBJPROP_YSIZE, panelH);
    ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, RGB(12, 15, 20)); // Ebony Stealth
    ObjectSetInteger(0, bgName, OBJPROP_COLOR, RGB(35, 40, 50)); // Dark Border
    ObjectSetInteger(0, bgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, bgName, OBJPROP_ZORDER, 100);

    DrawHUDText("NEXUS_WYCK_TITLE", "WYCKOFF PRECISION", baseX + 15, baseY + 10, RGB(0, 188, 212), 9, false, corner);
    
    int rowY = baseY + 40; int rowH = 20;
    DrawHUDRowWyck("NEXUS_WYCK_SCORE", "NEXUS Score", score, RGB(66, 165, 245), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRowWyck("NEXUS_WYCK_PHASE", "Market Phase", phase, RGB(255, 213, 79), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRowWyck("NEXUS_WYCK_DIV", "Divergence", div, (div == "None" ? clrGray : RGB(239, 83, 80)), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRowWyck("NEXUS_WYCK_STR", "Pressure", strength, clrWhite, baseX, rowY, panelW, corner);
    
}

void DrawHUDRowWyck(string id, string label, string val, color valClr, int baseX, int y, int panelW, int corner)
{
    // Padrão Universal: Label na Esquerda do Painel, Value na Direita
    DrawHUDText(id + "_L", label, baseX + 15, y, RGB(140, 140, 145), 8, false, corner); 
    DrawHUDText(id + "_V", val, baseX + panelW - 15, y, valClr, 8, true, corner);
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
    datetime start_time = iTime(_Symbol, _Period, MathMin(500, iBars(_Symbol, _Period)-1));
    if(start_time == 0) return;
    HistorySelect(start_time, TimeCurrent());
    int total = HistoryDealsTotal();
    
    for(int i=0; i<total; i++) {
        ulong ticket = HistoryDealGetTicket(i);
        string dSymbol = HistoryDealGetString(ticket, DEAL_SYMBOL);
        
        // Filtro de Símbolo Resiliente (Ignora Case)
        if(StringCompare(dSymbol, _Symbol, false) != 0) continue;
        
        long entry = HistoryDealGetInteger(ticket, DEAL_ENTRY);
        datetime dTime = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
        
        int bShift = iBarShift(_Symbol, _Period, dTime);
        double pHigh = iHigh(_Symbol, _Period, bShift);
        double pLow = iLow(_Symbol, _Period, bShift);
        
        // 1. TAG DE ENTRADA (NÍVEL 1: 15px)
        if(entry == DEAL_ENTRY_IN) {
            string inName = "NEXUS_TTAG_IN_" + IntegerToString(ticket);
            long type = HistoryDealGetInteger(ticket, DEAL_TYPE);
            color bg = (type == DEAL_TYPE_BUY) ? RGB(38, 166, 154) : RGB(239, 83, 80);
            string txt = (type == DEAL_TYPE_BUY) ? "BUY" : "SELL";
            bool isAbove = (type == DEAL_TYPE_SELL);
            
            CreateTradingViewTag(inName, dTime, isAbove ? pHigh : pLow, txt, bg, isAbove, 40, 15);
        }
        
        // 2. TAG DE SAÍDA (NÍVEL 2: 35px) + CONECTOR
        if(entry == DEAL_ENTRY_OUT || entry == DEAL_ENTRY_INOUT) {
            ulong pos_id = HistoryDealGetInteger(ticket, DEAL_POSITION_ID);
            double profit = HistoryDealGetDouble(ticket, DEAL_PROFIT);
            string outName = "NEXUS_TTAG_OUT_" + IntegerToString(ticket);
            color bg = (profit >= 0) ? RGB(38, 166, 154) : RGB(239, 83, 80);
            
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
                    string lineName = "NEXUS_TLINE_" + IntegerToString(ticket);
                    if(ObjectFind(0, lineName) < 0) {
                        ObjectCreate(0, lineName, OBJ_TREND, 0, in_time, in_price, dTime, HistoryDealGetDouble(ticket, DEAL_PRICE));
                        ObjectSetInteger(0, lineName, OBJPROP_COLOR, RGB(60, 65, 75));
                        ObjectSetInteger(0, lineName, OBJPROP_STYLE, STYLE_DOT);
                        ObjectSetInteger(0, lineName, OBJPROP_RAY_RIGHT, false);
                        ObjectSetInteger(0, lineName, OBJPROP_BACK, true);
                    }
                }
            }
            
            string txt = "REALIZED: " + (profit >= 0 ? "+" : "") + DoubleToString(profit, 1);
            CreateTradingViewTag(outName, dTime, (profit >= 0) ? pHigh : pLow, txt, bg, (profit >= 0), 85, 35);
        }
    }
}

// Motor de Renderização com Suporte a Níveis de Haste (v4.6)
void CreateTradingViewTag(string name, datetime time, double price, string text, color bg, bool isAbove, int tagW, int stemLen)
{
    int x, y;
    if(!ChartTimePriceToXY(0, 0, time, price, x, y)) return;
    
    string btnName = name + "_BTN";
    string stemName = name + "_STEM";
    int tagH = 18;
    
    if(ObjectFind(0, stemName) < 0) ObjectCreate(0, stemName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, stemName, OBJPROP_XDISTANCE, x - 1);
    ObjectSetInteger(0, stemName, OBJPROP_YDISTANCE, isAbove ? y - stemLen : y);
    ObjectSetInteger(0, stemName, OBJPROP_XSIZE, 1);
    ObjectSetInteger(0, stemName, OBJPROP_YSIZE, stemLen);
    ObjectSetInteger(0, stemName, OBJPROP_BGCOLOR, bg);
    ObjectSetInteger(0, stemName, OBJPROP_COLOR, bg);
    ObjectSetInteger(0, stemName, OBJPROP_BORDER_TYPE, BORDER_FLAT);

    if(ObjectFind(0, btnName) < 0) {
        ObjectCreate(0, btnName, OBJ_BUTTON, 0, 0, 0);
        ObjectSetInteger(0, btnName, OBJPROP_SELECTABLE, false);
        ObjectSetInteger(0, btnName, OBJPROP_FONTSIZE, 7);
        ObjectSetString(0, btnName, OBJPROP_FONT, "Segoe UI Bold");
        ObjectSetInteger(0, btnName, OBJPROP_CORNER, CORNER_LEFT_UPPER);
    }
    
    ObjectSetInteger(0, btnName, OBJPROP_XDISTANCE, x - (tagW/2));
    ObjectSetInteger(0, btnName, OBJPROP_YDISTANCE, isAbove ? y - stemLen - tagH : y + stemLen);
    ObjectSetInteger(0, btnName, OBJPROP_XSIZE, tagW);
    ObjectSetInteger(0, btnName, OBJPROP_YSIZE, tagH);
    ObjectSetString(0, btnName, OBJPROP_TEXT, text);
    ObjectSetInteger(0, btnName, OBJPROP_BGCOLOR, bg);
    ObjectSetInteger(0, btnName, OBJPROP_COLOR, clrWhite);
    ObjectSetInteger(0, btnName, OBJPROP_STATE, false);
}

// Helper para cálculo de volatilidade dinâmica (ATR)
double iATR(string symbol, ENUM_TIMEFRAMES tf, int period, int shift) {
    int handle = iATR(symbol, tf, period);
    if(handle == INVALID_HANDLE) return 0;
    double val[1];
    if(CopyBuffer(handle, 0, shift, 1, val) > 0) return val[0];
    return 0;
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
string GetQRWShort(string qrw) { 
    if(qrw == "NEUTRAL" || qrw == "") return "No Interf."; 
    if(qrw == "QUANTUM_ACCUMULATION_BULL") return "Accumulation"; 
    if(qrw == "QUANTUM_DISTRIBUTION_BEAR") return "Distribution"; 
    if(qrw == "QUANTUM_EXHAUSTION_SHORT") return "!!! SINGULARITY TOP !!!";
    if(qrw == "QUANTUM_EXHAUSTION_LONG") return "!!! SINGULARITY BOTTOM !!!";
    return qrw; 
}
color GetQRWColor(string qrw) { 
    if(qrw == "QUANTUM_ACCUMULATION_BULL") return RGB(0, 255, 180); 
    if(qrw == "QUANTUM_DISTRIBUTION_BEAR") return RGB(255, 167, 38); 
    if(qrw == "QUANTUM_EXHAUSTION_SHORT") return RGB(255, 0, 85); // Neon Pink
    if(qrw == "QUANTUM_EXHAUSTION_LONG") return RGB(0, 255, 255);  // Neon Cyan
    return RGB(120, 123, 134); 
}
string GetRMTShort(string rmt) {
    if(StringFind(rmt, "PURE_SIGNAL") >= 0) {
        string res = rmt;
        StringReplace(res, "PURE_SIGNAL_x", "S-MAT x");
        return res;
    }
    if(StringFind(rmt, "NOISE_x") >= 0) {
        string res = rmt;
        StringReplace(res, "NOISE_x", "NOISE x");
        return res;
    }
    return "NOISE"; 
}
color GetRMTColor(string rmt) { 
    if(StringFind(rmt, "PURE_SIGNAL") >= 0) {
        double val = StringToDouble(StringSubstr(rmt, StringFind(rmt, "_x") + 2));
        if(val >= 3.0) return RGB(255, 215, 0); // Gold
        return RGB(255, 110, 0); // Orange Neon
    }
    return RGB(80, 85, 100); 
}
void DrawEnergyBar(string id, double val, double maxVal, int x, int y, int w, int h, color clr, int corner)
{
    string bgName = id + "_BG"; string fillName = id + "_FILL";
    if(ObjectFind(0, bgName) < 0) ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, bgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, x); ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, bgName, OBJPROP_XSIZE, w); ObjectSetInteger(0, bgName, OBJPROP_YSIZE, h);
    ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, RGB(12, 15, 20)); // Ebony Stealth
    ObjectSetInteger(0, bgName, OBJPROP_COLOR, RGB(35, 40, 50)); // Dark Border
    ObjectSetInteger(0, bgName, OBJPROP_ZORDER, 100);

    int fillW = (int)((val / maxVal) * w); if(fillW > w) fillW = w; if(fillW < 2) fillW = 2;
    if(ObjectFind(0, fillName) < 0) ObjectCreate(0, fillName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, fillName, OBJPROP_CORNER, corner); ObjectSetInteger(0, fillName, OBJPROP_XDISTANCE, x); ObjectSetInteger(0, fillName, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, fillName, OBJPROP_XSIZE, fillW); ObjectSetInteger(0, fillName, OBJPROP_YSIZE, h);
    ObjectSetInteger(0, fillName, OBJPROP_BGCOLOR, clr); ObjectSetInteger(0, fillName, OBJPROP_COLOR, clr);
    ObjectSetInteger(0, fillName, OBJPROP_ZORDER, 110);
}
void DrawHUDText(string name, string text, int x, int y, color clr, int fontSize, bool isRightAligned=false, int corner=CORNER_LEFT_UPPER)
{
    if(ObjectFind(0, name) < 0) ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0);
    ObjectSetInteger(0, name, OBJPROP_CORNER, corner);
    ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
    ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
    ObjectSetString(0, name, OBJPROP_TEXT, text);
    ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
    ObjectSetInteger(0, name, OBJPROP_FONTSIZE, fontSize);
    ObjectSetString(0, name, OBJPROP_FONT, "Segoe UI");
    
    ENUM_ANCHOR_POINT anchor = isRightAligned ? ANCHOR_RIGHT_UPPER : ANCHOR_LEFT_UPPER;
    ObjectSetInteger(0, name, OBJPROP_ANCHOR, anchor);
    
    ObjectSetInteger(0, name, OBJPROP_ZORDER, 1100);
    ObjectSetInteger(0, name, OBJPROP_BACK, false);
    ObjectSetInteger(0, name, OBJPROP_HIDDEN, false);
}
color RGB(uchar r, uchar g, uchar b) { return (color)((b << 16) | (g << 8) | r); }
void DrawHUDRow(string id, string label, string val, color valClr, int baseX, int y, int panelW, int corner=CORNER_LEFT_UPPER)
{
    DrawHUDText(id + "_L", label, baseX + 15, y, RGB(140, 140, 145), 9, false, corner); 
    DrawHUDText(id + "_V", val, baseX + panelW - 15, y, valClr, 9, true, corner);
}
void DrawModernDashboard(string status, double instAvg, double health, string rht, string lbm, string zp, string qrw, string sec, string rmt, string ricci, string entropy, bool collapsed)
{
    int panelW = 280; int panelH = 360; int corner = CORNER_LEFT_UPPER; int baseX = 20; int baseY = 30;
    string bgName = "NEXUS_HUD_BASE"; if(ObjectFind(0, bgName) < 0) ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, bgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, baseX); ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, baseY);
    ObjectSetInteger(0, bgName, OBJPROP_XSIZE, panelW); ObjectSetInteger(0, bgName, OBJPROP_YSIZE, panelH); 
    color mainBg = RGB(12, 15, 20);
    ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, mainBg);
    ObjectSetInteger(0, bgName, OBJPROP_COLOR, RGB(35, 40, 50)); 
    ObjectSetInteger(0, bgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, bgName, OBJPROP_ZORDER, 1000); 
    ObjectSetInteger(0, bgName, OBJPROP_BACK, false);

    string hBgName = "NEXUS_HUD_HEADER_BG"; if(ObjectFind(0, hBgName) < 0) ObjectCreate(0, hBgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, hBgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, hBgName, OBJPROP_XDISTANCE, baseX); ObjectSetInteger(0, hBgName, OBJPROP_YDISTANCE, baseY);
    ObjectSetInteger(0, hBgName, OBJPROP_XSIZE, panelW); ObjectSetInteger(0, hBgName, OBJPROP_YSIZE, 35); 
    
    double rCurv = StringToDouble(ricci);
    bool isCollapsed = (rCurv >= 2.5);
    
    if(isCollapsed) {
        ObjectSetInteger(0, hBgName, OBJPROP_BGCOLOR, RGB(242, 54, 69)); // TV Red
        DrawHUDText("NEXUS_HUD_TITLE", "!!! COLLAPSE DETECTED !!!", baseX + 15, baseY + 10, clrWhite, 10, false, corner);
    } else {
        ObjectSetInteger(0, hBgName, OBJPROP_BGCOLOR, RGB(42, 46, 62)); // Ebony Header
        DrawHUDText("NEXUS_HUD_TITLE", "AETHELGARD :: QUANTUM CORE", baseX + 15, baseY + 10, RGB(220, 225, 235), 10, false, corner);
    }
    ObjectSetInteger(0, hBgName, OBJPROP_COLOR, clrNONE); 
    ObjectSetInteger(0, hBgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, hBgName, OBJPROP_ZORDER, 1010);

    int rowY = baseY + 45; int rowH = 20;
    for(int k=0; k<15; k++) {
        string rBgName = "NEXUS_HUD_ROW_BG_" + IntegerToString(k); if(ObjectFind(0, rBgName) < 0) ObjectCreate(0, rBgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
        ObjectSetInteger(0, rBgName, OBJPROP_CORNER, corner); 
        ObjectSetInteger(0, rBgName, OBJPROP_XDISTANCE, baseX); 
        ObjectSetInteger(0, rBgName, OBJPROP_YDISTANCE, baseY + 36 + (k * rowH));
        ObjectSetInteger(0, rBgName, OBJPROP_XSIZE, panelW);
        ObjectSetInteger(0, rBgName, OBJPROP_YSIZE, rowH);
        
        color rCol = (k % 2 == 0) ? RGB(15, 18, 25) : RGB(10, 12, 18);
        ObjectSetInteger(0, rBgName, OBJPROP_BGCOLOR, rCol); 
        ObjectSetInteger(0, rBgName, OBJPROP_COLOR, clrNONE); 
        ObjectSetInteger(0, rBgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
        ObjectSetInteger(0, rBgName, OBJPROP_ZORDER, 1005);
        ObjectSetInteger(0, rBgName, OBJPROP_BACK, false);
    }

    DrawHUDRow("NEXUS_HUD_L_1", "Regime", GetStatusShort(status), GetStatusColor(status), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_2", "Confidence", DoubleToString(health * 100, 1) + "%", GetHealthColor(health), baseX, rowY, panelW, corner); rowY += rowH;
    
    color rhtClr = RGB(140, 140, 145);
    if(StringFind(rht, "IGNITION") >= 0) rhtClr = RGB(255, 100, 0); // Orange
    else if(StringFind(rht, "HEATING") >= 0) rhtClr = RGB(255, 200, 0); // Yellow
    else if(StringFind(rht, "LAMINAR") >= 0) rhtClr = RGB(0, 255, 180); // Cyan
    
    DrawHUDRow("NEXUS_HUD_L_3", "RHT Heat", rht, rhtClr, baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_RHTF", "RHT Flash", (StringToDouble(rhtFlash) != 0 ? (rhtFlash=="1"?"BULL":"BEAR") : "LAMINAR"), (StringToDouble(rhtFlash)!=0?(rhtFlash=="1"?RGB(0,255,255):RGB(255,50,50)):RGB(140,140,145)), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_4", "LBM Fluid", GetLBMShort(lbm), GetLBMColor(lbm), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_5", "AdS/CFT Bulk", GetZPShort(zp), GetZPColor(zp), baseX, rowY, panelW, corner); rowY += rowH;
    DrawHUDRow("NEXUS_HUD_L_6", "QRW Flux", GetQRWShort(qrw), GetQRWColor(qrw), baseX, rowY, panelW, corner); rowY += rowH;
    
    double rmtVal = 0.0;
    if(StringFind(rmt, "_x") >= 0) rmtVal = StringToDouble(StringSubstr(rmt, StringFind(rmt, "_x") + 2));
    color rmtClr = GetRMTColor(rmt);
    DrawHUDRow("NEXUS_HUD_L_7", "S-Matrix Amp", GetRMTShort(rmt), rmtClr, baseX, rowY, panelW, corner);
    rowY += 15;
    DrawEnergyBar("NEXUS_RMT_BAR", rmtVal, 8.0, baseX + 15, rowY, panelW - 30, 5, rmtClr, corner);
    rowY += 12;

    color cytClr = isCollapsed ? RGB(255, 30, 30) : (rCurv >= 1.5 ? RGB(200, 0, 255) : RGB(0, 255, 255));
    DrawHUDRow("NEXUS_HUD_L_CYT", "Ricci Flow / AdS", ricci + " sigma", cytClr, baseX, rowY, panelW, corner);
    rowY += 15;
    DrawEnergyBar("NEXUS_CYT_BAR", rCurv, 5.0, baseX + 15, rowY, panelW - 30, 5, cytClr, corner);
    rowY += 12;
    
    DrawHUDRow("NEXUS_HUD_L_8", "Inst. Avg", DoubleToString(instAvg, 2), RGB(200, 200, 200), baseX, rowY, panelW, corner);
    
    if(isCollapsed) {
        string auraName = "NEXUS_CYT_AURA";
        if(ObjectFind(0, auraName) < 0) ObjectCreate(0, auraName, OBJ_VLINE, 0, iTime(_Symbol, _Period, 0), 0);
        ObjectSetInteger(0, auraName, OBJPROP_TIME, iTime(_Symbol, _Period, 0));
        ObjectSetInteger(0, auraName, OBJPROP_COLOR, RGB(255, 0, 0)); 
        ObjectSetInteger(0, auraName, OBJPROP_WIDTH, 5);
        ObjectSetInteger(0, auraName, OBJPROP_BACK, true);
    } else {
        ObjectDelete(0, "NEXUS_CYT_AURA");
    }
    ObjectDelete(0, "NEXUS_CYT_WARNING");

    ObjectDelete(0, "NEXUS_SEC_ICON");
    ObjectDelete(0, "NEXUS_SEC_ALERT");
    ObjectsDeleteAll(0, "NEXUS_BLACK_HOLE_");
    ObjectDelete(0, "NEXUS_BH_LABEL");
}
