//+------------------------------------------------------------------+
//|                                              Nexus_Observer.mq5 |
//|                                  Copyright 2026, NEXUS AGI CEO |
//+------------------------------------------------------------------+
#property copyright "NEXUS AGI CEO"
#property version   "114.00"
#property strict

// Memória de Estado
string last_payload = "";

// --- PROTÓTIPOS DE INTERFACE ---
void ParseAndDraw(string data);
void DrawModernDashboard(string status, double instAvg, double health, string rhtStatus, string lbm, string z, string qrw, string sec, string rmt, string ricci, string h_ent, bool collapsed, string rhtF, double qddFid, double qteProb, string qteAdvice, int qhoN, double qhoStability, string qhoStatus, double mhdStrength, string setupTel);
void DrawSetupSignal(string setupTel);
void DrawLBMHistory(string hist);
void DrawQGCHistory(string data);
void DrawQHOShells(string shells);
void DrawHUDText(string name, string text, int x, int y, color clr, int fs, bool alignRight=false, int corner=CORNER_LEFT_UPPER);
void DrawHUDRow(string id, string label, string val, color clr, int bx, int y, int pw, int corner);
void CreateTradingViewTag(string name, datetime t, double p, string txt, color bg, bool above, int tw, int sl);
void DrawModernTradeHistory();
string GetStatusShort(string status);
color GetStatusColor(string status);
color GetHealthColor(double h);
string GetLBMShort(string lbm);
color GetLBMColor(string lbm);
string GetZPShort(string zp);
color GetZPColor(string zp);
string GetQRWShort(string qrw);
color GetQRWColor(string qrw);
string GetRMTShort(string rmt);
color GetRMTColor(string rmt);

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
   string url = "http://127.0.0.1:5000/nexus?tf=" + IntegerToString(_Period) + "&symbol=" + _Symbol;
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
   // PROTOCOLO DE PURIFICAÇÃO AGRESSIVA (Incinerar resíduos históricos)
   ObjectsDeleteAll(0, "NEXUS_CYT_HIST_");
   ObjectsDeleteAll(0, "NEXUS_HEAT_");
   ObjectsDeleteAll(0, "NEXUS_DOT_");
   // [ANTI-FLICKER] QCD objects updated in-place, not purged
   
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
   string qrw_signal = (ArraySize(parts) > 14) ? parts[14] : "OFFLINE";
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
   double qddFidelity = (ArraySize(parts) > 31) ? StringToDouble(parts[31]) : 0.0;
   double qteProb = (ArraySize(parts) > 32) ? StringToDouble(parts[32]) : 0.0;
   string qteAdvice = (ArraySize(parts) > 33) ? parts[33] : "STABLE_ORBIT";
   int qhoN = (ArraySize(parts) > 34) ? (int)StringToInteger(parts[34]) : 0;
   double qhoStability = (ArraySize(parts) > 35) ? StringToDouble(parts[35]) : 1.0;
   string qhoStatus = (ArraySize(parts) > 36) ? parts[36] : "GROUND_STATE";
   string qhoShells = (ArraySize(parts) > 37) ? parts[37] : "";

   // --- 1. ESTABILIZAÇÃO VISUAL (ANTI-FLICKER) ---
   // Removida a purga global para evitar o efeito estroboscópico.
   // Objetos agora são atualizados in-place.

   string mhd_s = (ArraySize(parts) > 38) ? parts[38] : "0.00";
   double mhdStrength = StringToDouble(mhd_s);
    
     // --- SETUP ENGINE PARSING (v1.0) ---
     string setupTel = (ArraySize(parts) > 39) ? parts[39] : "NO_SETUP";
     string setupHistory = (ArraySize(parts) > 40) ? parts[40] : "";
     
     // Extrai SL e TP Dinâmicos (ANZ) da Telemetria de Setup
     // Extrai SL e TP Dinâmicos (ANZ) da Telemetria de Setup
     string sParts[]; StringSplit(setupTel, '|', sParts);
     double anzSl = 0.0; double anzTp = 0.0;
     int nParts = ArraySize(sParts);
     if(nParts >= 3) {
         anzSl = StringToDouble(sParts[nParts-2]);
         anzTp = StringToDouble(sParts[nParts-1]);
     }
     
     // Reconstrói a string do setup para as outras funções ignorarem os preços no final
     string cleanSetup = sParts[0];
     for(int x=1; x < nParts-2; x++) cleanSetup += "|" + sParts[x];

   // DrawModernDashboard(...) call removed

     // --- ADAPTIVE NEURAL ZONES (ANZ) VISUALS ---
     if(anzSl > 0.1) {
         if(ObjectFind(0, "NEXUS_ANZ_SL") < 0) ObjectCreate(0, "NEXUS_ANZ_SL", OBJ_HLINE, 0, 0, anzSl);
         ObjectSetDouble(0, "NEXUS_ANZ_SL", OBJPROP_PRICE, anzSl);
         ObjectSetInteger(0, "NEXUS_ANZ_SL", OBJPROP_COLOR, RGB(220, 20, 60)); // Crimson Red
         ObjectSetInteger(0, "NEXUS_ANZ_SL", OBJPROP_STYLE, STYLE_DASHDOT);
         ObjectSetInteger(0, "NEXUS_ANZ_SL", OBJPROP_WIDTH, 1);
     } else ObjectDelete(0, "NEXUS_ANZ_SL");

     if(anzTp > 0.1) {
         if(ObjectFind(0, "NEXUS_ANZ_TP") < 0) ObjectCreate(0, "NEXUS_ANZ_TP", OBJ_HLINE, 0, 0, anzTp);
         ObjectSetDouble(0, "NEXUS_ANZ_TP", OBJPROP_PRICE, anzTp);
         ObjectSetInteger(0, "NEXUS_ANZ_TP", OBJPROP_COLOR, RGB(0, 255, 255)); // Cyan
         ObjectSetInteger(0, "NEXUS_ANZ_TP", OBJPROP_STYLE, STYLE_DASHDOT);
         ObjectSetInteger(0, "NEXUS_ANZ_TP", OBJPROP_WIDTH, 1);
     } else ObjectDelete(0, "NEXUS_ANZ_TP");

     // --- SETUP HISTORY VISUALS ---
     ObjectsDeleteAll(0, "NEXUS_SH_");

   // --- 1.8 RHT THERMODYNAMIC VISUALS (IGNIÇÕES HISTÓRICAS) ---
   ObjectsDeleteAll(0, "NEXUS_SPARK_HIST_");

    // [PURGA INTERNA REMOVIDA PARA EVITAR FLICKER]

   // 1. ATUALIZAÇÃO DAS CAIXAS (Protocolo v23.0 Anticipatory Lead)
   ObjectsDeleteAll(0, "NEXUS_ZONE_");
   
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
            int nr = (ArraySize(nSub) > 0) ? (int)StringToInteger(nSub[0]) : -1;
            
            if(nr == r) end++;
            else if(nr == 0) { // Unificação de Hiato (Peek-ahead v22.1)
                bool found = false;
                for(int look=1; look<=5 && (end+1+look) < totalR; look++) {
                    string v = hReg[totalR - 1 - (end+1+look)];
                    string s[]; StringSplit(v, '|', s);
                    if(ArraySize(s) > 0) {
                        int lr = (int)StringToInteger(s[0]);
                        if(lr == r) { found = true; break; }
                        if(lr != 0) break;
                    }
                }
                if(found) end++; else break;
            } else break;
         }
         
         // [TEMPORAL PRUNING v23.0]
         // Ignora caixas confirmadas (1, 2) com duração < 3, a menos que seja a barra atual (i=0)
         int duration = end - start + 1;
         bool isGhost = (r > 10);
         if(!isGhost && duration < 3 && start != 0) {
            i = end + 1; continue;
         }
         
         // [BODY-CENTERED MANIFOLD v23.0]
         // Delimita pela massa real (Open/Close), ignorando pavios anômalos
         double maxH = 0; double minL = 9999999;
         for(int k=start; k<=end; k++) {
            double bodyHigh = MathMax(iOpen(_Symbol, _Period, k), iClose(_Symbol, _Period, k));
            double bodyLow  = MathMin(iOpen(_Symbol, _Period, k), iClose(_Symbol, _Period, k));
            maxH = MathMax(maxH, bodyHigh);
            minL = MathMin(minL, bodyLow);
         }
         
         string bName = "NEXUS_ZONE_" + IntegerToString(boxIdx);
         int baseR = (r > 10) ? (r % 10) : r;
         color zClr;
         if(r == 21 || r == 22) zClr = RGB(255, 202, 40); // Amber Exhaustion
         else zClr = (baseR == 1) ? RGB(38, 166, 154) : RGB(239, 83, 80); 
         
         if(ObjectCreate(0, bName, OBJ_RECTANGLE, 0, iTime(_Symbol, _Period, start), maxH, iTime(_Symbol, _Period, end), minL)) {
             ObjectSetInteger(0, bName, OBJPROP_COLOR, zClr);
             ObjectSetInteger(0, bName, OBJPROP_WIDTH, 1);
             ObjectSetInteger(0, bName, OBJPROP_STYLE, isGhost ? STYLE_DOT : STYLE_SOLID);
             ObjectSetInteger(0, bName, OBJPROP_FILL, false); 
             ObjectSetInteger(0, bName, OBJPROP_BACK, true); 
             ObjectSetInteger(0, bName, OBJPROP_ZORDER, 0);
         }
         
         boxIdx++;
         i = end + 1;
      } else i++;
   }

   // 1.5 [CYT HIST DELETED PERMANENTLY]
   ObjectsDeleteAll(0, "NEXUS_CYT_HIST_");
   ObjectsDeleteAll(0, "NEXUS_CYT_ZONE_");

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
   ObjectsDeleteAll(0, "NEXUS_SIG_");
   
   // 4. ATUALIZAÇÃO DA NUVEM QUÂNTICA (v27.0 R-Exec Comet Trail)
   if(ArraySize(parts) > 10 && parts[10] != "") {
      string cloudParts[]; StringSplit(parts[10], ':', cloudParts);
      if(ArraySize(cloudParts) == 2) {
         double dx_val = StringToDouble(cloudParts[0]);
         string cloudHistory[]; StringSplit(cloudParts[1], ';', cloudHistory);
         int histSize = ArraySize(cloudHistory);
         
         double maxDensity = 0.0001;
         for(int h=0; h<histSize; h++) {
             if(cloudHistory[h] == "") continue;
             string cloudBins[]; StringSplit(cloudHistory[h], ',', cloudBins);
             for(int b=0; b<ArraySize(cloudBins); b++) {
                 string cVal[]; StringSplit(cloudBins[b], '|', cVal);
                 if(ArraySize(cVal) == 2) { double den = StringToDouble(cVal[1]); if(den > maxDensity) maxDensity = den; }
             }
         }

         int barCount = iBars(_Symbol, _Period);
         double currentPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         int boxCounter = 0;
         
         for(int h=0; h<histSize; h++) {
            if(cloudHistory[h] == "") continue;
            string cloudBins[]; StringSplit(cloudHistory[h], ',', cloudBins);
            
            // v27.0: Interpolação Temporal no MT5 (Rastro do Cometa)
            // Cada fatia ocupa o espaço de 1 candle
            datetime tEnd = (h == 0) ? TimeCurrent() + PeriodSeconds(_Period) * 10 : iTime(_Symbol, _Period, h-1);
            datetime tStart = iTime(_Symbol, _Period, h); 
            
            for(int b=0; b<ArraySize(cloudBins); b++) {
               string cVal[]; StringSplit(cloudBins[b], '|', cVal);
               if(ArraySize(cVal) != 2) continue;
               double pLevel = StringToDouble(cVal[0]);
               double den = StringToDouble(cVal[1]);
               
               if(den < maxDensity * 0.12) continue;
               
               string bName = "NEXUS_QC_" + IntegerToString(boxCounter);
               string tagName = "NEXUS_QCTAG_" + IntegerToString(boxCounter);
               boxCounter++;
               
               double ratio = den / maxDensity;
               
               // Decaimento Hawking no rastro (fading alpha)
               double timeDecay = MathPow(0.85, h); 
               double finalRatio = ratio * timeDecay;
               
               uchar rVal, gVal, bVal;
               if(pLevel > currentPrice) { 
                   rVal = (uchar)(15 + (70 * finalRatio)); 
                   gVal = (uchar)(5 + (15 * finalRatio)); 
                   bVal = (uchar)(10 + (20 * finalRatio)); 
               } else { 
                   rVal = (uchar)(5 + (15 * finalRatio)); 
                   gVal = (uchar)(20 + (70 * finalRatio)); 
                   bVal = (uchar)(18 + (60 * finalRatio)); 
               }
               
               if(ObjectFind(0, bName) < 0) ObjectCreate(0, bName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
               ObjectSetInteger(0, bName, OBJPROP_TIME, 0, tStart);
               ObjectSetDouble(0, bName, OBJPROP_PRICE, 0, pLevel + (dx_val * 0.55));
               ObjectSetInteger(0, bName, OBJPROP_TIME, 1, tEnd);
               ObjectSetDouble(0, bName, OBJPROP_PRICE, 1, pLevel - (dx_val * 0.55));
               ObjectSetInteger(0, bName, OBJPROP_COLOR, RGB(rVal, gVal, bVal));
               ObjectSetInteger(0, bName, OBJPROP_FILL, true);
               ObjectSetInteger(0, bName, OBJPROP_BACK, true);
               ObjectSetInteger(0, bName, OBJPROP_ZORDER, 1);
               
               if(h == 0 && ratio > 0.96) {
                   if(ObjectFind(0, tagName) < 0) ObjectCreate(0, tagName, OBJ_ARROW_RIGHT_PRICE, 0, 0, 0);
                   ObjectSetInteger(0, tagName, OBJPROP_TIME, 0, tEnd);
                   ObjectSetDouble(0, tagName, OBJPROP_PRICE, 0, pLevel);
                   ObjectSetInteger(0, tagName, OBJPROP_COLOR, clrCyan);
               } else {
                   ObjectDelete(0, tagName);
               }
            }
         }
         // Limpeza de resíduos in-place
         for(int k=boxCounter; k<2000; k++) {
             ObjectDelete(0, "NEXUS_QC_"+IntegerToString(k));
             ObjectDelete(0, "NEXUS_QCTAG_"+IntegerToString(k));
         }
      }
   }


   // 5. ATUALIZAÇÃO DA CROMODINÂMICA (MARKET QCD - SHORT SIGNALS)
   ObjectsDeleteAll(0, "NEXUS_QCD_");

   // 6. ATUALIZAÇÃO DA DINÂMICA DE FLUIDOS (LBM ICONS TÁTICOS)
   ObjectsDeleteAll(0, "NEXUS_LBM_ICON_");

   // 7. DECAIMENTO HAWKING (QGC) - FITAS DE GRAVIDADE
   ObjectsDeleteAll(0, "NEXUS_QGC_");   
   // --- 7.1 HARMONIC ENERGY SHELLS (QHO) ---
   ObjectsDeleteAll(0, "NEXUS_QHO_SHELL_");

   // --- 7.2 TUNNELING EXIT PORTAL (QTE) ---
   if(qteProb > 0.8) {
      string tName = "NEXUS_QTE_PORTAL";
      double tPrice = instAvgPrice + (qteAdvice == "TUNNEL_BULL" ? 200*_Point : -200*_Point); 
      if(ObjectFind(0, tName) < 0) ObjectCreate(0, tName, OBJ_ARROW_BUY, 0, iTime(_Symbol, _Period, 0), tPrice);
      ObjectSetInteger(0, tName, OBJPROP_ARROWCODE, 161); // Círculo concêntrico
      ObjectSetInteger(0, tName, OBJPROP_COLOR, clrGold);
      ObjectSetInteger(0, tName, OBJPROP_WIDTH, 5);
      ObjectSetInteger(0, tName, OBJPROP_BACK, false);
      ObjectSetInteger(0, tName, OBJPROP_ZORDER, 100);
   } else ObjectDelete(0, "NEXUS_QTE_PORTAL");

   // [DUPLICATE CLOUD REMOVED] - Primary heatmap is Section 4 (LuxAlgo Style)
   ObjectsDeleteAll(0, "NEXUS_CLOUD_");

   // Define prioridade máxima para todos os labels do HUD
   for(int i=0; i<ObjectsTotal(0, 0, OBJ_LABEL); i++) {
      string n = ObjectName(0, i, 0, OBJ_LABEL);
      if(StringFind(n, "NEXUS_") >= 0) ObjectSetInteger(0, n, OBJPROP_ZORDER, 100);
   }
   
   ChartRedraw();
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
   ObjectSetInteger(0, name, OBJPROP_ZORDER, 100);
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
                        ObjectSetInteger(0, lineName, OBJPROP_ZORDER, 0);
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
    ObjectSetInteger(0, stemName, OBJPROP_ZORDER, 100);

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
    ObjectSetInteger(0, btnName, OBJPROP_ZORDER, 100);
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
    else if(StringFind(status, "EXHAUSTION_BULL") >= 0) res = "Bull Exhaustion [!]";
    else if(StringFind(status, "EXHAUSTION_BEAR") >= 0) res = "Bear Exhaustion [!]";
    else if(StringFind(status, "GHOST_BULL") >= 0) res = "Bull Pre-Ignition";
    else if(StringFind(status, "GHOST_BEAR") >= 0) res = "Bear Pre-Ignition";
    if(StringFind(status, "ALERTA TOPOL") >= 0) res += " [!!]";
    if(StringFind(status, "TRAP") >= 0) res += " [TRAP]";
    return res;
}
color GetStatusColor(string status) {
    if(StringFind(status, "ALERTA TOPOL") >= 0) return RGB(255, 82, 82);
    if(StringFind(status, "EXHAUSTION") >= 0) return RGB(255, 202, 40); // Amber
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
void DrawNeuralHealthBar(string id, double health, int x, int y, int w, int h, int corner)
{
    string bgName = id + "_BG"; string fillName = id + "_FILL";
    if(ObjectFind(0, bgName) < 0) ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, bgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, x); ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, bgName, OBJPROP_XSIZE, w); ObjectSetInteger(0, bgName, OBJPROP_YSIZE, h);
    ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, RGB(12, 15, 20)); 
    ObjectSetInteger(0, bgName, OBJPROP_COLOR, RGB(35, 40, 50)); 
    ObjectSetInteger(0, bgName, OBJPROP_ZORDER, 100);

    int fillW = (int)(health * w); if(fillW > w) fillW = w; if(fillW < 2) fillW = 2;
    color hClr = (health < 0.3) ? RGB(239, 83, 80) : (health < 0.6 ? RGB(255, 167, 38) : RGB(38, 166, 154));
    
    if(ObjectFind(0, fillName) < 0) ObjectCreate(0, fillName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, fillName, OBJPROP_CORNER, corner); ObjectSetInteger(0, fillName, OBJPROP_XDISTANCE, x); ObjectSetInteger(0, fillName, OBJPROP_YDISTANCE, y);
    ObjectSetInteger(0, fillName, OBJPROP_XSIZE, fillW); ObjectSetInteger(0, fillName, OBJPROP_YSIZE, h);
    ObjectSetInteger(0, fillName, OBJPROP_BGCOLOR, hClr); ObjectSetInteger(0, fillName, OBJPROP_COLOR, hClr);
    ObjectSetInteger(0, fillName, OBJPROP_ZORDER, 100);
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
    ObjectSetInteger(0, fillName, OBJPROP_ZORDER, 100);
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
    
    ObjectSetInteger(0, name, OBJPROP_ZORDER, 100);
    ObjectSetInteger(0, name, OBJPROP_BACK, false);
    ObjectSetInteger(0, name, OBJPROP_HIDDEN, false);
}
color RGB(uchar r, uchar g, uchar b) { return (color)((b << 16) | (g << 8) | r); }
void DrawHUDRow(string id, string label, string val, color valClr, int baseX, int y, int panelW, int corner=CORNER_LEFT_UPPER)
{
    DrawHUDText(id + "_L", label, baseX + 15, y, RGB(140, 140, 145), 9, false, corner); 
    DrawHUDText(id + "_V", val, baseX + panelW - 15, y, valClr, 9, true, corner);
}
void DrawModernDashboard(string status, double instAvg, double health, string rht, string lbm, string zp, string qrw, string sec, string rmt, string ricci, string entropy, bool collapsed, string rhtFlash, double qddFidelity, double qteProb, string qteAdvice, int qhoN, double qhoStability, string qhoStatus, double mhdStrength, string setupTel)
{
    int panelW = 280; int panelH = 560; int corner = CORNER_LEFT_UPPER; int baseX = 20; int baseY = 30;
    string bgName = "NEXUS_HUD_BASE"; if(ObjectFind(0, bgName) < 0) ObjectCreate(0, bgName, OBJ_RECTANGLE_LABEL, 0, 0, 0);
    ObjectSetInteger(0, bgName, OBJPROP_CORNER, corner); ObjectSetInteger(0, bgName, OBJPROP_XDISTANCE, baseX); ObjectSetInteger(0, bgName, OBJPROP_YDISTANCE, baseY);
    ObjectSetInteger(0, bgName, OBJPROP_XSIZE, panelW); ObjectSetInteger(0, bgName, OBJPROP_YSIZE, panelH); 
    color mainBg = RGB(12, 15, 20);
    ObjectSetInteger(0, bgName, OBJPROP_BGCOLOR, mainBg);
    ObjectSetInteger(0, bgName, OBJPROP_COLOR, RGB(35, 40, 50)); 
    ObjectSetInteger(0, bgName, OBJPROP_BORDER_TYPE, BORDER_FLAT);
    ObjectSetInteger(0, bgName, OBJPROP_ZORDER, 100); 
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
    ObjectSetInteger(0, hBgName, OBJPROP_ZORDER, 100);

    int rowY = baseY + 45; int rowH = 20;
    for(int k=0; k<25; k++) {
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
        ObjectSetInteger(0, rBgName, OBJPROP_ZORDER, 100);
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
    
    DrawHUDRow("NEXUS_HUD_L_8", "Inst. Avg", DoubleToString(instAvg, 2), RGB(200, 200, 200), baseX, rowY, panelW, corner); rowY += rowH;

    // --- ACTIVE SETUP DISPLAY ---
     string setupDisplayName = "No Setup";
     color setupClr2 = RGB(80, 85, 100);
     if(StringFind(setupTel, "S1_") >= 0) { setupDisplayName = "Slingshot"; setupClr2 = RGB(255, 165, 0); }
     else if(StringFind(setupTel, "S2_") >= 0) { setupDisplayName = "Vacuum Kill"; setupClr2 = RGB(255, 50, 50); }
     else if(StringFind(setupTel, "S3_") >= 0) { setupDisplayName = "Bosonic Fire"; setupClr2 = RGB(255, 215, 0); }
     else if(StringFind(setupTel, "S4_") >= 0) { setupDisplayName = "Harmonic PB"; setupClr2 = RGB(0, 255, 180); }
     else if(StringFind(setupTel, "S5_") >= 0) { setupDisplayName = "!! COLLAPSE !!"; setupClr2 = RGB(255, 0, 85); }
     else if(StringFind(setupTel, "S6_") >= 0) { setupDisplayName = "Tunneling"; setupClr2 = RGB(0, 200, 255); }
     else if(StringFind(setupTel, "S7_") >= 0) { setupDisplayName = "TSUNAMI MACRO"; setupClr2 = RGB(0, 255, 255); }
     
     string setupDir2 = "";
     if(StringFind(setupTel, "LONG") >= 0) setupDir2 = " LONG";
     else if(StringFind(setupTel, "SHORT") >= 0) setupDir2 = " SHORT";
     
     DrawHUDRow("NEXUS_HUD_L_SETUP", "Active Setup", setupDisplayName + setupDir2, setupClr2, baseX, rowY, panelW, corner);
     rowY += rowH;

    // --- DIMENSIONAL COHERENCE (QDD) ---
    color qddClr = (MathAbs(qddFidelity) >= 0.8) ? RGB(0, 255, 120) : (MathAbs(qddFidelity) >= 0.4 ? RGB(255, 180, 0) : RGB(255, 60, 60));
    DrawHUDRow("NEXUS_HUD_L_QDD", "Dim. Coherence", DoubleToString(qddFidelity, 3), qddClr, baseX, rowY, panelW, corner);
    rowY += 15;
    DrawEnergyBar("NEXUS_QDD_BAR", MathAbs(qddFidelity), 1.0, baseX + 15, rowY, panelW - 30, 5, qddClr, corner);
    rowY += 12;

    color mhdClr = (mhdStrength > 7.0) ? clrGold : (mhdStrength > 4.0 ? RGB(255, 150, 0) : RGB(140, 140, 145));
    DrawHUDRow("NEXUS_HUD_L_MHD", "Magnetic Pull", DoubleToString(mhdStrength, 2) + " mT", mhdClr, baseX, rowY, panelW, corner);
    rowY += rowH;

    DrawHUDRow("NEXUS_HUD_L_QTE", "Tunnel Exit P", DoubleToString(qteProb * 100, 1) + "%", (qteProb > 0.8 ? clrGold : clrWhite), baseX, rowY, panelW, corner);
    rowY += rowH;

    // --- NEW: SCHRÖDINGER CLOUD ANALYSIS ---
    color qCloudClr = (qteProb > 0.6) ? RGB(0, 255, 255) : RGB(140, 140, 145);
    DrawHUDRow("NEXUS_HUD_L_QCLOUD_D", "Q-Cloud Density", DoubleToString(qteProb, 3), qCloudClr, baseX, rowY, panelW, corner);
    rowY += 15;
    DrawEnergyBar("NEXUS_QCLOUD_BAR", qteProb, 1.0, baseX + 15, rowY, panelW - 30, 6, qCloudClr, corner);
    rowY += 12;
    DrawHUDRow("NEXUS_HUD_L_QCLOUD_A", "Q-Cloud Analysis", qteAdvice, qCloudClr, baseX, rowY, panelW, corner);
    rowY += rowH;

    // --- QUANTUM HARMONIC OSCILLATOR (QHO) ---
    color qhoClr = (qhoN >= 5) ? RGB(255, 80, 80) : (qhoN >= 3 ? RGB(255, 200, 0) : RGB(0, 255, 180));
    DrawHUDRow("NEXUS_HUD_L_QHO_N", "Energy Level (n)", IntegerToString(qhoN), qhoClr, baseX, rowY, panelW, corner);
    rowY += 15;
    DrawEnergyBar("NEXUS_QHO_BAR", qhoStability, 1.0, baseX + 15, rowY, panelW - 30, 6, qhoClr, corner);
    rowY += 12;
    DrawHUDRow("NEXUS_HUD_L_QHO_S", "QHO State", qhoStatus, qhoClr, baseX, rowY, panelW, corner);
    
   // Protocolo de Soberania Total: Eleva toda a estrutura NEXUS (Texto e Painéis)
   for(int i=0; i<ObjectsTotal(0, 0, -1); i++) {
      string n = ObjectName(0, i, 0, -1);
      if(StringFind(n, "NEXUS_HUD") >= 0 || StringFind(n, "NEXUS_BG") >= 0 || StringFind(n, "NEXUS_RMT_BAR") >= 0) {
         ObjectSetInteger(0, n, OBJPROP_ZORDER, 100);
         ObjectSetInteger(0, n, OBJPROP_BACK, false);
      }
   }
   
   ChartRedraw();
}

//+------------------------------------------------------------------+
//| Sub-Módulos de Renderização Quântica                             |
//+------------------------------------------------------------------+

void DrawLBMHistory(string hist)
{
   ObjectsDeleteAll(0, "NEX_LBM_H_");
   if(StringLen(hist) == 0) return;
   string sigs[]; StringSplit(hist, ',', sigs);
   int t = ArraySize(sigs);
   for(int k=0; k < t && k < 150; k++) {
      int v = (int)StringToInteger(sigs[t - 1 - k]);
      if(v == 0) continue;
      datetime tm = iTime(_Symbol, _Period, k);
      double p = (v == 1) ? iLow(_Symbol, _Period, k) : iHigh(_Symbol, _Period, k);
      color c = (v == 1) ? RGB(0, 255, 255) : (v == 2 ? RGB(255, 0, 255) : clrGold);
      string n = "NEX_LBM_H_" + IntegerToString(k);
      ObjectCreate(0, n, OBJ_ARROW, 0, tm, p);
      ObjectSetInteger(0, n, OBJPROP_ARROWCODE, 159);
      ObjectSetInteger(0, n, OBJPROP_COLOR, c);
      ObjectSetInteger(0, n, OBJPROP_ANCHOR, (v == 1 ? ANCHOR_TOP : ANCHOR_BOTTOM));
   }
}

void DrawQGCHistory(string data)
{
   ObjectsDeleteAll(0, "NEX_QGC_");
   if(StringLen(data) == 0) return;
   string lines[]; StringSplit(data, ',', lines);
   for(int k=0; k<ArraySize(lines); k++) {
      string p[]; StringSplit(lines[k], '|', p);
      if(ArraySize(p) == 3) {
         double price = StringToDouble(p[1]);
         double mass = StringToDouble(p[2]);
         string n = "NEX_QGC_" + IntegerToString(k);
         ObjectCreate(0, n, OBJ_RECTANGLE, 0, iTime(_Symbol, _Period, (int)StringToInteger(p[0])), price + mass*10, TimeCurrent() + 3600, price - mass*10);
         ObjectSetInteger(0, n, OBJPROP_BGCOLOR, RGB(60, 10, 15));
         ObjectSetInteger(0, n, OBJPROP_FILL, true);
         ObjectSetInteger(0, n, OBJPROP_BACK, true);
      }
   }
}

void DrawQHOShells(string shells)
{
   ObjectsDeleteAll(0, "NEX_QHO_");
   if(StringLen(shells) == 0) return;
   string p[]; StringSplit(shells, ',', p);
   for(int k=0; k<ArraySize(p); k++) {
      double pr = StringToDouble(p[k]);
      string n = "NEX_QHO_" + IntegerToString(k);
      ObjectCreate(0, n, OBJ_HLINE, 0, 0, pr);
      ObjectSetInteger(0, n, OBJPROP_COLOR, RGB(0, 60, 60));
      ObjectSetInteger(0, n, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0, n, OBJPROP_BACK, true);
   }
}

