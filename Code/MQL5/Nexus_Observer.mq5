//+------------------------------------------------------------------+
//|                                              Nexus_Observer.mq5 |
//|                                  Copyright 2026, NEXUS AGI CEO |
//+------------------------------------------------------------------+
#property copyright "NEXUS AGI CEO"
#property version   "71.00"
#property strict

#include <Canvas\Canvas.mqh>

// Instância Master do Renderizador (v71.0 - Stable Volumetric Plasma)
CCanvas m_canvas;
string m_canvas_name = "NEXUS_QUANTUM_CANVAS";

// Buffer de Campo Contínuo [Snapshots][Bins]
double m_field[801][512]; 
double m_field_meta[801][4]; // [p_min][p_max][Time][Price_Actual]

// Memória de Estado
string last_payload = "";
int m_chart_w = 0;
int m_chart_h = 0;

// --- PROTÓTIPO MESTRE ---
void ParseAndDraw(string data);
uint GetLushColor(double val, double age);
void BlendSmoothPixel(CCanvas &canvas, int x, int y, uint clr);

//+------------------------------------------------------------------+
int OnInit() { 
    EventSetTimer(1); 
    ChartSetInteger(0, CHART_SHOW_TRADE_LEVELS, false); 
    ObjectsDeleteAll(0, "NEXUS_"); 
    
    m_chart_w = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
    m_chart_h = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS);
    
    if(!m_canvas.CreateBitmapLabel(m_canvas_name, 0, 0, m_chart_w, m_chart_h, COLOR_FORMAT_ARGB_NORMALIZE)) return(INIT_FAILED);
    ObjectSetInteger(0, m_canvas_name, OBJPROP_BACK, true); 
    m_canvas.Erase(0x00000000);
    m_canvas.Update();
    
    return(INIT_SUCCEEDED); 
}

void OnDeinit(const int reason) { 
    EventKillTimer(); 
    ObjectsDeleteAll(0, "NEXUS_"); 
    m_canvas.Destroy(); 
}

void OnTick() { UpdateDashboard(); }
void OnTimer() { UpdateDashboard(); }

void UpdateDashboard()
{
   string url = "http://127.0.0.1:5000/nexus?tf=" + IntegerToString(_Period) + "&symbol=" + _Symbol;
   string cookie=NULL,headers;
   char post[],result[];
   int res;
   
   res = WebRequest("GET", url, cookie, NULL, 5000, post, 0, result, headers);
   if(res == 200) {
      string response = CharArrayToString(result);
      StringTrimRight(response);
      ParseAndDraw(response);
      last_payload = response;
   }
}

void BlendSmoothPixel(CCanvas &canvas, int x, int y, uint clr)
{
   if(x < 0 || x >= m_chart_w || y < 0 || y >= m_chart_h) return;
   
   uchar base_alpha = (uchar)((clr >> 24) & 0xFF);
   if(base_alpha < 1) return;
   
   uchar r_base = (uchar)((clr >> 16) & 0xFF);
   uchar g_base = (uchar)((clr >> 8) & 0xFF);
   uchar b_base = (uchar)(clr & 0xFF);
   
   uint back = canvas.PixelGet(x, y);
   
   uchar a1_pre = (uchar)((back >> 24) & 0xFF);
   uchar r1_pre = (uchar)((back >> 16) & 0xFF);
   uchar g1_pre = (uchar)((back >> 8) & 0xFF);
   uchar b1_pre = (uchar)(back & 0xFF);
   
   // Blend aditivo para brilho liso (Bilinear)
   double alpha_blend = (double)base_alpha / 255.0;
   
   uint r_new = (uint)MathMin(255, r_base * alpha_blend + r1_pre * (1.0 - alpha_blend * 0.5));
   uint g_new = (uint)MathMin(255, g_base * alpha_blend + g1_pre * (1.0 - alpha_blend * 0.5));
   uint b_new = (uint)MathMin(255, b_base * alpha_blend + b1_pre * (1.0 - alpha_blend * 0.5));
   uint a_new = (uint)MathMin(255, base_alpha + a1_pre); 
   
   canvas.PixelSet(x, y, (a_new << 24) | (r_new << 16) | (g_new << 8) | b_new);
}


void ParseAndDraw(string data)
{
   if(ObjectFind(0, m_canvas_name) < 0) {
      m_chart_w = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
      m_chart_h = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS);
      m_canvas.CreateBitmapLabel(m_canvas_name, 0, 0, m_chart_w, m_chart_h, COLOR_FORMAT_ARGB_NORMALIZE);
      ObjectSetInteger(0, m_canvas_name, OBJPROP_BACK, true);
   }

   int curW = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
   int curH = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS);
   if(curW != m_chart_w || curH != m_chart_h) {
      m_chart_w = curW; m_chart_h = curH;
      m_canvas.Resize(m_chart_w, m_chart_h);
      ObjectSetInteger(0, m_canvas_name, OBJPROP_BACK, true);
   }

   m_canvas.Erase(0x00000000);
   
   string parts[];
   StringSplit(data, ';', parts);
   if(ArraySize(parts) < 11) { m_canvas.Update(); return; }

   // 1. CAIXAS DE REGIME (SMC EVOLVED)
   string historyRegimes = parts[4]; 
   ObjectsDeleteAll(0, "NEXUS_ZONE_");
   string hReg[]; StringSplit(historyRegimes, ',', hReg);
   int totalR = ArraySize(hReg);
   int boxIdx = 0;
   for(int i=0; i < totalR && i < iBars(_Symbol, _Period); i++) {
      string val = hReg[totalR - 1 - i];
      string sub[]; StringSplit(val, '|', sub);
      if(ArraySize(sub) < 1) continue;
      int r = (int)StringToInteger(sub[0]);
      if(r != 0) {
         int start = i; int end = i;
         while(end + 1 < totalR && end + 1 < iBars(_Symbol, _Period)) {
            string nextVal = hReg[totalR - 1 - (end + 1)];
            string nSub[]; StringSplit(nextVal, '|', nSub);
            int nr = (ArraySize(nSub) > 0) ? (int)StringToInteger(nSub[0]) : -1;
            if(nr == r) end++; else break;
         }
         double maxH = 0; double minL = 9999999;
         for(int k=start; k<=end; k++) {
            maxH = MathMax(maxH, MathMax(iOpen(_Symbol, _Period, k), iClose(_Symbol, _Period, k)));
            minL = MathMin(minL, MathMin(iOpen(_Symbol, _Period, k), iClose(_Symbol, _Period, k)));
         }
         string bName = "NEXUS_ZONE_" + IntegerToString(boxIdx);
         color zClr = (r == 1) ? RGB(0, 255, 255) : (r == 2 ? RGB(255, 0, 255) : RGB(255, 202, 40));
         if(ObjectCreate(0, bName, OBJ_RECTANGLE, 0, iTime(_Symbol, _Period, start), maxH, iTime(_Symbol, _Period, end), minL)) {
             ObjectSetInteger(0, bName, OBJPROP_COLOR, zClr);
             ObjectSetInteger(0, bName, OBJPROP_FILL, false);
             ObjectSetInteger(0, bName, OBJPROP_BACK, true);
             ObjectSetInteger(0, bName, OBJPROP_WIDTH, 1);
         }
         boxIdx++; i = end;
      }
   }

   // 2. ABSOLUTE SPECTRAL VAPOR SYNTHESIS (v71.6 - LUSH NEBULA)
   string cloud_str = parts[10];
   if(cloud_str != "") {
      string cloudHistory[]; StringSplit(cloud_str, '^', cloudHistory);
      int histSize = ArraySize(cloudHistory);
      
      for(int h=0; h<histSize && h<801; h++) {
         string snapParts[]; StringSplit(cloudHistory[h], '|', snapParts);
         if(ArraySize(snapParts) < 3) continue;
         
         double p_min = StringToDouble(snapParts[0]);
         double p_max = StringToDouble(snapParts[1]);
         string hex   = snapParts[2];
         int hexLen   = StringLen(hex);
         
         for(int b=0; b<512; b++) {
            if(b*2 + 2 <= hexLen) {
               m_field[h][b] = (double)StringToInteger(StringSubstr(hex, b*2, 2)) / 99.0;
            } else m_field[h][b] = 0;
         }
         m_field_meta[h][0] = p_min;
         m_field_meta[h][1] = p_max;
         m_field_meta[h][2] = (double)iTime(_Symbol, _Period, h);
         m_field_meta[h][3] = iClose(_Symbol, _Period, h);
      }
      
      int bars_to_render = MathMin(histSize-1, 800);
      for(int h=0; h<bars_to_render; h++) {
         datetime t1 = (datetime)m_field_meta[h][2];
         datetime t2 = (datetime)m_field_meta[h+1][2];
         
         int x1, py1, x2, py2;
         ChartTimePriceToXY(0, 0, t1, iClose(_Symbol, _Period, h), x1, py1);
         ChartTimePriceToXY(0, 0, t2, iClose(_Symbol, _Period, h+1), x2, py2);
         
         int startX = x2; int endX = x1;
         if(startX > endX) { int tmp=startX; startX=endX; endX=tmp; }
         
         int steps = (int)MathMax(1, MathAbs(endX - startX)); 
         for(int s=0; s<steps; s++) { // [v71.9] s<steps remove o overlap aditivo causador das listras verticais
            double lerp_x = (steps > 0) ? (double)s / (double)steps : 0.0;
            int x = (int)(startX + lerp_x * (endX - startX));
            if(x < 0 || x >= m_chart_w) continue;
            
            datetime t_curr = (datetime)(m_field_meta[h+1][2] + lerp_x * (m_field_meta[h][2] - m_field_meta[h+1][2]));
            
            double p_min_lerp = (m_field_meta[h+1][0] + lerp_x * (m_field_meta[h][0] - m_field_meta[h+1][0]));
            double p_max_lerp = (m_field_meta[h+1][1] + lerp_x * (m_field_meta[h][1] - m_field_meta[h+1][1]));

            int py_top_curr, py_bot_curr, dummyX;
            ChartTimePriceToXY(0, 0, t_curr, p_max_lerp, dummyX, py_top_curr);
            ChartTimePriceToXY(0, 0, t_curr, p_min_lerp, dummyX, py_bot_curr);

            int screen_y_start = MathMin(py_top_curr, py_bot_curr);
            int screen_y_end   = MathMax(py_top_curr, py_bot_curr);
            double height = (double)MathMax(1, screen_y_end - screen_y_start);
            
            double exact_age = (h + 1) - lerp_x; // Idade fracional exata para decaimento macio
            
            for(int y = screen_y_start; y <= screen_y_end; y++) { 
               if(y < 0 || y >= m_chart_h) continue;
               
               double bin_exact = (1.0 - (double)(y - screen_y_start) / height) * 511.0;
               int b_idx = (int)MathFloor(bin_exact);
               int b_next = MathMin(511, b_idx + 1);
               double b_frac = bin_exact - b_idx;
               
               double d2 = m_field[h][b_idx] + b_frac * (m_field[h][b_next] - m_field[h][b_idx]);
               double d1 = m_field[h+1][b_idx] + b_frac * (m_field[h+1][b_next] - m_field[h+1][b_idx]);
               
               double val = d1 + lerp_x * (d2 - d1); // Bilinear 2D Interpolation Puro
               
               if(MathAbs(val - 0.505) > 0.02) { 
                  uint qClr = GetLushColor(val, exact_age);
                  BlendSmoothPixel(m_canvas, x, y, qClr);
               }
            }
         }
      }
   }
   
   // 3. TACTICAL HUD (ASI Ph.D. Telemetry)
   DrawTacticalHUD(parts);
   
   m_canvas.Update();
   ChartRedraw();
}

void DrawTacticalHUD(string &parts[])
{
   if(ArraySize(parts) < 30) return;
   
   // Fundo translúcido do painel
   int x = 20, y = 20, w = 320, h = 140;
   m_canvas.FillRectangle(x, y, x+w, y+h, ColorToARGB(clrBlack, 180));
   m_canvas.Rectangle(x, y, x+w, y+h, ColorToARGB(clrDimGray, 200));
   
   // Título
   m_canvas.FontSet("Consolas", 14, FW_BOLD);
   m_canvas.TextOut(x + 15, y + 10, "NEXUS ASI-5 :: QUANTUM TELEMETRY", ColorToARGB(clrWhite, 255));
   m_canvas.LineHorizontal(x + 10, x + w - 10, y + 35, ColorToARGB(clrDimGray, 150));
   
   // 1. Core Status
   string core_status = parts[2];
   m_canvas.FontSet("Consolas", 12, FW_NORMAL);
   m_canvas.TextOut(x + 15, y + 45, "SYS CORE : ", ColorToARGB(clrLightGray, 255));
   m_canvas.TextOut(x + 100, y + 45, core_status, ColorToARGB(clrCyan, 255));
   
   // 2. Regime Status (SMC Evolved)
   string regime_str = "NEUTRAL";
   uint regime_clr = ColorToARGB(clrDarkGray, 255);
   string historyRegimes = parts[4]; 
   string hReg[]; StringSplit(historyRegimes, ',', hReg);
   if(ArraySize(hReg) > 0) {
      string sub[]; StringSplit(hReg[ArraySize(hReg)-1], '|', sub);
      if(ArraySize(sub) > 0) {
         int r = (int)StringToInteger(sub[0]);
         if(r == 1) { regime_str = "BULLISH (ABSORPTION)"; regime_clr = ColorToARGB(clrCyan, 255); }
         else if(r == 2) { regime_str = "BEARISH (DISTRIBUTION)"; regime_clr = ColorToARGB(clrMagenta, 255); }
      }
   }
   m_canvas.TextOut(x + 15, y + 70, "TOPOLOGY : ", ColorToARGB(clrLightGray, 255));
   m_canvas.TextOut(x + 100, y + 70, regime_str, regime_clr);
   
   // 3. RHT Status (Thermodynamics)
   string rht_status = parts[21];
   uint rht_clr = ColorToARGB(clrYellow, 255); // Default warning/heating
   if(StringFind(rht_status, "BULL") >= 0) rht_clr = ColorToARGB(clrCyan, 255);
   if(StringFind(rht_status, "BEAR") >= 0) rht_clr = ColorToARGB(clrMagenta, 255);
   if(StringFind(rht_status, "LAMINAR") >= 0) rht_clr = ColorToARGB(clrDimGray, 255);
   
   m_canvas.TextOut(x + 15, y + 95, "RHT DIFF : ", ColorToARGB(clrLightGray, 255));
   m_canvas.TextOut(x + 100, y + 95, rht_status, rht_clr);
   
   // 4. QDD Fidelity
   string qdd_fid = (ArraySize(parts) > 31) ? parts[31] : "0.00";
   m_canvas.TextOut(x + 15, y + 120, "FIDELITY : ", ColorToARGB(clrLightGray, 255));
   m_canvas.TextOut(x + 100, y + 120, qdd_fid + " SIGMA", ColorToARGB(clrWhite, 255));
}

uint GetLushColor(double val, double age) 
{ 
    double delta = (val - 0.505) * 2.0;
    if(MathAbs(delta) < 0.02) return 0x00000000;
    
    uint r=0, g=0, b=0, a=0;
    double intensity = MathPow(MathAbs(delta), 0.6); 
    double age_decay = MathPow(0.985, age); // [v37.9] Decaimento muito mais longo (0.97 -> 0.985)
    
    // [v37.9] Multiplicador de alpha elevado para 255 para brilho total no núcleo
    a = (uint)MathMin(255, 255 * intensity * age_decay); 
    
    if(delta > 0) { // BUY / ABSORPTION (CYAN NEON)
       r = 0;
       g = (uint)(180 + 75 * intensity);
       b = 255; 
    } else { // SELL / DISTRIBUTION (MAGENTA NEON)
       r = 255;
       g = 0;
       b = (uint)(180 + 75 * intensity);
    }
    
    // Retorno ARGB canônico absoluto (A << 24 | R << 16 | G << 8 | B)
    return (a << 24) | (r << 16) | (g << 8) | b;
}

color RGB(uchar r, uchar g, uchar b) { return (color)((b << 16) | (g << 8) | r); }
