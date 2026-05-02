#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>

namespace py = pybind11;

class QHOEngine {
public:
    QHOEngine() {} 

    py::dict scan_quantum_triggers(
        py::array_t<double> open_arr,
        py::array_t<double> high_arr,
        py::array_t<double> low_arr,
        py::array_t<double> close_arr, 
        py::array_t<double> ema_arr, 
        py::array_t<int> regime_arr,
        py::array_t<double> atr_arr
    ) {
        py::buffer_info buf_o = open_arr.request();
        py::buffer_info buf_h = high_arr.request();
        py::buffer_info buf_l = low_arr.request();
        py::buffer_info buf_c = close_arr.request();
        py::buffer_info buf_e = ema_arr.request();
        py::buffer_info buf_r = regime_arr.request();
        py::buffer_info buf_atr = atr_arr.request();

        int N = buf_c.shape[0];
        
        double *open = static_cast<double *>(buf_o.ptr);
        double *high = static_cast<double *>(buf_h.ptr);
        double *low = static_cast<double *>(buf_l.ptr);
        double *close = static_cast<double *>(buf_c.ptr);
        double *ema = static_cast<double *>(buf_e.ptr);
        int *regime = static_cast<int *>(buf_r.ptr);
        double *atr = static_cast<double *>(buf_atr.ptr);

        std::vector<int> signals(N, 0);
        int cooldown = 0;
        
        int current_well_regime = 0;
        int regime_age = 0; // Rastreador da idade do regime

        for (int i = 5; i < N; ++i) {
            if (cooldown > 0) cooldown--;
            
            int r = regime[i];
            
            // Atualiza a idade do regime
            if (r != current_well_regime) {
                current_well_regime = r;
                regime_age = 0;
            } else {
                regime_age++;
            }

            if (r == 0) continue;

            double lower_anomaly = ema[i] - (1.2 * atr[i]);
            double upper_anomaly = ema[i] + (1.2 * atr[i]);
            
            double lower_value_zone = ema[i] - (0.4 * atr[i]);
            double upper_value_zone = ema[i] + (0.4 * atr[i]);

            double body = std::abs(close[i] - open[i]);
            bool is_green = close[i] > open[i];
            bool is_red = close[i] < open[i];

            if (r == 1) { // BULL REGIME
                bool touched_anomaly = (low[i-3] < lower_anomaly || low[i-2] < lower_anomaly || low[i-1] < lower_anomaly || low[i] < lower_anomaly);
                bool tunneling_ignition = is_green && (close[i] > lower_value_zone) && (body > atr[i] * 0.5);

                bool breakout_ignition = is_green && (body > atr[i] * 1.0) && (close[i] > upper_anomaly) && (open[i] > ema[i]) && (regime_age < 15);

                if ((touched_anomaly && tunneling_ignition) || breakout_ignition) {
                    if (cooldown == 0) {
                        signals[i] = 1; 
                        cooldown = 20; // Aumento do cooldown para silenciar lateralizações
                    }
                }
            } 
            else if (r == 2) { // BEAR REGIME
                bool touched_anomaly = (high[i-3] > upper_anomaly || high[i-2] > upper_anomaly || high[i-1] > upper_anomaly || high[i] > upper_anomaly);
                bool tunneling_ignition = is_red && (close[i] < upper_value_zone) && (body > atr[i] * 0.5);

                bool breakout_ignition = is_red && (body > atr[i] * 1.0) && (close[i] < lower_anomaly) && (open[i] < ema[i]) && (regime_age < 15);

                if ((touched_anomaly && tunneling_ignition) || breakout_ignition) {
                    if (cooldown == 0) {
                        signals[i] = 2; 
                        cooldown = 20; 
                    }
                }
            }
        }

        py::dict result;
        result["signals"] = py::array_t<int>(signals.size(), signals.data());
        return result;
    }
};

PYBIND11_MODULE(qho_engine, m) {
    m.doc() = "Quantum Keltner Tunneling Engine";
    py::class_<QHOEngine>(m, "QHOEngine")
        .def(py::init<>())
        .def("scan_quantum_triggers", &QHOEngine::scan_quantum_triggers);
}
