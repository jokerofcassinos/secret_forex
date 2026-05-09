#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <complex>
#include <numeric>

namespace py = pybind11;

/**
 * 🌌 KSI ENGINE v1.0 - KURAMOTO SYNCHRONIZATION INDEX
 * Aplica o Modelo de Kuramoto não-linear para calcular o grau de coerência de fase
 * entre múltiplas dimensões (timeframes/ciclos de frequência) do mercado.
 */
class KSIEngine {
private:
    int num_oscillators;
    int time_steps;
    std::vector<std::vector<double>> oscillators_data;
    std::vector<double> order_parameter_history;
    std::vector<double> global_phase_history;

public:
    KSIEngine(int num_osc, int t_steps) : num_oscillators(num_osc), time_steps(t_steps) {
        if (num_oscillators <= 0 || time_steps <= 0) {
            oscillators_data.resize(1, std::vector<double>(1, 0.0));
        } else {
            oscillators_data.resize(num_oscillators, std::vector<double>(time_steps, 0.0));
        }
    }

    // Carrega dados. Formato esperado: (num_oscillators, time_steps)
    void load_oscillator_data(py::array_t<double> input_data) {
        py::buffer_info buf = input_data.request();
        if (buf.ndim != 2 || buf.shape[0] != num_oscillators || buf.shape[1] != time_steps) {
            throw std::runtime_error("KSI: Dimensões da matriz de osciladores incompatíveis.");
        }

        double *ptr = static_cast<double *>(buf.ptr);
        for (int i = 0; i < num_oscillators; ++i) {
            for (int t = 0; t < time_steps; ++t) {
                oscillators_data[i][t] = ptr[i * time_steps + t];
            }
        }
    }

    /**
     * Calcula o Parâmetro de Ordem de Kuramoto (R) ao longo do tempo.
     * R varia de 0 (caos total) a 1 (sincronização perfeita de fase).
     */
    void compute_synchronization() {
        order_parameter_history.assign(time_steps, 0.0);
        global_phase_history.assign(time_steps, 0.0);

        // Para cada tempo t, extrai a "fase" aproximada de cada oscilador.
        // Como aproximação rápida do Transformado de Hilbert analítico para série discreta,
        // usamos a variação local (derivada) e o offset médio para estimar ângulo.
        for (int t = 1; t < time_steps; ++t) {
            std::complex<double> sum_phases(0.0, 0.0);

            for (int i = 0; i < num_oscillators; ++i) {
                // Estimativa de fase: arctan(dx/dt, x - mean_x)
                double current_val = oscillators_data[i][t];
                double prev_val = oscillators_data[i][t - 1];
                double dx_dt = current_val - prev_val;

                // Estimação média móvel local p/ baseline do oscilador
                int window = 14;
                int start_idx = std::max(0, t - window);
                double sum = 0;
                for (int w = start_idx; w <= t; ++w) {
                    sum += oscillators_data[i][w];
                }
                double mean_val = sum / (t - start_idx + 1);
                
                double centered_val = current_val - mean_val;

                // Fase em radianos [-pi, pi]
                double phase = std::atan2(dx_dt, centered_val);
                
                sum_phases += std::polar(1.0, phase);
            }

            std::complex<double> z = sum_phases / static_cast<double>(num_oscillators);
            
            order_parameter_history[t] = std::abs(z);
            global_phase_history[t] = std::arg(z);
        }
        // t=0 herda de t=1
        if (time_steps > 1) {
            order_parameter_history[0] = order_parameter_history[1];
            global_phase_history[0] = global_phase_history[1];
        }
    }

    py::dict get_results() {
        py::dict d;
        d["synchronization_index"] = order_parameter_history;
        d["global_phase"] = global_phase_history;
        return d;
    }
    
    double get_current_ksi() {
        if(time_steps > 0) return order_parameter_history[time_steps - 1];
        return 0.0;
    }
};

PYBIND11_MODULE(ksi_engine, m) {
    m.doc() = "KSI Engine v1.0 - Kuramoto Synchronization Index para Variedades Riemanniana";

    py::class_<KSIEngine>(m, "KSIEngine")
        .def(py::init<int, int>())
        .def("load_oscillator_data", &KSIEngine::load_oscillator_data)
        .def("compute_synchronization", &KSIEngine::compute_synchronization)
        .def("get_results", &KSIEngine::get_results)
        .def("get_current_ksi", &KSIEngine::get_current_ksi);
}
