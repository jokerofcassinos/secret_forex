//+------------------------------------------------------------------+
//|                                              Nexus_Observer.mq5 |
//|                                  Copyright 2026, NEXUS AGI CEO |
//+------------------------------------------------------------------+
#property copyright "NEXUS AGI CEO"
#property version   "305.00"
#property strict

#include <Canvas\Canvas.mqh>

// Instância Master do Renderizador (v52.0 - Riemann Fluid Surface)
CCanvas m_canvas;
string m_canvas_name = "NEXUS_QUANTUM_CANVAS";

// Buffer de Campo Contínuo [Snapshots][Bins]
double m_field[42][512]; 
double m_field_meta[42][4]; // [p_center][h_range][Time][Price_Actual]

// Memória de Estado
string last_payload = "";
int m_chart_w = 0;
int m_chart_h = 0;

// --- PROTÓTIPOS ---
void ParseAndDraw(string data);
uint GetInfernoColor(double density);

//+------------------------------------------------------------------+
int OnInit() { 
    EventSetTimer(1); 
    ChartSetInteger(0, CHART_SHOW_TRADE_LEVELS, false); 
    ObjectsDeleteAll(0, "NEXUS_"); 
    
    m_chart_w = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
    m_chart_h = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS);
    
    if(!m_canvas.CreateBitmapLabel(m_canvas_name, 0, 0, m_chart_w, m_chart_h, COLOR_FORMAT_ARGB_NORMALIZE)) return(INIT_FAILED);
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
   
   res = WebRequest("GET", url, cookie, NULL, 500, post, 0, result, headers);
   if(res == 200) {
      string response = CharArrayToString(result);
      StringTrimRight(response);
      ParseAndDraw(response);
      last_payload = response;
   }
}

void ParseAndDraw(string data)
{
   if(ObjectFind(0, m_canvas_name) < 0) {
      m_chart_w = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
      m_chart_h = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS);
      m_canvas.CreateBitmapLabel(m_canvas_name, 0, 0, m_chart_w, m_chart_h, COLOR_FORMAT_ARGB_NORMALIZE);
   }

   int curW = (int)ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
   int curH = (int)ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS);
   if(curW != m_chart_w || curH != m_chart_h) {
      m_chart_w = curW; m_chart_h = curH;
      m_canvas.Resize(m_chart_w, m_chart_h);
   }

   m_canvas.Erase(0x00000000); 
   
   string parts[];
   StringSplit(data, ';', parts);
   if(ArraySize(parts) < 11) return;

   // 1. CAIXAS DE REGIME
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
         color zClr = (r == 1) ? RGB(38, 166, 154) : (r == 2 ? RGB(239, 83, 80) : RGB(255, 202, 40));
         if(ObjectCreate(0, bName, OBJ_RECTANGLE, 0, iTime(_Symbol, _Period, start), maxH, iTime(_Symbol, _Period, end), minL)) {
             ObjectSetInteger(0, bName, OBJPROP_COLOR, zClr);
             ObjectSetInteger(0, bName, OBJPROP_FILL, false);
             ObjectSetInteger(0, bName, OBJPROP_BACK, true);
         }
         boxIdx++; i = end;
      }
   }

   // 2. RIEMANN FLUID SURFACE (v52.0)
   string cloud_str = parts[10];
   if(cloud_str != "") {
      string cloudHistory[]; StringSplit(cloud_str, '^', cloudHistory);
      int histSize = ArraySize(cloudHistory);
      
      // Decode Snapshots
      for(int h=0; h<histSize && h<42; h++) {
         string snapParts[]; StringSplit(cloudHistory[h], '|', snapParts);
         if(ArraySize(snapParts) < 3) continue;
         
         double p_center = StringToDouble(snapParts[0]);
         double h_range  = StringToDouble(snapParts[1]);
         string hex      = snapParts[2];
         int hexLen      = StringLen(hex);
         
         for(int b=0; b<512; b++) {
            if(b*2 + 2 <= hexLen) {
               m_field[h][b] = (double)StringToInteger(StringSubstr(hex, b*2, 2)) / 99.0;
            } else m_field[h][b] = 0;
         }
         m_field_meta[h][0] = p_center;
         m_field_meta[h][1] = h_range;
         m_field_meta[h][2] = (double)iTime(_Symbol, _Period, h);
         m_field_meta[h][3] = iClose(_Symbol, _Period, h);
      }
      
      // Renderização Riemann (Superfluidez Horizontal + Vertical)
      int bars_to_render = MathMin(histSize-1, 40);
      for(int h=0; h<bars_to_render; h++) {
         datetime t1 = (datetime)m_field_meta[h][2];
         datetime t2 = (datetime)m_field_meta[h+1][2];
         
         int x1, y_dummy1, x2, y_dummy2;
         // Pre-calculate X coordinates for the candles
         ChartTimePriceToXY(0, 0, t1, m_field_meta[h][3], x1, y_dummy1);
         ChartTimePriceToXY(0, 0, t2, m_field_meta[h+1][3], x2, y_dummy2);
         
         // Pre-calculate Y extent for both candles to interpolate between them
         int y_top1, y_bot1, y_top2, y_bot2;
         ChartTimePriceToXY(0, 0, t1, m_field_meta[h][0] + m_field_meta[h][1], x1, y_top1);
         ChartTimePriceToXY(0, 0, t1, m_field_meta[h][0] - m_field_meta[h][1], x1, y_bot1);
         ChartTimePriceToXY(0, 0, t2, m_field_meta[h+1][0] + m_field_meta[h+1][1], x2, y_top2);
         ChartTimePriceToXY(0, 0, t2, m_field_meta[h+1][0] - m_field_meta[h+1][1], x2, y_bot2);
         
         int startX = x2; int endX = x1;
         if(startX > endX) { int tmp=startX; startX=endX; endX=tmp; }
         
         // Loop over every pixel column (X) to ensure 0 gaps
         for(int x = startX; x <= endX; x++) {
            if(x < 0 || x >= m_chart_w) continue;
            
            double lerp_t = (endX - startX > 0) ? (double)(x - startX) / (double)(endX - startX) : 1.0;
            
            // Interpolate Y extent
            int py_top = (int)(y_top2 + lerp_t * (y_top1 - y_top2));
            int py_bot = (int)(y_bot2 + lerp_t * (y_bot1 - y_bot2));
            
            int py_start = MathMin(py_top, py_bot);
            int py_end   = MathMax(py_top, py_bot);
            
            // Fill vertical column for this X
            for(int y = py_start; y <= py_end; y++) {
               if(y < 0 || y >= m_chart_h) continue;
               
               double bin_lerp = (double)(y - py_start) / (double)(py_end - py_start + 1e-9);
               int b_idx = (int)((1.0 - bin_lerp) * 511.0);
               if(b_idx < 0) b_idx = 0; if(b_idx > 511) b_idx = 511;
               
               // Bilinear Density
               double density = m_field[h+1][b_idx] + lerp_t * (m_field[h][b_idx] - m_field[h+1][b_idx]);
               
               if(density > 0.015) {
                  uint qClr = GetInfernoColor(density * MathPow(0.98, h));
                  m_canvas.PixelSet(x, y, qClr);
               }
            }
         }
      }
   }
   
   m_canvas.Update();
   ChartRedraw();
}

uint GetInfernoColor(double d) 
{ 
    if(d <= 0.01) return 0x00000000;
    uchar r=0, g=0, b=0, a=0;
    
    // [V53.0] BOOSTED NEON GLOW
    a = (uchar)MathMin(255, 260 * MathPow(d, 0.85));
    
    // Inferno Gradient (Vivid Edition)
    if(d < 0.2) {
       r = (uchar)(80 * (d/0.2)); g = 15; b = (uchar)(180 * (d/0.2));
    } else if(d < 0.4) {
       r = (uchar)(80 + 110 * ((d-0.2)/0.2)); g = (uchar)(15 + 70 * ((d-0.2)/0.2)); b = (uchar)(180 + 30 * ((d-0.2)/0.2));
    } else if(d < 0.6) {
       r = (uchar)(190 + 65 * ((d-0.4)/0.2)); g = (uchar)(85 + 90 * ((d-0.4)/0.2)); b = (uchar)(210 - 70 * ((d-0.4)/0.2));
    } else if(d < 0.8) {
       r = 255; g = (uchar)(175 + 80 * ((d-0.6)/0.2)); b = (uchar)(140 - 140 * ((d-0.6)/0.2));
    } else {
       r = 255; g = 255; b = (uchar)(50 + 205 * ((d-0.8)/0.2));
    }
    return ((uint)a << 24) | ((uint)r << 16) | ((uint)g << 8) | (uint)b;
}

color RGB(uchar r, uchar g, uchar b) { return (color)((b << 16) | (g << 8) | r); }
