#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <complex>
#include <cmath>
#include <algorithm>

namespace py = pybind11;

using Complex = std::complex<double>;

class QRWEngine {
private:
    int num_positions;
    std::vector<Complex> state_up;
    std::vector<Complex> state_down;
    double decoherence_factor = 0.9992;
    static constexpr double EPSILON = 1e-18;

public:
    QRWEngine(int positions = 4001) : num_positions(positions) {
        if(num_positions % 2 == 0) num_positions += 1;
        state_up.assign(num_positions, 0.0);
        state_down.assign(num_positions, 0.0);
        reset();
    }

    void reset() {
        std::fill(state_up.begin(), state_up.end(), 0.0);
        std::fill(state_down.begin(), state_down.end(), 0.0);
        int center = num_positions / 2;
        double inv_sqrt2 = 1.0 / std::sqrt(2.0);
        state_up[center] = Complex(inv_sqrt2, 0.0);
        state_down[center] = Complex(inv_sqrt2, 0.0);
    }

    void step(double bias, double dyn_deco) {
        std::vector<Complex> next_up(num_positions, 0.0);
        std::vector<Complex> next_down(num_positions, 0.0);
        
        double theta = M_PI / 4.0; 
        Complex I(0.0, 1.0);
        
        // Bias rotativo suave
        Complex C00(std::cos(theta), 0.0);
        Complex C01 = I * std::sin(theta) * std::exp(I * bias);
        Complex C10 = I * std::sin(theta) * std::exp(-I * bias);
        Complex C11(std::cos(theta), 0.0);

        int center = num_positions / 2;

        for (int i = 0; i < num_positions; ++i) {
            // Força de Centralização (Potencial Harmônico Fraco)
            // Quanto mais longe do centro, mais a decoerência aumenta
            double dist_from_center = (double)(i - center) / (double)center;
            // Força de Centralização Suavizada (1e-5) para permitir drift institucional
            double local_deco = dyn_deco * (1.0 - 0.0001 * std::pow(dist_from_center * center, 2) / (double)center);
            
            Complex s_up = state_up[i] * local_deco;
            Complex s_down = state_down[i] * local_deco;
            if (std::norm(s_up) < EPSILON && std::norm(s_down) < EPSILON) continue;

            Complex v_up = C00 * s_up + C01 * s_down;
            Complex v_down = C10 * s_up + C11 * s_down;

            // Fronteiras Refletivas com Absorção
            if (i > 0) next_up[i - 1] += v_up;
            else next_down[i + 1] += v_up * 0.5; // Reflexão parcial

            if (i < num_positions - 1) next_down[i + 1] += v_down;
            else next_up[i - 1] += v_down * 0.5; // Reflexão parcial
        }
        
        // Normalização para evitar drift de energia quântica
        double norm_sum = 0.0;
        for(int i=0; i<num_positions; ++i) norm_sum += std::norm(next_up[i]) + std::norm(next_down[i]);
        if(norm_sum > 0) {
            double factor = 1.0 / std::sqrt(norm_sum);
            for(int i=0; i<num_positions; ++i) {
                next_up[i] *= factor;
                next_down[i] *= factor;
            }
        }

        state_up = std::move(next_up);
        state_down = std::move(next_down);
    }

    double get_skewness() {
        double exp_v = 0.0, total_p = 0.0;
        int center = num_positions / 2;
        for (int i = 0; i < num_positions; ++i) {
            double p = std::norm(state_up[i]) + std::norm(state_down[i]);
            total_p += p;
            exp_v += (double)(i - center) * p;
        }
        if (total_p < 1e-9) return 0.0;
        // Retorna o Drift Normalizado entre -1.0 e 1.0
        return (exp_v / total_p) / (double)center;
    }

    double get_entropy() {
        double entropy = 0.0, total_p = 0.0;
        for (int i = 0; i < num_positions; ++i) {
            double p = std::norm(state_up[i]) + std::norm(state_down[i]);
            total_p += p;
            if (p > 1e-12) entropy -= p * std::log(p);
        }
        if (total_p < 1e-9) return 0.0;
        return entropy / total_p;
    }

    double get_wave_variance() {
        double exp_v = 0.0, var = 0.0, total_p = 0.0;
        int center = num_positions / 2;
        for (int i = 0; i < num_positions; ++i) {
            double p = std::norm(state_up[i]) + std::norm(state_down[i]);
            total_p += p;
            exp_v += (double)(i - center) * p;
        }
        if (total_p < 1e-9) return 0.0;
        exp_v /= total_p;
        for (int i = 0; i < num_positions; ++i) {
            double p = std::norm(state_up[i]) + std::norm(state_down[i]);
            var += p * std::pow((double)(i - center) - exp_v, 2);
        }
        return var / total_p;
    }

    double get_coherence() {
        double max_p = 0.0;
        double total_p = 0.0;
        for (int i = 0; i < num_positions; ++i) {
            double p = std::norm(state_up[i]) + std::norm(state_down[i]);
            if (p > max_p) max_p = p;
            total_p += p;
        }
        if (total_p < 1e-9) return 0.0;
        return max_p / (total_p + 1e-12);
    }

    double update_and_get_skew(py::array_t<double> deltas, py::array_t<double> volumes, double scale) {
        auto r_d = deltas.unchecked<1>();
        auto r_v = volumes.unchecked<1>();
        int size = r_d.shape(0);
        for (int i = 0; i < size; ++i) {
            double d = r_d(i), v = r_v(i);
            // Moeda Quântica de Nova Geração (v3.6) - Range de Bias Expandido para PI/4
            // Permite interferência construtiva total para capturar explosões de preço
            double bias_angle = (M_PI / 4.0) - (std::tanh(d * scale * 2.0) * (M_PI / 4.0));
            
            double dyn_deco = decoherence_factor * (1.0 - std::abs(std::tanh(d * scale * 0.01)));

            step(bias_angle, std::clamp(dyn_deco, 0.99, 1.0));
        }
        return get_skewness();
    }

    void set_decoherence(double factor) {
        decoherence_factor = std::clamp(factor, 0.0, 1.0);
    }

    py::array_t<double> get_probability_distribution() {
        py::array_t<double> res(num_positions);
        auto r = res.mutable_unchecked<1>();
        for (int i = 0; i < num_positions; ++i) r(i) = std::norm(state_up[i]) + std::norm(state_down[i]);
        return res;
    }
};

PYBIND11_MODULE(qrw_engine, m) {
    py::class_<QRWEngine>(m, "QRWEngine")
        .def(py::init<int>(), py::arg("positions") = 401)
        .def("reset", &QRWEngine::reset)
        .def("set_decoherence", &QRWEngine::set_decoherence)
        .def("get_skewness", &QRWEngine::get_skewness)
        .def("get_entropy", &QRWEngine::get_entropy)
        .def("get_wave_variance", &QRWEngine::get_wave_variance)
        .def("get_coherence", &QRWEngine::get_coherence)
        .def("get_probability_distribution", &QRWEngine::get_probability_distribution)
        .def("update_and_get_skew", &QRWEngine::update_and_get_skew, py::arg("deltas"), py::arg("volumes"), py::arg("scale"));
}
