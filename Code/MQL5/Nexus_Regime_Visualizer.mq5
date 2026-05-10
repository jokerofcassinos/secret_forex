//+------------------------------------------------------------------+
//|                                        Nexus_Regime_Visualizer.mq5|
//|                                  Copyright 2026, NEXUS ASI Core  |
//+------------------------------------------------------------------+
#property copyright "NEXUS ASI"
#property version   "1.00"
#property strict

//--- Parâmetros de Conexão
input string   InpURL = "http://127.0.0.1:5000/nexus";

int OnInit() {
    EventSetTimer(1);
    return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) {
    EventKillTimer();
    ObjectsDeleteAll(0, "NEXUS_ZONE_");
}

void OnTick() {
    // EA Operacional - Foco em visualização de Regime
}

void OnTimer() {
    string result, headers;
    string cookie = NULL;
    char post[], res[];
    
    // Protocolo de extração: Busca apenas a string de Regime (Campo 4: historyRegimes)
    if(WebRequest("GET", InpURL + "?tf=" + IntegerToString(_Period) + "&symbol=" + _Symbol, cookie, NULL, 500, post, 0, res, headers) == 200) {
        string data = CharArrayToString(res);
        string parts[];
        if(StringSplit(data, ';', parts) > 4) {
            DrawRegimeBoxes(parts[4]);
        }
    }
}

void DrawRegimeBoxes(string historyRegimes) {
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
            
            datetime t1 = iTime(_Symbol, _Period, start);
            datetime t2 = iTime(_Symbol, _Period, end);
            
            string bName = "NEXUS_ZONE_" + IntegerToString(boxIdx);
            string tLine = "NEXUS_ZLINE_T_" + IntegerToString(boxIdx);
            string bLine = "NEXUS_ZLINE_B_" + IntegerToString(boxIdx);
            
            // Cores Profissionais Neo-TradingView
            color zClr = (r == 1) ? RGB(38, 166, 154) : RGB(239, 83, 80);
            
            // 1. A ZONA (Fundo ultra-sutil)
            if(ObjectFind(0, bName) < 0) ObjectCreate(0, bName, OBJ_RECTANGLE, 0, 0, 0, 0, 0);
            ObjectSetInteger(0, bName, OBJPROP_TIME, 0, t1);
            ObjectSetDouble(0, bName, OBJPROP_PRICE, 0, maxH);
            ObjectSetInteger(0, bName, OBJPROP_TIME, 1, t2);
            ObjectSetDouble(0, bName, OBJPROP_PRICE, 1, minL);
            ObjectSetInteger(0, bName, OBJPROP_COLOR, zClr);
            ObjectSetInteger(0, bName, OBJPROP_WIDTH, 1);
            ObjectSetInteger(0, bName, OBJPROP_FILL, true);
            ObjectSetInteger(0, bName, OBJPROP_BACK, true);
            ObjectSetInteger(0, bName, OBJPROP_BGCOLOR, ColorToARGB(zClr, 15)); // Alpha 15 (Quase invisível, apenas brilho)

            // 2. LINHAS DE CONTORNO (Estrutura da Fita)
            if(ObjectFind(0, tLine) < 0) ObjectCreate(0, tLine, OBJ_TREND, 0, t1, maxH, t2, maxH);
            else { ObjectSetInteger(0, tLine, OBJPROP_TIME, 0, t1); ObjectSetDouble(0, tLine, OBJPROP_PRICE, 0, maxH); ObjectSetInteger(0, tLine, OBJPROP_TIME, 1, t2); ObjectSetDouble(0, tLine, OBJPROP_PRICE, 1, maxH); }
            ObjectSetInteger(0, tLine, OBJPROP_COLOR, zClr);
            ObjectSetInteger(0, tLine, OBJPROP_STYLE, STYLE_SOLID);
            ObjectSetInteger(0, tLine, OBJPROP_WIDTH, 1);
            ObjectSetInteger(0, tLine, OBJPROP_RAY_RIGHT, false);

            if(ObjectFind(0, bLine) < 0) ObjectCreate(0, bLine, OBJ_TREND, 0, t1, minL, t2, minL);
            else { ObjectSetInteger(0, bLine, OBJPROP_TIME, 0, t1); ObjectSetDouble(0, bLine, OBJPROP_PRICE, 0, minL); ObjectSetInteger(0, bLine, OBJPROP_TIME, 1, t2); ObjectSetDouble(0, bLine, OBJPROP_PRICE, 1, minL); }
            ObjectSetInteger(0, bLine, OBJPROP_COLOR, zClr);
            ObjectSetInteger(0, bLine, OBJPROP_STYLE, STYLE_SOLID);
            ObjectSetInteger(0, bLine, OBJPROP_WIDTH, 1);
            ObjectSetInteger(0, bLine, OBJPROP_RAY_RIGHT, false);
            
            boxIdx++;
            i = end + 1;
        } else i++;
    }
    // Limpeza de resíduos
    for(int k=boxIdx; k<100; k++) {
        ObjectDelete(0, "NEXUS_ZONE_"+IntegerToString(k));
        ObjectDelete(0, "NEXUS_ZLINE_T_"+IntegerToString(k));
        ObjectDelete(0, "NEXUS_ZLINE_B_"+IntegerToString(k));
    }
    ChartRedraw();
}


color RGB(uchar r, uchar g, uchar b) { return (color)((b << 16) | (g << 8) | r); }
