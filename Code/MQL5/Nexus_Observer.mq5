//+------------------------------------------------------------------+
//|                                              Nexus_Observer.mq5 |
//|                                  Copyright 2026, NEXUS AGI CEO |
//+------------------------------------------------------------------+
#property copyright "NEXUS AGI CEO"
#property version   "11.00"
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
   
   if(res == 200)
   {
      string response = CharArrayToString(result);
      ParseAndDraw(response);
   }
}

void ParseAndDraw(string data)
{
   string parts[];
   StringSplit(data, ';', parts);
   
   if(ArraySize(parts) < 5) return;

   string historyStr = parts[4];
   string historyParts[];
   StringSplit(historyStr, ',', historyParts);
   int total = ArraySize(historyParts);
   
   ObjectsDeleteAll(0, "NEXUS_ZONE_");
   ObjectsDeleteAll(0, "NEXUS_TXT_");

   int i = 0;
   int boxCount = 0;
   
   while(i < total && i < iBars(_Symbol, _Period))
   {
      string scoreStr = historyParts[total - 1 - i];
      string subParts[];
      StringSplit(scoreStr, '|', subParts);
      int regimeVal = (int)StringToInteger(subParts[0]);
      
      if(regimeVal != 0)
      {
         int startIdx = i;
         int endIdx = i;
         
         while(endIdx + 1 < total && endIdx + 1 < iBars(_Symbol, _Period))
         {
            string nextScoreStr = historyParts[total - 1 - (endIdx + 1)];
            string nextSubParts[];
            StringSplit(nextScoreStr, '|', nextSubParts);
            if((int)StringToInteger(nextSubParts[0]) == regimeVal)
               endIdx++;
            else
               break;
         }
         
         // FILTRO MASTER: Mínimo 10 candles para ser uma zona institucional
         int duration = endIdx - startIdx;
         if(duration >= 10)
         {
            string boxName = "NEXUS_ZONE_" + IntegerToString(boxCount);
            string txtNameStart = "NEXUS_TXT_S_" + IntegerToString(boxCount);
            string txtNameEnd = "NEXUS_TXT_E_" + IntegerToString(boxCount);
            
            datetime timeStart = iTime(_Symbol, _Period, startIdx);
            datetime timeEnd = iTime(_Symbol, _Period, endIdx);
            
            double highPrice = 0, lowPrice = 9999999;
            for(int k=startIdx; k<=endIdx; k++) {
               highPrice = MathMax(highPrice, iHigh(_Symbol, _Period, k));
               lowPrice = MathMin(lowPrice, iLow(_Symbol, _Period, k));
            }

            color zoneColor = (regimeVal == 1) ? clrLime : clrRed;

            // Criar Moldura Principal
            ObjectCreate(0, boxName, OBJ_RECTANGLE, 0, timeStart, highPrice, timeEnd, lowPrice);
            ObjectSetInteger(0, boxName, OBJPROP_COLOR, zoneColor);
            ObjectSetInteger(0, boxName, OBJPROP_WIDTH, 2);
            ObjectSetInteger(0, boxName, OBJPROP_FILL, false);
            ObjectSetInteger(0, boxName, OBJPROP_BACK, false);

            // Label de Início
            ObjectCreate(0, txtNameStart, OBJ_TEXT, 0, timeStart, highPrice);
            string labelS = (regimeVal == 1) ? ">> BULL DOMAIN" : ">> BEAR DOMAIN";
            ObjectSetString(0, txtNameStart, OBJPROP_TEXT, labelS);
            ObjectSetInteger(0, txtNameStart, OBJPROP_COLOR, zoneColor);
            ObjectSetInteger(0, txtNameStart, OBJPROP_FONTSIZE, 9);
            ObjectSetInteger(0, txtNameStart, OBJPROP_ANCHOR, ANCHOR_LEFT_LOWER);

            // Label de Fim (Duração)
            ObjectCreate(0, txtNameEnd, OBJ_TEXT, 0, timeEnd, lowPrice);
            ObjectSetString(0, txtNameEnd, OBJPROP_TEXT, "DUR: " + IntegerToString(duration) + "c");
            ObjectSetInteger(0, txtNameEnd, OBJPROP_COLOR, clrGray);
            ObjectSetInteger(0, txtNameEnd, OBJPROP_FONTSIZE, 7);
            ObjectSetInteger(0, txtNameEnd, OBJPROP_ANCHOR, ANCHOR_RIGHT_UPPER);

            boxCount++;
         }
         i = endIdx + 1;
      }
      else i++;
   }
   
   DrawLabel("NEXUS_TITLE", "AETHELGARD [QUANTUM DOMAIN] V11.0", 10, 20, clrCyan, 12);
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
