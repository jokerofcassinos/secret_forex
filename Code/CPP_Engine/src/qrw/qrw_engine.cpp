#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <complex>
#include <cmath>
#include <algorithm>
#include <random>
#include <omp.h>

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

    // [METODO INTERNO DE STEP - Otimizado]
    void internal_step(std::vector<Complex>& s_up, std::vector<Complex>& s_down, double bias, double dyn_deco) {
        std::vector<Complex> n_up(num_positions, 0.0);
        std::vector<Complex> n_down(num_positions, 0.0);
        double theta = M_PI / 4.0; 
        Complex I(0.0, 1.0);
        Complex C00(std::cos(theta), 0.0);
        Complex C01 = I * std::sin(theta) * std::exp(I * bias);
        Complex C10 = I * std::sin(theta) * std::exp(-I * bias);
        Complex C11(std::cos(theta), 0.0);
        int center = num_positions / 2;

        for (int i = 0; i < num_positions; ++i) {
            double dist = (double)(i - center) / (double)center;
            double l_deco = dyn_deco * (1.0 - 0.0001 * std::pow(dist * center, 2) / (double)center);
            Complex su = s_up[i] * l_deco;
            Complex sd = s_down[i] * l_deco;
            if (std::norm(su) < EPSILON && std::norm(sd) < EPSILON) continue;
            Complex vu = C00 * su + C01 * sd;
            Complex vd = C10 * su + C11 * sd;
            if (i > 0) n_up[i - 1] += vu;
            else n_down[i + 1] += vu * 0.5;
            if (i < num_positions - 1) n_down[i + 1] += vd;
            else n_up[i - 1] += vd * 0.5;
        }
        s_up = std::move(n_up);
        s_down = std::move(n_down);
    }

    void step(double bias, double dyn_deco) {
        internal_step(state_up, state_down, bias, dyn_deco);
        // Normalização
        double norm_sum = 0.0;
        for(int i=0; i<num_positions; ++i) norm_sum += std::norm(state_up[i]) + std::norm(state_down[i]);
        if(norm_sum > 0) {
            double factor = 1.0 / std::sqrt(norm_sum);
            for(int i=0; i<num_positions; ++i) { state_up[i] *= factor; state_down[i] *= factor; }
        }
    }

    // --- [NOVO MOTOR DE PRE-COGNITION C++] ---
    std::vector<double> simulate_future_collapse(
        double current_price, 
        double atr, 
        int steps, 
        int simulations, 
        double top_zone, 
        double bottom_zone,
        double threshold_mult
    ) {
        std::vector<double> breach_levels;
        breach_levels.reserve(simulations);
        
        // Detectar modo de operação: Contenção ou Fuga (Escape)
        bool is_outside_top = current_price > (top_zone - (atr * threshold_mult));
        bool is_outside_bottom = current_price < (bottom_zone + (atr * threshold_mult));
        bool escape_mode = is_outside_top || is_outside_bottom;

        #pragma omp parallel
        {
            std::random_device rd;
            std::mt19937 gen(rd() ^ (omp_get_thread_num() + (int)time(NULL)));
            std::normal_distribution<> d(0, atr * 0.5); 
            
            std::vector<double> local_breaches;
            
            #pragma omp for
            for(int s = 0; s < simulations; ++s) {
                double sim_p = current_price;
                bool collapsed = false;
                
                for(int t = 0; t < steps; ++t) {
                    sim_p += d(gen);
                    
                    if (escape_mode) {
                        // Modo Fuga: Reversão brusca é o perigo
                        double dynamic_boundary_bottom = current_price - (atr * threshold_mult * 1.5);
                        double dynamic_boundary_top = current_price + (atr * threshold_mult * 3.0);
                        
                        if (is_outside_top && sim_p < dynamic_boundary_bottom) {
                            local_breaches.push_back(sim_p);
                            collapsed = true;
                            break;
                        }
                        if (is_outside_bottom && sim_p > dynamic_boundary_top) {
                            local_breaches.push_back(sim_p);
                            collapsed = true;
                            break;
                        }
                    } else {
                        if (sim_p > top_zone - (atr * threshold_mult) || sim_p < bottom_zone + (atr * threshold_mult)) {
                            local_breaches.push_back(sim_p);
                            collapsed = true;
                            break;
                        }
                    }
                }
                if (!collapsed) local_breaches.push_back(sim_p);
            }
            
            #pragma omp critical
            breach_levels.insert(breach_levels.end(), local_breaches.begin(), local_breaches.end());
        }
        
        return breach_levels;
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
        return (exp_v / total_p) / (double)center;
    }

    double update_and_get_skew(py::array_t<double> deltas, py::array_t<double> volumes, double scale) {
        auto r_d = deltas.unchecked<1>();
        int size = r_d.shape(0);
        for (int i = 0; i < size; ++i) {
            double d = r_d(i);
            double bias_angle = (M_PI / 4.0) - (std::tanh(d * scale * 2.0) * (M_PI / 4.0));
            double dyn_deco = decoherence_factor * (1.0 - std::abs(std::tanh(d * scale * 0.01)));
            step(bias_angle, std::clamp(dyn_deco, 0.99, 1.0));
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
    py::class_<QRWEngine>(m, "QRWEngine")
        .def(py::init<int>(), py::arg("positions") = 401)
        .def("reset", &QRWEngine::reset)
        .def("get_skewness", &QRWEngine::get_skewness)
        .def("get_probability_distribution", &QRWEngine::get_probability_distribution)
        .def("update_and_get_skew", &QRWEngine::update_and_get_skew, py::arg("deltas"), py::arg("volumes"), py::arg("scale"))
        .def("simulate_future_collapse", &QRWEngine::simulate_future_collapse, 
             py::arg("current_price"), py::arg("atr"), py::arg("steps"), 
             py::arg("simulations"), py::arg("top_zone"), py::arg("bottom_zone"), 
             py::arg("threshold_mult"));
}
