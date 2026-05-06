#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <complex>
#include <iostream>
#include <stdexcept>
#include <numeric>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

struct QDDResult {
    int regime_state;     
    double energy_level;  
    double coherence;     
};

class QDDEngine {
private:
    int N; 
    double hbar;
    double gamma_dissipation;

    // Renormalization Flow (Haar Wavelet level reduction)
    std::vector<double> renormalization_flow(const std::vector<double>& input_series, int uv_cutoff_levels) {
        std::vector<double> current = input_series;
        for (int level = 0; level < uv_cutoff_levels; ++level) {
            std::vector<double> next_level;
            for (size_t i = 0; i < current.size() - 1; i += 2) {
                // Low-pass filter (approximation)
                next_level.push_back((current[i] + current[i+1]) / std::sqrt(2.0));
            }
            if (next_level.empty()) break;
            current = next_level;
        }
        return current;
    }

    double compute_eigen_energy(const std::vector<double>& macro_state) {
        if (macro_state.size() < 2) return 0.0;
        
        double kinetic_energy = 0.0;
        for (size_t i = 1; i < macro_state.size(); ++i) {
            double dp = macro_state[i] - macro_state[i-1];
            kinetic_energy += 0.5 * (dp * dp);
        }
        return kinetic_energy / macro_state.size();
    }
    
    // Normaliza um estado quântico (vetor) para que a norma L2 seja 1
    void normalize_state(std::vector<double>& state) {
        double norm = 0.0;
        for(double v : state) norm += v * v;
        norm = std::sqrt(norm);
        if (norm > 1e-9) {
            for(double& v : state) v /= norm;
        }
    }

public:
    QDDEngine(int dim, double planck_const = 1.0, double gamma = 0.1) 
        : N(dim), hbar(planck_const), gamma_dissipation(gamma) {}

    py::dict quantize_regime(py::array_t<double> input_data, int uv_cutoff, double energy_threshold) {
        py::buffer_info buf = input_data.request();
        if (buf.ndim != 1) {
            throw std::runtime_error("Entrada deve ser um array 1D.");
        }

        double *ptr = static_cast<double *>(buf.ptr);
        std::vector<double> raw_series(ptr, ptr + buf.shape[0]);

        std::vector<double> macro_state = renormalization_flow(raw_series, uv_cutoff);

        double raw_energy = compute_eigen_energy(macro_state);
        double decohered_energy = raw_energy * std::exp(-gamma_dissipation);

        int state = 0; 
        if (decohered_energy > energy_threshold * 2.5) {
            state = 2; 
        } else if (decohered_energy > energy_threshold) {
            state = 1; 
        }

        py::dict result;
        result["regime_state"] = state;
        result["energy_level"] = decohered_energy;
        result["coherence"] = std::exp(-gamma_dissipation); 
        result["macro_state_size"] = macro_state.size();

        return result;
    }

    /**
     * @brief Tensor Network Entanglement Fidelity
     * Calcula o grau de emaranhamento quântico (Fidelidade) entre múltiplas dimensões (ex: H2 e M5).
     * O Grupo de Renormalização (RG) alinha as escalas de tempo.
     * Retorna a Fidelidade F = |<psi_macro | psi_micro>|^2 (0.0 a 1.0)
     */
    double calculate_entanglement_fidelity(py::array_t<double> macro_data, py::array_t<double> micro_data, int macro_cutoff, int micro_cutoff) {
        py::gil_scoped_release release; // Libera GIL para paralelismo livre
        
        py::buffer_info buf_macro = macro_data.request();
        py::buffer_info buf_micro = micro_data.request();

        double *ptr_macro = static_cast<double *>(buf_macro.ptr);
        double *ptr_micro = static_cast<double *>(buf_micro.ptr);

        std::vector<double> macro_series(ptr_macro, ptr_macro + buf_macro.shape[0]);
        std::vector<double> micro_series(ptr_micro, ptr_micro + buf_micro.shape[0]);

        // RG Flow para trazer ambos os estados para uma base comparável
        std::vector<double> psi_macro = renormalization_flow(macro_series, macro_cutoff);
        std::vector<double> psi_micro = renormalization_flow(micro_series, micro_cutoff);

        // Ajuste de dimensionalidade (Truncamento simétrico)
        size_t min_size = std::min(psi_macro.size(), psi_micro.size());
        if (min_size < 2) return 0.0; // Decoerência total

        std::vector<double> state_macro(psi_macro.end() - min_size, psi_macro.end());
        std::vector<double> state_micro(psi_micro.end() - min_size, psi_micro.end());

        // Transformar em Vetores de Momentum (Diferença)
        std::vector<double> p_macro(min_size - 1);
        std::vector<double> p_micro(min_size - 1);
        
        for (size_t i = 1; i < min_size; ++i) {
            p_macro[i-1] = state_macro[i] - state_macro[i-1];
            p_micro[i-1] = state_micro[i] - state_micro[i-1];
        }

        normalize_state(p_macro);
        normalize_state(p_micro);

        // Produto Interno das funções de onda de Momentum <psi_macro | psi_micro>
        double inner_product = 0.0;
        for (size_t i = 0; i < p_macro.size(); ++i) {
            inner_product += p_macro[i] * p_micro[i];
        }

        // Fidelidade = Produto Interno ao Quadrado
        double fidelity = inner_product * inner_product;
        
        // Se a direção do fluxo for oposta (inner_product < 0), significa Efeito Estilingue (Pullback anti-alinhado).
        // Se for positivo, estão emaranhados direcionalmente.
        // Retornamos um Fidelity Signed (-1 a 1) para o N-Core saber se estão em oposição ou união.
        double signed_fidelity = (inner_product < 0) ? -fidelity : fidelity;

        return signed_fidelity;
    }

    void set_gamma(double new_gamma) {
        gamma_dissipation = new_gamma;
    }
    
    double get_gamma() const {
        return gamma_dissipation;
    }
};

PYBIND11_MODULE(qdd_engine, m) {
    m.doc() = "Quantum Decoherence Dynamics Engine (RG-QDD) v5.0 - N-Dimensional Tensor Network";

    py::class_<QDDEngine>(m, "QDDEngine")
        .def(py::init<int, double, double>(), 
             py::arg("dim") = 1, 
             py::arg("planck_const") = 1.0, 
             py::arg("gamma") = 0.1)
        .def("quantize_regime", &QDDEngine::quantize_regime, 
             py::arg("input_data"), py::arg("uv_cutoff"), py::arg("energy_threshold"))
        .def("calculate_entanglement_fidelity", &QDDEngine::calculate_entanglement_fidelity,
             "Calcula a coerencia quantica (0.0 a 1.0) entre duas funcoes de onda fractais",
             py::arg("macro_data"), py::arg("micro_data"), py::arg("macro_cutoff"), py::arg("micro_cutoff"))
        .def("set_gamma", &QDDEngine::set_gamma)
        .def("get_gamma", &QDDEngine::get_gamma);
}
