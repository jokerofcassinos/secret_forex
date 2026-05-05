#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <stdexcept>
#include <numeric>

namespace py = pybind11;

// Teoria de Ressonância Holográfica de Tensores (RHT)
class RHTEngine {
private:
    int num_timeframes;
    int time_steps;
    std::vector<std::vector<double>> tensor_matrix;

public:
    RHTEngine(int num_tf, int t_steps) : num_timeframes(num_tf), time_steps(t_steps) {
        if (num_timeframes <= 0 || time_steps <= 0) throw std::invalid_argument("Dimensões devem ser positivas.");
        tensor_matrix.resize(num_timeframes, std::vector<double>(time_steps, 0.0));
    }

    // Carrega dados. Formato: Matriz 2D onde cada linha é um timeframe normalizado (mesmo tamanho T)
    // Exemplo: Linha 0 = M5 (interp), Linha 1 = M15 (interp), etc.
    void load_tensor_data(py::array_t<double> input_data) {
        py::buffer_info buf = input_data.request();
        if (buf.ndim != 2 || buf.shape[0] != num_timeframes || buf.shape[1] != time_steps) {
            throw std::runtime_error("Formato de array numpy incompatível para o Tensor 3D.");
        }

        double *ptr = static_cast<double *>(buf.ptr);
        for (int i = 0; i < num_timeframes; ++i) {
            for (int t = 0; t < time_steps; ++t) {
                // A normalização para o espectro de onda já deve vir pré-calculada do Python (Ex: Z-score do momentum)
                tensor_matrix[i][t] = ptr[i * time_steps + t];
            }
        }
    }

    // Calcula a Interferência Construtiva Holográfica
    // Retorna a Ressonância de Liquidez Absoluta para o tempo t
    std::vector<double> compute_resonance() {
        std::vector<double> resonance_signal(time_steps, 0.0);
        
        for (int t = 0; t < time_steps; ++t) {
            double sum_amplitudes = 0.0;
            double sum_absolute_amplitudes = 0.0;
            
            for (int i = 0; i < num_timeframes; ++i) {
                double wave_val = tensor_matrix[i][t];
                sum_amplitudes += wave_val;
                sum_absolute_amplitudes += std::abs(wave_val);
            }
            
            // Interferência construtiva ocorre quando todos os vetores estão na mesma direção (sinal).
            // A ressonância é o quadrado da soma preservando o sinal, escalonada pela entropia.
            // Se sum_amplitudes == sum_absolute_amplitudes, alinhamento total de ALTA (Bull Resonance)
            // Se sum_amplitudes == -sum_absolute_amplitudes, alinhamento total de BAIXA (Bear Resonance)
            
            if (sum_absolute_amplitudes > 1e-9) {
                // Fator de coerência de fase: Varia de -1 (Bear total) a +1 (Bull total)
                double phase_coherence = std::abs(sum_amplitudes) / sum_absolute_amplitudes;
                
                // Multiplicador de gravidade quântica (Quanto maior a soma absoluta, maior a energia no mercado)
                double quantum_gravity = sum_absolute_amplitudes / num_timeframes;
                
                // O sinal (direção)
                double direction = (sum_amplitudes > 0) ? 1.0 : -1.0;
                
                // Ressonância final (Pulso do Tensor)
                resonance_signal[t] = direction * std::pow(phase_coherence, 3) * quantum_gravity;
            } else {
                resonance_signal[t] = 0.0;
            }
        }
        
        return resonance_signal;
    }
    
    // Retorna o valor de ressonância no instante atual (último tick) e uma flag de colapso
    // threshold: O valor mínimo de quantum_gravity necessário para validar um colapso
    std::vector<double> get_instant_collapse(double threshold = 0.8) {
        if (time_steps == 0) return {0.0, 0.0, 0.0};
        
        int t = time_steps - 1; // Instante atual (último elemento)
        double sum_amplitudes = 0.0;
        double sum_absolute_amplitudes = 0.0;
        
        for (int i = 0; i < num_timeframes; ++i) {
            double wave_val = tensor_matrix[i][t];
            sum_amplitudes += wave_val;
            sum_absolute_amplitudes += std::abs(wave_val);
        }
        
        double resonance = 0.0;
        double direction = 0.0;
        double collapse_flag = 0.0; // 0 = Neutro, 1 = Buy (Bull), -1 = Sell (Bear)
        
        if (sum_absolute_amplitudes > 1e-9) {
            double phase_coherence = std::abs(sum_amplitudes) / sum_absolute_amplitudes;
            double quantum_gravity = sum_absolute_amplitudes / num_timeframes;
            direction = (sum_amplitudes > 0) ? 1.0 : -1.0;
            
            resonance = direction * std::pow(phase_coherence, 3) * quantum_gravity;
            
            // Condição de colapso: Alta coerência de fase (> 0.9) e gravidade acima do limiar institucional
            if (phase_coherence > 0.9 && quantum_gravity > threshold) {
                collapse_flag = direction;
            }
        }
        
        return {resonance, direction, collapse_flag}; // Retorna Ressonância, Vetor Direcional e Sinal de Ação
    }
};

PYBIND11_MODULE(rht_engine, m) {
    m.doc() = "Ressonancia Holografica de Tensores (RHT) Engine";
    
    py::class_<RHTEngine>(m, "RHTEngine")
        .def(py::init<int, int>())
        .def("load_tensor_data", &RHTEngine::load_tensor_data, "Carrega matriz de tensores fractais (Timeframes x Ticks)")
        .def("compute_resonance", &RHTEngine::compute_resonance, "Calcula a linha do tempo da ressonancia holografica")
        .def("get_instant_collapse", &RHTEngine::get_instant_collapse, 
             py::arg("threshold") = 0.8, 
             "Avalia se ocorreu interferencia construtiva no tempo t (Gatilho Operacional)");
}