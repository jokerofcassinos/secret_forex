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
    std::vector<std::vector<Complex>> state;
    std::vector<std::vector<Complex>> new_state;

public:
    QRWEngine(int positions = 201) : num_positions(positions) {
        if(num_positions % 2 == 0) num_positions += 1;
        state.resize(num_positions, std::vector<Complex>(2, 0.0));
        new_state.resize(num_positions, std::vector<Complex>(2, 0.0));
    }

    void reset(int start_pos = -1) {
        for(int i=0; i<num_positions; ++i) {
            state[i][0] = 0.0;
            state[i][1] = 0.0;
        }
        if(start_pos == -1) start_pos = num_positions / 2;
        
        // Inicialização Assimétrica para gerar Drift Quântico
        state[start_pos][0] = Complex(1.0, 0.0);
        state[start_pos][1] = Complex(0.0, 0.0);
    }

    void step(double theta) {
        Complex C00(std::cos(theta), 0.0);
        Complex C01(std::sin(theta), 0.0);
        Complex C10(std::sin(theta), 0.0);
        Complex C11(-std::cos(theta), 0.0);

        for(int i=0; i<num_positions; ++i) {
            new_state[i][0] = 0.0;
            new_state[i][1] = 0.0;
        }

        for(int i=0; i<num_positions; ++i) {
            if(std::norm(state[i][0]) == 0 && std::norm(state[i][1]) == 0) continue;

            Complex val0 = C00 * state[i][0] + C01 * state[i][1];
            Complex val1 = C10 * state[i][0] + C11 * state[i][1];

            if(i - 1 >= 0) new_state[i - 1][0] += val0;
            if(i + 1 < num_positions) new_state[i + 1][1] += val1;
        }

        state = new_state;
    }

    double get_expected_value() {
        double expected_val = 0.0;
        for(int i=0; i<num_positions; ++i) {
            double prob = std::norm(state[i][0]) + std::norm(state[i][1]);
            int x = i - (num_positions / 2);
            expected_val += x * prob;
        }
        return expected_val;
    }

    // Calcula o Desvio do Drift Quântico (Biased vs Unbiased)
    double compute_interference_skew(const std::vector<double>& price_deltas, const std::vector<double>& volumes) {
        int steps = price_deltas.size();
        
        // 1. Simulação Não-Viesada (Baseline Drift)
        reset();
        for(int t=0; t<steps; ++t) {
            step(M_PI / 4.0); // Hadamard puro
        }
        double baseline_expected = get_expected_value();

        // 2. Simulação Viesada (Com Intenção Institucional Oculta)
        reset();
        for(int t=0; t<steps; ++t) {
            double delta = price_deltas[t];
            // Viés baseado no momentum do tick. 
            double bias = std::tanh(delta * volumes[t] * 0.00001); 
            double theta = (M_PI / 4.0) + (bias * M_PI / 8.0);
            step(theta);
        }
        double biased_expected = get_expected_value();

        // Se o drift com viés for maior (mais à direita/Bullish) que o baseline, retorna positivo
        // Invertemos o sinal porque o drift natural do [1,0] é negativo (esquerda).
        double drift_diff = biased_expected - baseline_expected;
        
        return drift_diff;
    }
};

PYBIND11_MODULE(qrw_engine, m) {
    m.doc() = "Quantum Random Walk (QRW) Engine for Market Decrypting";
    py::class_<QRWEngine>(m, "QRWEngine")
        .def(py::init<int>(), py::arg("positions") = 201)
        .def("compute_interference_skew", &QRWEngine::compute_interference_skew, "Compute Probability Drift based on Quantum Interference");
}
