//+------------------------------------------------------------------+
//|                                              Nexus_Observer.mq5 |
//|                                  Copyright 2026, NEXUS AGI CEO |
//+------------------------------------------------------------------+
#property copyright "NEXUS AGI CEO"
#property version   "112.00"
#property strict

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
      ParseAndDraw(response);
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
   
   DrawLabel("NEXUS_HEADER", "AETHELGARD [TRUE SYNC] V112", 10, 20, clrCyan, 12);
   
   color sClr = clrWhite;
   if(health < 0.3) sClr = clrRed;
   else if(health < 0.6) sClr = clrGold;
   else sClr = clrSpringGreen;
   
   DrawLabel("NEXUS_STATUS", "STATUS: " + statusTxt, 10, 40, sClr, 10);
   DrawLabel("NEXUS_INST_AVG", "INST_AVG_PRICE: " + DoubleToString(instAvgPrice, 2), 10, 60, clrGray, 9);

   // 1. DESENHO DAS CAIXAS
   string hReg[]; StringSplit(historyRegimes, ',', hReg);
   int totalR = ArraySize(hReg);
   ObjectsDeleteAll(0, "NEXUS_ZONE_");
   
   int i = 0; int boxCount = 0;
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
         
         string bName = "NEXUS_ZONE_" + IntegerToString(boxCount);
         color zClr = (r == 1) ? clrLime : clrRed;
         ObjectCreate(0, bName, OBJ_RECTANGLE, 0, iTime(_Symbol, _Period, start), maxH, iTime(_Symbol, _Period, end), minL);
         ObjectSetInteger(0, bName, OBJPROP_COLOR, zClr);
         ObjectSetInteger(0, bName, OBJPROP_WIDTH, 2);
         ObjectSetInteger(0, bName, OBJPROP_FILL, false);
         boxCount++;
         i = end + 1;
      } else i++;
   }

   // 2. DESENHO DOS SINAIS DE VOLUME (RESTAURADO)
   string hSig[]; StringSplit(historySignals, ',', hSig);
   ObjectsDeleteAll(0, "NEXUS_SIG_");
   
   for(int j=0; j < ArraySize(hSig) && j < iBars(_Symbol, _Period); j++) {
      int sigVal = (int)StringToInteger(hSig[ArraySize(hSig) - 1 - j]);
      if(sigVal != 0) {
         string sName = "NEXUS_SIG_" + IntegerToString(j);
         datetime sTime = iTime(_Symbol, _Period, j);
         double sPrice = (sigVal == 1) ? iLow(_Symbol, _Period, j) - 80 * _Point : iHigh(_Symbol, _Period, j) + 80 * _Point;
         
         ObjectCreate(0, sName, OBJ_TEXT, 0, sTime, sPrice);
         string textMsg = (sigVal == 1) ? "[BULL_VOLUME]" : "[BEAR_VOLUME]";
         ObjectSetString(0, sName, OBJPROP_TEXT, textMsg);
         ObjectSetInteger(0, sName, OBJPROP_COLOR, (sigVal == 1 ? clrDodgerBlue : clrOrangeRed));
         ObjectSetInteger(0, sName, OBJPROP_FONTSIZE, 8);
         ObjectSetInteger(0, sName, OBJPROP_ANCHOR, (sigVal == 1 ? ANCHOR_TOP : ANCHOR_BOTTOM));
      }
   }

   // 3. DESENHO DOS TACTICAL DOTS (GRADIENTE)
   string hDots[]; StringSplit(historyDots, ',', hDots);
   ObjectsDeleteAll(0, "NEXUS_DOT_");
   
   for(int d=0; d < ArraySize(hDots) && d < iBars(_Symbol, _Period); d++) {
      int dotVal = (int)StringToInteger(hDots[ArraySize(hDots) - 1 - d]);
      if(dotVal == 0) continue;
      
      color dClr = clrBlack;
      if(dotVal == 1) dClr = clrSpringGreen;
      if(dotVal == 11) dClr = clrMediumSeaGreen;
      if(dotVal == 12) dClr = clrForestGreen;
      if(dotVal == 13) dClr = clrDarkGreen;
      if(dotVal == 2) dClr = clrRed;
      if(dotVal == 21) dClr = clrCrimson;
      if(dotVal == 22) dClr = clrFireBrick;
      if(dotVal == 23) dClr = clrMaroon;
      
      if(dClr == clrBlack) continue;

      string dName = "NEXUS_DOT_" + IntegerToString(d);
      datetime dTime = iTime(_Symbol, _Period, d);
      double dPrice = (dotVal < 20) ? iLow(_Symbol, _Period, d) - 40*_Point : iHigh(_Symbol, _Period, d) + 40*_Point;
      
      ObjectCreate(0, dName, OBJ_ARROW, 0, dTime, dPrice);
      ObjectSetInteger(0, dName, OBJPROP_ARROWCODE, 159);
      ObjectSetInteger(0, dName, OBJPROP_COLOR, dClr);
      ObjectSetInteger(0, dName, OBJPROP_WIDTH, (dotVal < 10 ? 2 : 1));
   }
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
