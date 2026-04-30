#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <complex>
#include <cmath>

namespace py = pybind11;

using Complex = std::complex<double>;

class QRWEngine {
private:
    int num_positions;
    // Estado quântico: matriz de [posição][estado da moeda (0: desce, 1: sobe)]
    std::vector<std::vector<Complex>> state;
    std::vector<std::vector<Complex>> new_state;

public:
    QRWEngine(int positions = 201) : num_positions(positions) {
        if(num_positions % 2 == 0) num_positions += 1; // Garantir tamanho ímpar com centro no 0
        state.resize(num_positions, std::vector<Complex>(2, 0.0));
        new_state.resize(num_positions, std::vector<Complex>(2, 0.0));
    }

    void reset(int start_pos = -1) {
        for(int i=0; i<num_positions; ++i) {
            state[i][0] = 0.0;
            state[i][1] = 0.0;
        }
        if(start_pos == -1) start_pos = num_positions / 2; // Inicia no centro
        
        // Inicialização simétrica padrão
        state[start_pos][0] = Complex(1.0 / std::sqrt(2.0), 0.0);
        state[start_pos][1] = Complex(0.0, 1.0 / std::sqrt(2.0));
    }

    // Moeda parametrizada pelo volume/fluxo. 
    // Theta = 0.25 * Pi (Hadamard simétrica). 
    // Theta enviesado = intenção oculta no order flow.
    void step(double theta) {
        // Matriz de moeda C(theta)
        Complex C00(std::cos(theta), 0.0);
        Complex C01(std::sin(theta), 0.0);
        Complex C10(std::sin(theta), 0.0);
        Complex C11(-std::cos(theta), 0.0);

        for(int i=0; i<num_positions; ++i) {
            new_state[i][0] = 0.0;
            new_state[i][1] = 0.0;
        }

        // Operação Unitária = Shift * Coin
        for(int i=0; i<num_positions; ++i) {
            if(std::norm(state[i][0]) == 0 && std::norm(state[i][1]) == 0) continue;

            // Aplica a moeda
            Complex val0 = C00 * state[i][0] + C01 * state[i][1]; // Ir para a esquerda
            Complex val1 = C10 * state[i][0] + C11 * state[i][1]; // Ir para a direita

            // Aplica o Shift
            if(i - 1 >= 0) new_state[i - 1][0] += val0;
            if(i + 1 < num_positions) new_state[i + 1][1] += val1;
        }

        state = new_state;
    }

    // Processa uma série temporal inteira
    double compute_interference_skew(const std::vector<double>& price_deltas, const std::vector<double>& volumes) {
        reset();
        
        int steps = price_deltas.size();
        for(int t=0; t<steps; ++t) {
            double delta = price_deltas[t];
            // Calcula o viés da moeda (theta). Se delta > 0, viés para subir.
            double bias = std::tanh(delta * volumes[t] * 0.00001); // Normaliza entre -1 e 1
            double theta = (M_PI / 4.0) + (bias * M_PI / 8.0); // Oscila ao redor da Hadamard simétrica
            
            step(theta);
        }

        // Calcula a distribuição de probabilidade final
        std::vector<double> probs(num_positions, 0.0);
        double total_prob = 0.0;
        double expected_val = 0.0;
        
        for(int i=0; i<num_positions; ++i) {
            probs[i] = std::norm(state[i][0]) + std::norm(state[i][1]);
            total_prob += probs[i];
            
            int x = i - (num_positions / 2); // Centralizado no 0
            expected_val += x * probs[i];
        }

        // Normaliza e calcula Skewness (Assimetria) para detectar acumulação
        double variance = 0.0;
        for(int i=0; i<num_positions; ++i) {
            int x = i - (num_positions / 2);
            variance += std::pow(x - expected_val, 2) * probs[i];
        }
        
        double skewness = 0.0;
        double std_dev = std::sqrt(variance);
        if(std_dev > 0) {
            for(int i=0; i<num_positions; ++i) {
                int x = i - (num_positions / 2);
                skewness += std::pow((x - expected_val) / std_dev, 3) * probs[i];
            }
        }
        
        return skewness;
    }
};

PYBIND11_MODULE(qrw_engine, m) {
    m.doc() = "Quantum Random Walk (QRW) Engine for Market Decrypting";
    py::class_<QRWEngine>(m, "QRWEngine")
        .def(py::init<int>(), py::arg("positions") = 201)
        .def("compute_interference_skew", &QRWEngine::compute_interference_skew, "Compute Probability Skewness based on Quantum Interference");
}
