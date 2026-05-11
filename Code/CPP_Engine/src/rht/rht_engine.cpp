#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>
#include <iostream>

namespace py = pybind11;

/**
 * 🌌 RHT ENGINE v3.0 - THERMODYNAMIC RESONANCE CORE (ASI Ph.D.)
 * Implementa a Equação Discreta de Calor, Entropia de Shannon Generalizada e 
 * Difusão Termodinâmica Fractal. Sem hardcodes, pura física.
 */
class RHTEngine {
private:
    int num_timeframes;
    int time_steps;
    std::vector<std::vector<double>> tensor_matrix;
    
    // Matriz de Campo Térmico [time_steps]
    std::vector<double> heat_flux;
    std::vector<double> entropy_field;
    std::vector<double> ignition_state;

    // Memória de inércia macro
    double global_thermo_inertia = 0.0;

public:
    RHTEngine(int num_tf, int t_steps) : num_timeframes(num_tf), time_steps(t_steps) {
        if (num_timeframes <= 0 || time_steps <= 0) {
            tensor_matrix.resize(1, std::vector<double>(1, 0.0));
        } else {
            tensor_matrix.resize(num_timeframes, std::vector<double>(time_steps, 0.0));
        }
    }

    void load_tensor_data(py::array_t<double> input_data) {
        py::buffer_info buf = input_data.request();
        if (buf.ndim != 2 || buf.shape[0] != num_timeframes || buf.shape[1] != time_steps) {
            throw std::runtime_error("RHT_ASI: Topological dimensions mismatch in Tensor Matrix.");
        }

        double *ptr = static_cast<double *>(buf.ptr);
        #pragma omp parallel for collapse(2)
        for (int i = 0; i < num_timeframes; ++i) {
            for (int t = 0; t < time_steps; ++t) {
                tensor_matrix[i][t] = ptr[i * time_steps + t];
            }
        }
    }

    /**
     * Motor de Difusão e Entropia.
     * Calcula o fluxo de calor em toda a dimensão temporal.
     */
    void compute_thermodynamics(double alpha = 0.15) {
        heat_flux.assign(time_steps, 0.0);
        entropy_field.assign(time_steps, 1.0);
        ignition_state.assign(time_steps, 0.0);

        double accumulated_heat = 0.0;

        for (int t = 0; t < time_steps; ++t) {
            double p_buy = 0.0;
            double p_sell = 0.0;
            double sum_abs = 0.0;
            double center_of_mass = 0.0;

            // 1. Cálculo da Massa Direcional e Entropia Base
            for (int i = 0; i < num_timeframes; ++i) {
                double v = tensor_matrix[i][t];
                sum_abs += std::abs(v);
                center_of_mass += v * std::pow(1.2, i); // Gravidade aumenta em TFs maiores
                
                if (v > 0) p_buy += std::abs(v);
                else p_sell += std::abs(v);
            }

            // 2. Entropia de Shannon Generalizada (Grau de Conflito)
            double entropy = 1.0;
            if (sum_abs > 1e-7) {
                double prob_b = p_buy / sum_abs;
                double prob_s = p_sell / sum_abs;
                entropy = 0.0;
                if (prob_b > 0) entropy -= prob_b * std::log2(prob_b);
                if (prob_s > 0) entropy -= prob_s * std::log2(prob_s);
                // Normaliza para [0, 1] no sistema binário
                entropy = std::min(1.0, std::max(0.0, entropy));
            }

            // 3. Equação de Difusão Térmica: Q_dot = Coerência * Densidade de Energia * (1 - Entropia)
            double instant_heat = 0.0;
            if (sum_abs > 1e-7) {
                double coherence = std::abs(center_of_mass) / (sum_abs * std::pow(1.2, num_timeframes-1) + 1e-9);
                double direction = (center_of_mass >= 0) ? 1.0 : -1.0;
                
                // O Calor aumenta exponencialmente com a Coerência Fractal
                double energy = sum_abs / num_timeframes;
                instant_heat = direction * std::pow(coherence, 2.0) * energy * (1.0 - entropy);
            }

            // 4. Inércia Térmica (Lennard-Jones style smoothing)
            accumulated_heat = (accumulated_heat * (1.0 - alpha)) + (instant_heat * alpha);
            
            // 5. Estado de Ignição Absoluta (Condensado de Bose-Einstein)
            // Se o calor supera limiares críticos com baixa entropia, ocorre o "Flash Point"
            double flash = 0.0;
            if (entropy < 0.35 && std::abs(accumulated_heat) > 0.8) {
                flash = (accumulated_heat > 0) ? 1.0 : -1.0;
            }

            heat_flux[t] = accumulated_heat;
            entropy_field[t] = entropy;
            ignition_state[t] = flash;
        }
    }

    py::dict get_thermodynamics() {
        py::dict d;
        d["heat_flux"] = heat_flux;
        d["entropy"] = entropy_field;
        d["ignition"] = ignition_state;
        return d;
    }
};

PYBIND11_MODULE(rht_engine, m) {
    m.doc() = "RHT Engine v3.0 - Quantum Thermodynamic Fluid Diffusion (ASI Ph.D)";
    py::class_<RHTEngine>(m, "RHTEngine")
        .def(py::init<int, int>())
        .def("load_tensor_data", &RHTEngine::load_tensor_data)
        .def("compute_thermodynamics", &RHTEngine::compute_thermodynamics, py::arg("alpha") = 0.15)
        .def("get_thermodynamics", &RHTEngine::get_thermodynamics);
}
