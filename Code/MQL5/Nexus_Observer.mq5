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
int OnInit() { EventSetTimer(1); return(INIT_SUCCEEDED); }
void OnDeinit(const int reason) { EventKillTimer(); ObjectsDeleteAll(0, "NEXUS_"); }
void OnTick() { UpdateDashboard(); }
void OnTimer() { UpdateDashboard(); }

void UpdateDashboard()
{
   string url = "http://127.0.0.1:5000/nexus";
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
   
   DrawLabel("NEXUS_HEADER", "AETHELGARD [TRUE SYNC] V113", 10, 20, clrCyan, 12);
   
   color sClr = (health < 0.3) ? clrRed : (health < 0.6 ? clrGold : clrSpringGreen);
   DrawLabel("NEXUS_STATUS", "STATUS: " + statusTxt, 10, 40, sClr, 10);
   DrawLabel("NEXUS_INST_AVG", "INST_AVG_PRICE: " + DoubleToString(instAvgPrice, 2), 10, 60, clrGray, 9);

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
         color zClr = (r == 1) ? clrLime : clrRed;
         
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

      if(dotVal == 1) dClr = clrSpringGreen;
      else if(dotVal == 11) dClr = clrMediumSeaGreen;
      else if(dotVal == 12) dClr = clrForestGreen;
      else if(dotVal == 13) dClr = clrDarkGreen;
      else if(dotVal == 2) dClr = clrRed;
      else if(dotVal == 21) dClr = clrCrimson;
      else if(dotVal == 22) dClr = clrFireBrick;
      else if(dotVal == 23) dClr = clrMaroon;

      if(dClr == clrBlack) { ObjectDelete(0, dName); continue; }

      if(ObjectFind(0, dName) < 0) ObjectCreate(0, dName, OBJ_ARROW, 0, 0, 0);
      
      double offset = 100 * _Point;
      double dPrice = isAbove ? iHigh(_Symbol, _Period, d) + offset : iLow(_Symbol, _Period, d) - offset;
      
      ObjectSetInteger(0, dName, OBJPROP_TIME, iTime(_Symbol, _Period, d));
      ObjectSetDouble(0, dName, OBJPROP_PRICE, dPrice);
      ObjectSetInteger(0, dName, OBJPROP_ARROWCODE, 159);
      ObjectSetInteger(0, dName, OBJPROP_COLOR, dClr);
      ObjectSetInteger(0, dName, OBJPROP_WIDTH, (dotVal < 10 ? 2 : 1));
      ObjectSetInteger(0, dName, OBJPROP_ANCHOR, isAbove ? ANCHOR_BOTTOM : ANCHOR_TOP);
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
      
      if(ObjectFind(0, sName) < 0) ObjectCreate(0, sName, OBJ_TEXT, 0, 0, 0);
      double sPrice = (sVal == 1) ? iLow(_Symbol, _Period, j) - 80 * _Point : iHigh(_Symbol, _Period, j) + 80 * _Point;
      
      ObjectSetInteger(0, sName, OBJPROP_TIME, iTime(_Symbol, _Period, j));
      ObjectSetDouble(0, sName, OBJPROP_PRICE, sPrice);
      ObjectSetString(0, sName, OBJPROP_TEXT, (sVal == 1 ? "[BULL_VOLUME]" : "[BEAR_VOLUME]"));
      ObjectSetInteger(0, sName, OBJPROP_COLOR, (sVal == 1 ? clrDodgerBlue : clrOrangeRed));
      ObjectSetInteger(0, sName, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, sName, OBJPROP_ANCHOR, (sVal == 1 ? ANCHOR_TOP : ANCHOR_BOTTOM));
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
      
      datetime tStart = iTime(_Symbol, _Period, 0);
      datetime tEnd = tStart + PeriodSeconds() * 10; // Avança visualmente 10 candles pra direita
      
      for(int b=0; b<tCloud; b++) {
         string cVal[]; StringSplit(cloudBins[b], '|', cVal);
         if(ArraySize(cVal) != 2) continue;
         
         double pLevel = StringToDouble(cVal[0]);
         double den = StringToDouble(cVal[1]);
         
         string bName = "NEXUS_QC_" + IntegerToString(b);
         if(den < maxDensity * 0.05) { // Ignora bins com densidade muito baixa para salvar performance
             ObjectDelete(0, bName);
             continue;
         }
         
         if(ObjectFind(0, bName) < 0) ObjectCreate(0, bName, OBJ_TREND, 0, 0, 0, 0, 0);
         
         // A largura da linha representa a densidade da nuvem naquele preço
         double ratio = den / maxDensity;
         datetime tCloudEnd = tStart + (int)(PeriodSeconds() * 10 * ratio);
         
         // Gradiente de cor baseado na densidade (Laranja Escuro para Amarelo Brilhante)
         color qColor = clrOrangeRed;
         if(ratio > 0.8) qColor = clrYellow;
         else if(ratio > 0.5) qColor = clrOrange;
         
         ObjectSetInteger(0, bName, OBJPROP_TIME, 0, tStart);
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 0, pLevel);
         ObjectSetInteger(0, bName, OBJPROP_TIME, 1, tCloudEnd);
         ObjectSetDouble(0, bName, OBJPROP_PRICE, 1, pLevel);
         
         ObjectSetInteger(0, bName, OBJPROP_COLOR, qColor);
         ObjectSetInteger(0, bName, OBJPROP_WIDTH, 4); // Espessura da linha horizontal
         ObjectSetInteger(0, bName, OBJPROP_RAY_RIGHT, false);
         ObjectSetInteger(0, bName, OBJPROP_BACK, true); // Desenha atrás dos candles
      }
      
      // Limpa bins extras que podem ter sobrado se o grid diminuir
      for(int k=tCloud; k<200; k++) ObjectDelete(0, "NEXUS_QC_"+IntegerToString(k));
   }
   
   // 5. ATUALIZAÇÃO DO ALARME LBM FLUID RUPTURE
   if(ArraySize(parts) > 11 && parts[11] != "") {
      string lbm_signal = parts[11];
      string lbm_label = "NEXUS_LBM_WARNING";
      
      if(lbm_signal == "FLUID_RUPTURE_BULL" || lbm_signal == "FLUID_RUPTURE_BEAR") {
          color wClr = (lbm_signal == "FLUID_RUPTURE_BULL") ? clrDeepSkyBlue : clrMagenta;
          string wTxt = (lbm_signal == "FLUID_RUPTURE_BULL") ? "⚠️ LBM SQUEEZE: ALTA COMPRESSÃO BULLISH!" : "⚠️ LBM SQUEEZE: ALTA COMPRESSÃO BEARISH!";
          DrawLabel(lbm_label, wTxt, 10, 90, wClr, 14); // Fonte maior, cor chamativa
      } else {
          // LAMINAR_FLOW -> Apaga o aviso ou deixa neutro
          if(ObjectFind(0, lbm_label) >= 0) ObjectDelete(0, lbm_label);
      }
   }
   
   // 6. ATUALIZAÇÃO DO ALARME MHD Z-PINCH (PLASMA)
   if(ArraySize(parts) > 12 && parts[12] != "") {
      string z_signal = parts[12];
      string z_label = "NEXUS_ZPINCH_WARNING";
      
      if(z_signal != "NEUTRAL") {
          color zClr = clrGold;
          string zTxt = "⚡ Z-PINCH ATINGIDO: " + z_signal + " (REVERSÃO ATÔMICA IMINENTE!)";
          DrawLabel(z_label, zTxt, 10, 110, zClr, 16); 
      } else {
          if(ObjectFind(0, z_label) >= 0) ObjectDelete(0, z_label);
      }
   }

   // 7. ATUALIZAÇÃO DO FILTRO RMT SPECTRAL (RUÍDO VS INSTITUCIONAL)
   if(ArraySize(parts) > 13 && parts[13] != "") {
      string rmt_signal = parts[13];
      string rmt_label = "NEXUS_RMT_WARNING";
      
      if(rmt_signal != "NOISE") {
          color rmtClr = clrLime;
          string rmtTxt = "🔬 RMT: " + rmt_signal + " (SINAL INSTITUCIONAL VERIFICADO)";
          DrawLabel(rmt_label, rmtTxt, 10, 130, rmtClr, 12); 
      } else {
          if(ObjectFind(0, rmt_label) >= 0) ObjectDelete(0, rmt_label);
      }
   }

   // 8. ATUALIZAÇÃO DO DECODER QRW (QUANTUM RANDOM WALK)
   if(ArraySize(parts) > 14 && parts[14] != "") {
      string qrw_signal = parts[14];
      string qrw_label = "NEXUS_QRW_WARNING";
      
      if(qrw_signal != "NEUTRAL") {
          color qrwClr = (qrw_signal == "HIDDEN_ACCUMULATION_BULL") ? clrCyan : clrOrange;
          string qrwTxt = "🎲 QRW DECODER: " + qrw_signal + " (INTERFERÊNCIA DETECTADA)";
          DrawLabel(qrw_label, qrwTxt, 10, 150, qrwClr, 12); 
      } else {
          if(ObjectFind(0, qrw_label) >= 0) ObjectDelete(0, qrw_label);
      }
   }

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
         ObjectSetInteger(0, name, OBJPROP_COLOR, (v == 1) ? clrDeepSkyBlue : clrMagenta);
         ObjectSetInteger(0, name, OBJPROP_ANCHOR, (v == 1) ? ANCHOR_TOP : ANCHOR_BOTTOM);
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
         ObjectSetInteger(0, name, OBJPROP_COLOR, clrGold);
         ObjectSetInteger(0, name, OBJPROP_ANCHOR, (v == 1) ? ANCHOR_TOP : ANCHOR_BOTTOM);
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
         ObjectSetInteger(0, name, OBJPROP_COLOR, (v == 1) ? clrCyan : clrOrange);
         ObjectSetInteger(0, name, OBJPROP_ANCHOR, (v == 1) ? ANCHOR_TOP : ANCHOR_BOTTOM);
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
