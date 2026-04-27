//+------------------------------------------------------------------+
//|                                              Nexus_Observer.mq5 |
//|                                  Copyright 2026, NEXUS AGI CEO |
//+------------------------------------------------------------------+
#property copyright "NEXUS AGI CEO"
#property version   "82.00"
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
   if(ArraySize(parts) < 8) return;

   string statusTxt = parts[2];
   string historyZonas = parts[4];
   string historySignals = parts[7];
   
   DrawLabel("NEXUS_HEADER", "AETHELGARD [TRUE SYNC] V82", 10, 20, clrCyan, 12);
   
   // EXIBIÇÃO DA PREVISÃO / STATUS v82
   color sClr = clrWhite;
   if(StringFind(statusTxt, "PREVISAO") >= 0) sClr = clrGold;
   if(StringFind(statusTxt, "ATIVO") >= 0) sClr = clrSpringGreen;
   if(StringFind(statusTxt, "ATIVA") >= 0) sClr = clrLime;
   
   DrawLabel("NEXUS_STATUS", "PREVISAO: " + statusTxt, 10, 40, sClr, 10);

   // 1. DESENHO DAS ZONAS
   string histZ[]; StringSplit(historyZonas, ',', histZ);
   int totalZ = ArraySize(histZ);
   ObjectsDeleteAll(0, "NEXUS_ZONE_");
   ObjectsDeleteAll(0, "NEXUS_TXT_");
   
   int i = 0; int boxCount = 0;
   while(i < totalZ && i < iBars(_Symbol, _Period)) {
      string scoreStr = histZ[totalZ - 1 - i];
      string subP[]; StringSplit(scoreStr, '|', subP);
      int regimeVal = (int)StringToInteger(subP[0]);
      
      if(regimeVal != 0) {
         int startIdx = i; int endIdx = i;
         while(endIdx + 1 < totalZ && endIdx + 1 < iBars(_Symbol, _Period)) {
            string nextS = histZ[totalZ - 1 - (endIdx + 1)];
            string nSub[]; StringSplit(nextS, '|', nSub);
            if((int)StringToInteger(nSub[0]) == regimeVal) endIdx++; else break;
         }
         
         string bName = "NEXUS_ZONE_" + IntegerToString(boxCount);
         datetime tS = iTime(_Symbol, _Period, startIdx);
         datetime tE = iTime(_Symbol, _Period, endIdx);
         double hP = 0, lP = 9999999;
         for(int k=startIdx; k<=endIdx; k++) { hP = MathMax(hP, iHigh(_Symbol, _Period, k)); lP = MathMin(lP, iLow(_Symbol, _Period, k)); }
         
         color zClr = (regimeVal == 1) ? clrLime : clrRed;
         
         ObjectCreate(0, bName, OBJ_RECTANGLE, 0, tS, hP, tE, lP);
         ObjectSetInteger(0, bName, OBJPROP_COLOR, zClr);
         ObjectSetInteger(0, bName, OBJPROP_WIDTH, 2);
         ObjectSetInteger(0, bName, OBJPROP_FILL, false);
         
         string tName = "NEXUS_TXT_" + IntegerToString(boxCount);
         ObjectCreate(0, tName, OBJ_TEXT, 0, tS, hP);
         ObjectSetString(0, tName, OBJPROP_TEXT, (regimeVal == 1 ? "[ BULL ]" : "[ BEAR ]"));
         ObjectSetInteger(0, tName, OBJPROP_COLOR, zClr);
         ObjectSetInteger(0, tName, OBJPROP_FONTSIZE, 9);
         ObjectSetInteger(0, tName, OBJPROP_ANCHOR, ANCHOR_LEFT_LOWER);
         
         boxCount++;
         i = endIdx + 1;
      } else i++;
   }

   // 2. DESENHO DOS SINAIS DE ANOMALIA (TEXTOS)
   string histS[]; StringSplit(historySignals, ',', histS);
   int totalS = ArraySize(histS);
   ObjectsDeleteAll(0, "NEXUS_SIG_");
   
   for(int j=0; j < totalS && j < iBars(_Symbol, _Period); j++) {
      int signalVal = (int)StringToInteger(histS[totalS - 1 - j]);
      if(signalVal != 0) {
         string sName = "NEXUS_SIG_" + IntegerToString(j);
         datetime sTime = iTime(_Symbol, _Period, j);
         
         // Aumentando o distanciamento para o texto não sobrepor a vela
         double sPrice = (signalVal == 1) ? iLow(_Symbol, _Period, j) - 40 * _Point : iHigh(_Symbol, _Period, j) + 40 * _Point;
         
         ObjectCreate(0, sName, OBJ_TEXT, 0, sTime, sPrice);
         string textMsg = (signalVal == 1) ? "[BULL_VOLUME]" : "[BEAR_VOLUME]";
         ObjectSetString(0, sName, OBJPROP_TEXT, textMsg);
         ObjectSetString(0, sName, OBJPROP_FONT, "Consolas");
         ObjectSetInteger(0, sName, OBJPROP_FONTSIZE, 8);
         ObjectSetInteger(0, sName, OBJPROP_COLOR, (signalVal == 1 ? clrDodgerBlue : clrOrangeRed));
         ObjectSetInteger(0, sName, OBJPROP_ANCHOR, (signalVal == 1 ? ANCHOR_TOP : ANCHOR_BOTTOM));
      }
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
