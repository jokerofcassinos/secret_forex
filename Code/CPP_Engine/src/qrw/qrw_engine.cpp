#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#include <pybind11/pybind11.h>     
#include <pybind11/numpy.h>        
#include <pybind11/stl.h>
#include <vector>
#include <complex>
#include <cmath>
#include <algorithm>
#include <omp.h>

namespace py = pybind11;

using Complex = std::complex<double>;

class QRWEngine {
private:
    int num_positions;
    std::vector<Complex> state_up;
    std::vector<Complex> state_down;
    double decoherence_factor = 0.9995; // ASI-5 Low decoherence
    static constexpr double EPSILON = 1e-15;

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
        state_down[center] = Complex(0.0, -inv_sqrt2);
    }

    void internal_step(std::vector<Complex>& s_up, std::vector<Complex>& s_down, double theta, double phi, double varphi) {
        std::vector<Complex> n_up(num_positions, 0.0);
        std::vector<Complex> n_down(num_positions, 0.0);

        Complex I(0.0, 1.0);

        Complex C00 = std::exp(I * phi) * std::cos(theta);
        Complex C01 = std::exp(I * varphi) * std::sin(theta);
        Complex C10 = -std::exp(-I * varphi) * std::sin(theta);
        Complex C11 = std::exp(-I * phi) * std::cos(theta);

        #pragma omp parallel for
        for (int i = 0; i < num_positions; ++i) {
            Complex u_term = 0.0;
            Complex d_term = 0.0;

            if (i < num_positions - 1) {
                Complex su = s_up[i+1] * decoherence_factor;
                Complex sd = s_down[i+1] * decoherence_factor;
                u_term = C00 * su + C01 * sd;
            } else {
                Complex su = s_up[i-1] * decoherence_factor;
                Complex sd = s_down[i-1] * decoherence_factor;
                u_term = (C10 * su + C11 * sd) * 0.5;
            }

            if (i > 0) {
                Complex su = s_up[i-1] * decoherence_factor;
                Complex sd = s_down[i-1] * decoherence_factor;
                d_term = C10 * su + C11 * sd;
            } else {
                Complex su = s_up[i+1] * decoherence_factor;
                Complex sd = s_down[i+1] * decoherence_factor;
                d_term = (C00 * su + C01 * sd) * 0.5;
            }

            n_up[i] = u_term;
            n_down[i] = d_term;
        }

        double norm_sum = 0.0;
        #pragma omp parallel for reduction(+:norm_sum)
        for (int i = 0; i < num_positions; ++i) {
            norm_sum += std::norm(n_up[i]) + std::norm(n_down[i]);
        }

        if (norm_sum > 0) {
            double factor = 1.0 / std::sqrt(norm_sum);
            #pragma omp parallel for
            for (int i = 0; i < num_positions; ++i) {
                n_up[i] *= factor;
                n_down[i] *= factor;
            }
        }

        s_up = std::move(n_up);
        s_down = std::move(n_down);
    }

    py::dict step(double current_price, double atr, double current_momentum) {
        int center = num_positions / 2;

        // Amplificação Z-Score (SU(2) Gain)
        double z_score = current_momentum;
        double magnitude = std::abs(z_score);
        double brutal_gain = std::tanh(magnitude * 5.0); // 0 to 1

        // Theta: 0 = Balístico (Sem mistura), PI/4 = Hadamard (Máxima Difusão)
        // Em alta volatilidade/momentum, queremos comportamento balístico direcional.
        double theta = (M_PI / 4.0) * (1.0 - brutal_gain);
        
        // Fases para interferência construtiva direcional
        double phi = z_score * M_PI;
        double varphi = 0.0;

        // Injeção de Estado (Inversão Corrigida):
        // Momentum > 0 (Bull) -> Injeta no Down (que se move para a DIREITA)
        // Momentum < 0 (Bear) -> Injeta no Up (que se move para a ESQUERDA)
        double inject_amount = magnitude * 0.5; // Escalar injeção
        if (z_score > 0) {
            state_down[center] += Complex(inject_amount, 0.0);
        } else if (z_score < 0) {
            state_up[center] += Complex(inject_amount, 0.0);
        }

        // Executa múltiplos sub-passos internos para propagação visível (Dinamismo ASI)
        for(int s = 0; s < 3; ++s) {
            internal_step(state_up, state_down, theta, phi, varphi);
        }

        std::vector<double> probs(num_positions, 0.0);
        double max_prob = 0.0;
        double sum_right = 0.0;
        double sum_left = 0.0;

        for (int i = 0; i < num_positions; ++i) {
            double p = std::norm(state_up[i]) + std::norm(state_down[i]);
            probs[i] = p;
            if (p > max_prob) {
                max_prob = p;
            }
            
            // Acumular massa de probabilidade para detecção de viés
            if (i > center + 5) {
                sum_right += p;
            } else if (i < center - 5) {
                sum_left += p;
            }
        }

        py::dict res;
        res["max_prob"] = max_prob;
        res["prob_right"] = sum_right;
        res["prob_left"] = sum_left;
        res["distribution"] = py::array_t<double>({num_positions}, {sizeof(double)}, probs.data());
        return res;
    }

    double get_skewness() {
        double exp_v = 0.0, total_p = 0.0;
        int center = num_positions / 2;

        #pragma omp parallel for reduction(+:exp_v, total_p)
        for (int i = 0; i < num_positions; ++i) {
            double p = std::norm(state_up[i]) + std::norm(state_down[i]);
            total_p += p;
            exp_v += (double)(i - center) * p;
        }
        if (total_p < 1e-9) return 0.0;
        return (exp_v / total_p) / (double)center;
    }

    double update_and_get_skew(py::array_t<double> deltas, py::array_t<double> volumes, double scale) {
        auto r_d = deltas.unchecked<1>();
        auto r_v = volumes.unchecked<1>();
        int size = r_d.shape(0);

        for (int i = 0; i < size; ++i) {
            double d = r_d(i);
            double v = (r_v.shape(0) > i) ? r_v(i) : 1.0;

            double momentum = d * v * scale;
            double theta = (M_PI / 4.0) - (std::tanh(std::abs(momentum)) * (M_PI / 8.0));
            double phi = momentum * M_PI;
            double varphi = momentum * M_PI * 0.5;

            internal_step(state_up, state_down, theta, phi, varphi);
        }
        return get_skewness();
    }

    py::array_t<double> get_probability_distribution() {
        py::array_t<double> res(num_positions);
        auto r = res.mutable_unchecked<1>();
        for (int i = 0; i < num_positions; ++i) r(i) = std::norm(state_up[i]) + std::norm(state_down[i]);
        return res;
    }
};

PYBIND11_MODULE(qrw_engine, m) {
    m.doc() = "QRW Engine (Quantum Random Walk - ASI-5 Adaptive Unitary Matrix with SU(2) Rotation and OMP)";
    py::class_<QRWEngine>(m, "QRWEngine")
        .def(py::init<int>(), py::arg("positions") = 401)
        .def("reset", &QRWEngine::reset)
        .def("get_skewness", &QRWEngine::get_skewness)
        .def("get_probability_distribution", &QRWEngine::get_probability_distribution)
        .def("update_and_get_skew", &QRWEngine::update_and_get_skew, py::arg("deltas"), py::arg("volumes"), py::arg("scale"))
        .def("step", &QRWEngine::step,
             py::arg("current_price"), py::arg("atr"), py::arg("current_momentum"));
}
