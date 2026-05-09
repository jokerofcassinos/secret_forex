with open(r'd:\AI Brain\US30\Code\MQL5\Nexus_Observer.mq5', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''    // --- SETUP ENGINE PARSING (v1.0) ---
     string setupTel = (ArraySize(parts) > 39) ? parts[39] : "NO_SETUP";

   DrawModernDashboard(statusTxt, instAvgPrice, health, rhtStatus, lbm_signal, z_signal, qrw_signal, secData, rmt_signal, ricci_c, h_entropy, (is_collapsed == "1"), rhtFlash, qddFidelity, qteProb, qteAdvice, qhoN, qhoStability, qhoStatus, mhdStrength, setupTel);

     // --- SETUP VISUALS ---
     DrawSetupSignal(setupTel);'''

new = '''    // --- SETUP ENGINE PARSING (v1.0) ---
     string setupTel = (ArraySize(parts) > 39) ? parts[39] : "NO_SETUP";
     string setupHistory = (ArraySize(parts) > 40) ? parts[40] : "";

   DrawModernDashboard(statusTxt, instAvgPrice, health, rhtStatus, lbm_signal, z_signal, qrw_signal, secData, rmt_signal, ricci_c, h_entropy, (is_collapsed == "1"), rhtFlash, qddFidelity, qteProb, qteAdvice, qhoN, qhoStability, qhoStatus, mhdStrength, setupTel);

     // --- SETUP VISUALS (CURRENT BAR) ---
     DrawSetupSignal(setupTel);

     // --- SETUP HISTORY VISUALS ---
     ObjectsDeleteAll(0, "NEXUS_SH_");
     if(StringLen(setupHistory) > 0) {
        string shSteps[]; StringSplit(setupHistory, ',', shSteps);
        int totalSH = ArraySize(shSteps);
        for(int sh=0; sh < totalSH && sh < iBars(_Symbol, _Period) && sh < 500; sh++) {
           int shVal = (int)StringToInteger(shSteps[totalSH - 1 - sh]);
           if(shVal == 0) continue;
           
           bool isLong = (shVal > 0);
           int setupNum = MathAbs(shVal);
           
           color shClr = clrWhite;
           string shLabel = "";
           if(setupNum == 1) { shClr = RGB(255, 165, 0);  shLabel = "S1"; }
           else if(setupNum == 2) { shClr = RGB(255, 50, 50);  shLabel = "S2"; }
           else if(setupNum == 3) { shClr = RGB(255, 215, 0);  shLabel = "S3"; }
           else if(setupNum == 4) { shClr = RGB(0, 255, 180);  shLabel = "S4"; }
           else if(setupNum == 5) { shClr = RGB(255, 0, 85);   shLabel = "S5"; }
           else if(setupNum == 6) { shClr = RGB(0, 200, 255);  shLabel = "S6"; }
           else if(setupNum == 7) { shClr = RGB(0, 255, 255);  shLabel = "S7"; }
           
           double pHigh = iHigh(_Symbol, _Period, sh);
           double pLow = iLow(_Symbol, _Period, sh);
           double atr_off = (iHigh(_Symbol, _Period, iHighest(_Symbol, _Period, MODE_HIGH, 20, sh)) - iLow(_Symbol, _Period, iLowest(_Symbol, _Period, MODE_LOW, 20, sh))) * 0.08;
           if(atr_off < 150 * _Point) atr_off = 150 * _Point;
           
           double markerP = isLong ? pLow - atr_off * 3.5 : pHigh + atr_off * 3.5;
           
           string shName = "NEXUS_SH_D_" + IntegerToString(sh);
           if(ObjectFind(0, shName) < 0) ObjectCreate(0, shName, OBJ_ARROW, 0, 0, 0);
           ObjectSetInteger(0, shName, OBJPROP_TIME, iTime(_Symbol, _Period, sh));
           ObjectSetDouble(0, shName, OBJPROP_PRICE, markerP);
           ObjectSetInteger(0, shName, OBJPROP_ARROWCODE, 74);
           ObjectSetInteger(0, shName, OBJPROP_COLOR, shClr);
           ObjectSetInteger(0, shName, OBJPROP_WIDTH, 2);
           ObjectSetInteger(0, shName, OBJPROP_ANCHOR, isLong ? ANCHOR_TOP : ANCHOR_BOTTOM);
           ObjectSetInteger(0, shName, OBJPROP_BACK, false);
           ObjectSetInteger(0, shName, OBJPROP_ZORDER, 90);
           
           string shTxtName = "NEXUS_SH_T_" + IntegerToString(sh);
           if(ObjectFind(0, shTxtName) < 0) ObjectCreate(0, shTxtName, OBJ_TEXT, 0, 0, 0);
           ObjectSetInteger(0, shTxtName, OBJPROP_TIME, iTime(_Symbol, _Period, sh));
           ObjectSetDouble(0, shTxtName, OBJPROP_PRICE, markerP + (isLong ? -atr_off * 0.5 : atr_off * 0.5));
           ObjectSetString(0, shTxtName, OBJPROP_TEXT, shLabel + (isLong ? " L" : " S"));
           ObjectSetString(0, shTxtName, OBJPROP_FONT, "Consolas");
           ObjectSetInteger(0, shTxtName, OBJPROP_FONTSIZE, 7);
           ObjectSetInteger(0, shTxtName, OBJPROP_COLOR, shClr);
           ObjectSetInteger(0, shTxtName, OBJPROP_ANCHOR, isLong ? ANCHOR_LEFT_UPPER : ANCHOR_LEFT_LOWER);
           ObjectSetInteger(0, shTxtName, OBJPROP_BACK, false);
        }
     }'''

if old in content:
    content = content.replace(old, new)
    with open(r'd:\AI Brain\US30\Code\MQL5\Nexus_Observer.mq5', 'w', encoding='utf-8') as f:
        f.write(content)
    print('SUCCESS: Setup history rendering added to MQ5')
else:
    print('ERROR: Old block not found')
