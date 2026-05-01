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
    
    // FIX P0-03: Epsilon para comparação numérica
    static constexpr double EPSILON = 1e-30;

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
        
        // Inicialização balanceada para simetria perfeita
        double inv_sqrt2 = 1.0 / std::sqrt(2.0);
        state[start_pos][0] = Complex(inv_sqrt2, 0.0);
        state[start_pos][1] = Complex(inv_sqrt2, 0.0);  // Ambas reais para simetria com operador i*sin
    }

    void step(double bias) {
        // Operador Unitário Simétrico Biased (SU(2))
        double theta = M_PI / 4.0;
        Complex I(0.0, 1.0);
        Complex C00(std::cos(theta), 0.0);
        Complex C01 = I * std::sin(theta) * std::exp(I * bias);
        Complex C10 = I * std::sin(theta) * std::exp(-I * bias);
        Complex C11(std::cos(theta), 0.0);

        for(int i=0; i<num_positions; ++i) {
            new_state[i][0] = 0.0;
            new_state[i][1] = 0.0;
        }

        for(int i=0; i<num_positions; ++i) {
            // FIX P0-03: Comparação com epsilon ao invés de ==0
            if(std::norm(state[i][0]) < EPSILON && std::norm(state[i][1]) < EPSILON) continue;

            Complex val0 = C00 * state[i][0] + C01 * state[i][1];
            Complex val1 = C10 * state[i][0] + C11 * state[i][1];

            if(i - 1 >= 0) new_state[i - 1][0] += val0;
            if(i + 1 < num_positions) new_state[i + 1][1] += val1;
        }

        state = new_state;
    }

    double get_expected_value() {
        double expected_val = 0.0;
        int center = num_positions / 2;
        for(int i=0; i<num_positions; ++i) {
            double prob = std::norm(state[i][0]) + std::norm(state[i][1]);
            int x = i - center;
            expected_val += x * prob;
        }
        return expected_val;
    }
    
    // FIX P1-04: Calcula a norma total para normalização
    double get_total_probability() {
        double total = 0.0;
        for(int i=0; i<num_positions; ++i) {
            total += std::norm(state[i][0]) + std::norm(state[i][1]);
        }
        return total;
    }
    
    // Calcula a variância da distribuição para normalização do skew
    double get_variance() {
        double mean = get_expected_value();
        double var = 0.0;
        int center = num_positions / 2;
        for(int i=0; i<num_positions; ++i) {
            double prob = std::norm(state[i][0]) + std::norm(state[i][1]);
            double x = (double)(i - center);
            var += (x - mean) * (x - mean) * prob;
        }
        return var;
    }

    // FIX P1-03: Aceita atr_scale para calibrar o bias dinamicamente
    // FIX P1-04: Retorna skewness normalizada pela variância
    double compute_interference_skew(const std::vector<double>& price_deltas, 
                                     const std::vector<double>& volumes,
                                     double atr_scale) {
        int steps = price_deltas.size();
        if(steps == 0) return 0.0;
        
        // Calcular escala de normalização do bias
        // FIX P1-03: atr_scale é passado pelo Python (1/ATR) para calibrar
        double bias_factor = (atr_scale > 1e-12) ? atr_scale : 0.001;
        
        // 1. Simulação Não-Viesada (Baseline)
        reset();
        for(int t=0; t<steps; ++t) {
            step(0.0); // Bias puro zero
        }
        double baseline_expected = get_expected_value();
        double baseline_var = get_variance();
        
        // 2. Simulação Viesada (Com Intenção Institucional)
        reset();
        for(int t=0; t<steps; ++t) {
            double delta = price_deltas[t];
            double vol = volumes[t];
            double bias = std::tanh(delta * vol * bias_factor); 
            step(bias);
        }
        double biased_expected = get_expected_value();
        
        // FIX P1-04: Normalizar o drift pela variância do baseline
        double drift_diff = biased_expected - baseline_expected;
        double std_dev = std::sqrt(baseline_var + 1e-12);
        double normalized_skew = drift_diff / std_dev;
        
        return normalized_skew;
    }
};

PYBIND11_MODULE(qrw_engine, m) {
    m.doc() = "Quantum Random Walk (QRW) Engine v2.0 - Unitary Coin Operator";
    py::class_<QRWEngine>(m, "QRWEngine")
        .def(py::init<int>(), py::arg("positions") = 201)
        .def("compute_interference_skew", &QRWEngine::compute_interference_skew, 
             "Compute normalized Probability Drift based on Quantum Interference",
             py::arg("price_deltas"), py::arg("volumes"), py::arg("atr_scale"));
}
