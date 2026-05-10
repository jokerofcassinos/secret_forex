#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <numeric>

namespace py = pybind11;

/**
 * 🌌 GAD ENGINE v1.0 - GAUGE ARBITRAGE DETECTOR
 * Implementa Teoria de Gauge (Ilinski) para precificação de arbitragem.
 * A conexão A = log(p_{i,t} / p_{i,t-1})
 * Curvatura F = dA + A \wedge A
 * Holonomia mede a arbitragem no fibrado principal (loop em múltiplos ativos).
 */
class GADEngine {
private:
    int num_assets;
    int time_steps;
    std::vector<std::vector<double>> prices; // shape: (num_assets, time_steps)
    std::vector<double> curvature_history;
    std::vector<double> holonomy_history;

public:
    GADEngine(int n_assets, int t_steps) : num_assets(n_assets), time_steps(t_steps) {
        if (num_assets < 2 || time_steps <= 0) {
            prices.resize(2, std::vector<double>(1, 1.0)); // min 2 assets
            num_assets = 2;
        } else {
            prices.resize(num_assets, std::vector<double>(time_steps, 0.0));
        }
    }

    void load_multi_asset_data(py::array_t<double> input_data) {
        py::buffer_info buf = input_data.request();
        if (buf.ndim != 2 || buf.shape[0] != num_assets || buf.shape[1] != time_steps) {
            throw std::runtime_error("GAD: Dimensões da matriz incompatíveis.");
        }

        double *ptr = static_cast<double *>(buf.ptr);
        for (int i = 0; i < num_assets; ++i) {
            for (int t = 0; t < time_steps; ++t) {
                prices[i][t] = ptr[i * time_steps + t];
            }
        }
    }

    void compute_gauge_curvature() {
        curvature_history.assign(time_steps, 0.0);
        holonomy_history.assign(time_steps, 0.0);

        // Matriz de log-returns (conexões de gauge)
        std::vector<std::vector<double>> A(num_assets, std::vector<double>(time_steps, 0.0));

        for (int i = 0; i < num_assets; ++i) {
            for (int t = 1; t < time_steps; ++t) {
                if (prices[i][t-1] > 0 && prices[i][t] > 0) {
                    A[i][t] = std::log(prices[i][t] / prices[i][t-1]);
                }
            }
        }

        // Calcula curvatura de gauge local e holonomia (integral de contorno).
        // Em 1D temporal multi-asset, o "loop" é a diferença entre as dinâmicas 
        // dos ativos ao longo do tempo (triangular arbitrage spread pseudo-loop).
        for (int t = 1; t < time_steps; ++t) {
            double local_curvature = 0.0;
            double loop_integral = 0.0;
            
            // Aproximação do contorno: A1 - A2 + A3... (simples loop espacial em t)
            for (int i = 0; i < num_assets; ++i) {
                // F = dA + [A, A]. Para abelian (U(1)), [A, A] = 0.
                // Usamos a derivada temporal dA/dt
                double dA_dt = A[i][t] - A[i][t-1];
                local_curvature += std::abs(dA_dt);
                
                // Holonomia em malha temporal-espacial simples:
                if (i < num_assets - 1) {
                    loop_integral += (A[i][t] - A[i+1][t]);
                } else {
                    loop_integral += (A[i][t] - A[0][t]);
                }
            }
            
            curvature_history[t] = local_curvature;
            holonomy_history[t] = loop_integral;
        }

        if (time_steps > 1) {
            curvature_history[0] = curvature_history[1];
            holonomy_history[0] = holonomy_history[1];
        }
    }

    py::dict get_results() {
        py::dict d;
        d["gauge_curvature"] = curvature_history;
        d["holonomy"] = holonomy_history;
        return d;
    }
};

PYBIND11_MODULE(gad_engine, m) {
    m.doc() = "GAD Engine v1.0 - Gauge Arbitrage Detector";

    py::class_<GADEngine>(m, "GADEngine")
        .def(py::init<int, int>())
        .def("load_multi_asset_data", &GADEngine::load_multi_asset_data)
        .def("compute_gauge_curvature", &GADEngine::compute_gauge_curvature)
        .def("get_results", &GADEngine::get_results);
}
