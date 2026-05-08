#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <numeric>
#include <algorithm>

namespace py = pybind11;

/**
 * 🌌 RHT ENGINE v2.0 - THERMODYNAMIC RESONANCE CORE
 * Implementa a Teoria de Calor Relativo e Entropia Holográfica para alinhamento de Timeframes.
 */
class RHTEngine {
private:
    int num_timeframes;
    int time_steps;
    std::vector<std::vector<double>> tensor_matrix;
    double heat_accumulator = 0.0; // Inércia Térmica da Ressonância
    
    // Memória de Histórico para HUD
    std::vector<double> heat_history;
    std::vector<double> entropy_history;
    std::vector<double> direction_history;

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
            throw std::runtime_error("RHT: Dimensões da matriz tensorial incompatíveis.");
        }

        double *ptr = static_cast<double *>(buf.ptr);
        for (int i = 0; i < num_timeframes; ++i) {
            for (int t = 0; t < time_steps; ++t) {
                tensor_matrix[i][t] = ptr[i * time_steps + t];
            }
        }
    }

    /**
     * Calcula o histórico de Ressonância Termodinâmica.
     * Retorna um sinal que combina Coerência de Fase com Intensidade Absoluta.
     */
    std::vector<double> compute_resonance_history(double gamma = 0.1) {
        heat_history.assign(time_steps, 0.0);
        entropy_history.assign(time_steps, 1.0);
        direction_history.assign(time_steps, 0.0);
        
        double local_heat = 0.0;

        for (int t = 0; t < time_steps; ++t) {
            double sum_val = 0.0;
            double sum_abs = 0.0;
            double p_buy = 0.0; double p_sell = 0.0;

            for (int i = 0; i < num_timeframes; ++i) {
                double v = tensor_matrix[i][t];
                sum_val += v;
                sum_abs += std::abs(v);
                if(v > 0) p_buy += v; else p_sell += std::abs(v);
            }

            if (sum_abs > 1e-7) {
                double coherence = std::abs(sum_val) / sum_abs;
                double direction = (sum_val >= 0) ? 1.0 : -1.0;
                double entropy = 0.0;
                double total_p = p_buy + p_sell;
                if(total_p > 0) {
                    double pb = p_buy / total_p; double ps = p_sell / total_p;
                    if(pb > 0) entropy -= pb * std::log2(pb);
                    if(ps > 0) entropy -= ps * std::log2(ps);
                }
                
                double instant_heat = direction * std::pow(coherence, 2.5) * (sum_abs / num_timeframes);
                local_heat = (local_heat * (1.0 - gamma)) + (instant_heat * gamma);
                
                heat_history[t] = local_heat;
                entropy_history[t] = entropy;
                direction_history[t] = direction;
            } else {
                local_heat *= (1.0 - gamma);
                heat_history[t] = local_heat;
            }
        }
        return heat_history;
    }

    /**
     * Analisa o Estado Termodinâmico Atual.
     * Retorna: {Heat, Entropy, Direction, Flash_Flag}
     * Flash_Flag: 1 (Bull Ignition), -1 (Bear Ignition), 0 (Neutral)
     */
    std::vector<double> analyze_current_state(double threshold = 0.7, double decay = 0.92) {
        if (time_steps == 0) return {0.0, 1.0, 0.0, 0.0};

        int t = time_steps - 1;
        double sum_val = 0.0;
        double sum_abs = 0.0;
        
        // Contadores para Entropia de Shannon (simplificada para 2 estados: Buy/Sell)
        double p_buy = 0.0;
        double p_sell = 0.0;

        for (int i = 0; i < num_timeframes; ++i) {
            double v = tensor_matrix[i][t];
            sum_val += v;
            sum_abs += std::abs(v);
            if (v > 0) p_buy += 1.0; else if (v < 0) p_sell += 1.0;
        }

        double heat = 0.0;
        double entropy = 1.0;
        double direction = 0.0;
        double flash_flag = 0.0;

        if (sum_abs > 1e-7) {
            double coherence = std::abs(sum_val) / sum_abs;
            direction = (sum_val >= 0) ? 1.0 : -1.0;
            
            // Entropia (S): Mede a desordem do alinhamento. S=0 é alinhamento total.
            double n = (double)num_timeframes;
            if (p_buy > 0 && p_sell > 0) {
                double pb = p_buy / n;
                double ps = p_sell / n;
                entropy = -(pb * std::log2(pb) + ps * std::log2(ps));
            } else {
                entropy = 0.0;
            }

            double sum_abs = 0.0;
            double agree_count = 0;
            
            for (int i = 0; i < n; ++i) {
                double val = tensor_matrix[i][t];
                sum_abs += std::abs(val);
                // Valida consenso direcional (Sign agreement)
                if ((direction > 0 && val > 0) || (direction < 0 && val < 0)) {
                    agree_count++;
                }
            }
            
            double consensus_ratio = agree_count / n;
            double energy_factor = (sum_abs / n);

            // Gravidade Macro (H1, H2, D1)
            double inst_macro_gravity = (tensor_matrix[2][t] + tensor_matrix[3][t] + tensor_matrix[4][t]) / 3.0;
            
            // Acumulador de Inércia Macro (Para evitar normalização precoce)
            static double macro_memory = 0.0;
            macro_memory = (macro_memory * 0.95) + (inst_macro_gravity * 0.05);
            
            double effective_gravity = (inst_macro_gravity + macro_memory) / 2.0;
            
            // PROTOCOLO ZERO-TOLERANCE (Anti-Hallucination)
            bool gravity_block = false;
            if (direction > 0 && effective_gravity < -0.05) gravity_block = true; // Bloqueio TOTAL de Bull em queda
            if (direction < 0 && effective_gravity > 0.05) gravity_block = true;  // Bloqueio TOTAL de Bear em alta
            
            // Relaxed Protocol (Adaptive Purity):
            //consensus_ratio >= 0.6 para começar a aquecer, 0.8 para pureza total
            double signal_purity = (consensus_ratio >= 0.6 && !gravity_block) ? consensus_ratio : 0.0;
            double instant_heat = direction * std::pow(coherence, 2.5) * energy_factor * (1.0 - entropy) * signal_purity;
            
            heat_accumulator = (heat_accumulator * decay) + (instant_heat * (1.0 - decay));
            heat = heat_accumulator;

            // Flash Point (Ignição com Alinhamento Binário de Gravidade):
            if (!gravity_block && coherence > 0.85 && std::abs(heat) > threshold && entropy < 0.22 && consensus_ratio >= 0.8) {
                flash_flag = direction;
            }
        } else {
            heat_accumulator *= decay;
        }

        return {heat, entropy, direction, flash_flag};
    }

    py::dict get_histories() {
        py::dict d;
        d["heat"] = heat_history;
        d["entropy"] = entropy_history;
        d["direction"] = direction_history;
        return d;
    }
};

PYBIND11_MODULE(rht_engine, m) {
    m.doc() = "RHT Engine v2.0 - Thermodynamic Tensor Resonance";

    py::class_<RHTEngine>(m, "RHTEngine")
        .def(py::init<int, int>())
        .def("load_tensor_data", &RHTEngine::load_tensor_data)
        .def("compute_resonance_history", &RHTEngine::compute_resonance_history, py::arg("gamma") = 0.1)
        .def("analyze_current_state", &RHTEngine::analyze_current_state, py::arg("threshold") = 0.7, py::arg("decay") = 0.92)
        .def("get_histories", &RHTEngine::get_histories);
}