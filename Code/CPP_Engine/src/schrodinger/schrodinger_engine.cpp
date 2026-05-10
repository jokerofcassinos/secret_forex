#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <complex>
#include <cmath>
#include <iostream>
#include <algorithm>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;
using Complex = std::complex<double>;

class QuantumCloudSolver {
private:
    int Nx;
    double dx;
    std::vector<Complex> psi;
    std::vector<double> V;
    std::vector<double> prob_density;
    std::vector<double> accumulated_density; // v25.1: Long Exposure
    std::vector<double> spatial_mass;
    std::vector<Complex> alpha;
    std::vector<Complex> beta;
    std::vector<Complex> gamma_arr;
    int absorb_width;
    std::vector<double> absorb_profile;

    void build_absorbing_profile() {
        absorb_profile.resize(Nx, 0.0);
        for(int i = 0; i < absorb_width; ++i) {
            double frac = (double)(absorb_width - i) / (double)absorb_width;
            double strength = 100.0 * std::pow(frac, 3); 
            absorb_profile[i] = strength;
            absorb_profile[Nx - 1 - i] = strength;
        }
    }

public:
    QuantumCloudSolver(int N, double dx_val) : Nx(N), dx(dx_val) {
        psi.resize(Nx, 0.0); V.resize(Nx, 0.0); prob_density.resize(Nx, 0.0);
        accumulated_density.resize(Nx, 0.0);
        spatial_mass.resize(Nx, 1.0);
        alpha.resize(Nx, 0.0); beta.resize(Nx, 0.0); gamma_arr.resize(Nx, 0.0);
        absorb_width = std::max(5, Nx / 20);
        build_absorbing_profile();
    }

    void initialize_gaussian(double x0, double sigma, double k0) {
        py::gil_scoped_release release;
        double norm = 0.0;
        #pragma omp parallel for reduction(+:norm)
        for (int i = 0; i < Nx; ++i) {
            double x = i * dx;
            double envelope = std::exp(-0.5 * std::pow((x - x0) / sigma, 2));
            psi[i] = Complex(envelope * std::cos(k0 * x), envelope * std::sin(k0 * x));
            norm += std::norm(psi[i]) * dx;
        }
        norm = std::sqrt(norm);
        if(norm > 1e-15) { 
            #pragma omp parallel for
            for (int i = 0; i < Nx; ++i) psi[i] /= norm; 
        }
        update_probability_density();
    }

    void update_potential(const std::vector<double>& new_V) {
        if ((int)new_V.size() != Nx) throw std::runtime_error("Potential array size must match Nx");
        V = new_V;
    }

    void update_spatial_mass(const std::vector<double>& new_mass) {
        if ((int)new_mass.size() != Nx) throw std::runtime_error("Mass array size must match Nx");
        spatial_mass = new_mass;
    }

    void step_forward(double dt, double global_mass_scale, double hbar_val, double drift_k = 0.0) {
        py::gil_scoped_release release;
        Complex I(0.0, 1.0);
        double hbar = hbar_val;
        
        std::vector<Complex> psi_backup = psi;
        std::fill(accumulated_density.begin(), accumulated_density.end(), 0.0);

        double min_mass = 100.0;
        for(double m : spatial_mass) if(m < min_mass) min_mass = m;
        double eff_mass = std::max(1e-6, min_mass * global_mass_scale);
        
        double r_mag = (hbar * dt) / (4.0 * eff_mass * dx * dx);
        double effective_dt = dt;
        if(r_mag > 0.5) effective_dt = (0.5 * 4.0 * eff_mass * dx * dx) / hbar;
        int substeps = std::max(1, std::min(100, (int)std::ceil(dt / effective_dt)));
        effective_dt = dt / (double)substeps;

        bool has_nan = false;
        for(int sub = 0; sub < substeps; ++sub) {
            std::vector<Complex> d(Nx, 0.0);
            #pragma omp parallel for
            for (int i = 1; i < Nx - 1; ++i) {
                double m_i = spatial_mass[i] * global_mass_scale;
                Complex r = (I * hbar * effective_dt) / (4.0 * m_i * dx * dx);
                
                // ADVECCÃO DE PLANCK v25.0: Correção de segunda ordem para fluxo contínuo
                // Minimiza a dispersão artificial unindo pacotes de onda ('Comet Trail')
                double v_scaled = drift_k * effective_dt / dx;
                Complex planck_advection = (v_scaled * v_scaled) / 2.0;
                
                // Efeito Doppler Financeiro (v24.1): Drift_k deforma o potencial na direção do movimento
                double doppler_shift = drift_k * (i - Nx/2) * dx * 0.1;
                Complex v_complex(V[i] + doppler_shift, -absorb_profile[i]);
                
                Complex drift_term = (drift_k * effective_dt) / (2.0 * dx);
                Complex v_term = (I * effective_dt * v_complex) / (2.0 * hbar);
                
                // Matriz Crank-Nicolson Estendida (v25.0)
                alpha[i] = -r - drift_term + planck_advection; 
                beta[i] = 1.0 + 2.0 * r + v_term - 2.0 * planck_advection; 
                gamma_arr[i] = -r + drift_term + planck_advection;
                
                d[i] = (r + drift_term - planck_advection) * psi[i-1] + 
                       (1.0 - 2.0 * r - v_term + 2.0 * planck_advection) * psi[i] + 
                       (r - drift_term - planck_advection) * psi[i+1];
            }
            beta[0] = 1.0; d[0] = 0.0; gamma_arr[0] = 0.0;
            beta[Nx-1] = 1.0; d[Nx-1] = 0.0; alpha[Nx-1] = 0.0;

            std::vector<Complex> c_prime(Nx, 0.0), d_prime(Nx, 0.0);
            c_prime[0] = gamma_arr[0] / beta[0]; d_prime[0] = d[0] / beta[0];
            for (int i = 1; i < Nx; ++i) {
                Complex denom = beta[i] - alpha[i] * c_prime[i-1];
                if(std::abs(denom) < 1e-18) denom = Complex(1e-18, 0.0);
                Complex m_val = 1.0 / denom;
                c_prime[i] = gamma_arr[i] * m_val;
                d_prime[i] = (d[i] - alpha[i] * d_prime[i-1]) * m_val;
            }
            psi[Nx-1] = d_prime[Nx-1];
            for (int i = Nx - 2; i >= 0; --i) {
                psi[i] = d_prime[i] - c_prime[i] * psi[i+1];
                if(!std::isfinite(psi[i].real()) || !std::isfinite(psi[i].imag())) {
                    has_nan = true; break;
                }
            }
            if(has_nan) break;

            // v25.1: Acumulação de Densidade Temporal (Long Exposure)
            // Captura o rastro da onda durante a evolução interna
            #pragma omp parallel for
            for (int i = 0; i < Nx; ++i) {
                accumulated_density[i] += std::norm(psi[i]);
            }
        }
        
        if(has_nan) {
            psi = psi_backup; 
        } else {
            double norm = 0.0;
            for (int i = 0; i < Nx; ++i) norm += std::norm(psi[i]) * dx;
            norm = std::sqrt(norm);
            if(norm > 1e-15) {
                for (int i = 0; i < Nx; ++i) psi[i] /= norm;
            }
        }
        
        // v25.1: Média da densidade acumulada para fluxo contínuo
        if (!has_nan) {
            #pragma omp parallel for
            for (int i = 0; i < Nx; ++i) {
                prob_density[i] = accumulated_density[i] / (double)substeps;
            }
        } else {
            update_probability_density();
        }
    }

    void shift_grid(int steps) {
        py::gil_scoped_release release;
        if (std::abs(steps) >= Nx) {
            std::fill(psi.begin(), psi.end(), Complex(0.0, 0.0));
            return;
        }
        if (steps > 0) {
            std::move(psi.begin() + steps, psi.end(), psi.begin());
            std::fill(psi.end() - steps, psi.end(), Complex(0.0, 0.0));
            std::move(V.begin() + steps, V.end(), V.begin());
            std::fill(V.end() - steps, V.end(), V.back());
        } else if (steps < 0) {
            int abs_steps = -steps;
            std::move_backward(psi.begin(), psi.end() - abs_steps, psi.end());
            std::fill(psi.begin(), psi.begin() + abs_steps, Complex(0.0, 0.0));
            std::move_backward(V.begin(), V.end() - abs_steps, V.end());
            std::fill(V.begin(), V.begin() + abs_steps, V.front());
        }
        update_probability_density();
    }

    void calculate_stationary_state(int iterations, double hbar_val) {
        py::gil_scoped_release release;
        double dt_im = 0.05; 
        for(int it = 0; it < iterations; ++it) {
            std::vector<Complex> d(Nx, 0.0);
            #pragma omp parallel for
            for (int i = 1; i < Nx - 1; ++i) {
                double r = (hbar_val * dt_im) / (2.0 * spatial_mass[i] * dx * dx);
                double v_term = (dt_im * V[i]) / hbar_val;
                alpha[i] = -r; beta[i] = 1.0 + 2.0 * r + v_term; gamma_arr[i] = -r;
                d[i] = r * psi[i-1] + (1.0 - 2.0 * r - v_term) * psi[i] + r * psi[i+1];
            }
            beta[0] = 1.0; d[0] = 0.0; gamma_arr[0] = 0.0;
            beta[Nx-1] = 1.0; d[Nx-1] = 0.0; alpha[Nx-1] = 0.0;

            std::vector<Complex> c_prime(Nx, 0.0), d_prime(Nx, 0.0);
            c_prime[0] = gamma_arr[0] / beta[0]; d_prime[0] = d[0] / beta[0];
            for (int i = 1; i < Nx; ++i) {
                Complex denom = beta[i] - alpha[i] * c_prime[i-1];
                if(std::abs(denom) < 1e-18) denom = Complex(1e-18, 0.0);
                Complex m_val = 1.0 / denom;
                c_prime[i] = gamma_arr[i] * m_val;
                d_prime[i] = (d[i] - alpha[i] * d_prime[i-1]) * m_val;
            }
            psi[Nx-1] = d_prime[Nx-1];
            for (int i = Nx - 2; i >= 0; --i) psi[i] = d_prime[i] - c_prime[i] * psi[i+1];

            double norm = 0.0;
            for (int i = 0; i < Nx; ++i) norm += std::norm(psi[i]) * dx;
            norm = std::sqrt(norm);
            if(norm > 1e-15) { for (int i = 0; i < Nx; ++i) psi[i] /= norm; }
        }
        update_probability_density();
    }
void recenter_wave_safe(double new_x0, double sigma) {
    py::gil_scoped_release release;

    double norm = 0.0;
    std::vector<Complex> new_psi(Nx, 0.0);
    #pragma omp parallel for reduction(+:norm)
    for (int i = 0; i < Nx; ++i) {
        double x = i * dx;
        double envelope = std::exp(-0.5 * std::pow((x - new_x0) / sigma, 2));
        new_psi[i] = Complex(envelope, 0.0);
        norm += std::norm(new_psi[i]) * dx;
    }
    norm = std::sqrt(norm);

    double final_norm = 0.0;
    if(norm > 1e-15) {
        #pragma omp parallel for reduction(+:final_norm)
        for (int i = 0; i < Nx; ++i) {
            new_psi[i] /= norm;
            // v26.0: Soft Blend Contínuo (Injeção de Energia Sem Quebrar Fase)
            psi[i] = psi[i] * 0.8 + new_psi[i] * 0.2;
            final_norm += std::norm(psi[i]) * dx;
        }
    }

    final_norm = std::sqrt(final_norm);
    if(final_norm > 1e-15) {
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) psi[i] /= final_norm;
    }
    update_probability_density();
}

    void update_probability_density() {
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            double n = std::norm(psi[i]);
            prob_density[i] = (std::isfinite(n) && n > 0.0) ? n : 0.0;
        }
    }

    py::array_t<double> get_probability_density() {
        return py::array_t<double>({Nx}, {sizeof(double)}, prob_density.data(), py::cast(this));
    }

    double get_center_of_mass() {
        double com = 0.0, total = 0.0;
        #pragma omp parallel for reduction(+:com, total)
        for(int i = 0; i < Nx; ++i) { double p = prob_density[i]; com += i * dx * p; total += p; }
        return (total > 1e-15) ? (com / total) : (Nx * dx / 2.0);
    }

    py::dict calculate_singularity_metrics(double price_min, double price_max) {
        double max_p = 0.0;
        int peak_idx = 0;
        double total_mass = 0.0;
        for (int i = 0; i < Nx; ++i) {
            double p = prob_density[i];
            total_mass += p;
            if (p > max_p) { max_p = p; peak_idx = i; }
        }
        double strength = (total_mass > 1e-15) ? (max_p / total_mass) : 0.0;
        py::dict res;
        res["singularity_strength"] = strength;
        res["schwarzschild_radius"] = strength * 50.0; 
        res["peak_price"] = price_min + (peak_idx * (price_max - price_min) / Nx);
        res["is_collapsed"] = (strength > 0.04);
        return res;
    }

    double calculate_tunneling_probability(double barrier_energy, double particle_energy, double volume_mass) {
        if (particle_energy > barrier_energy) return 1.0; 
        double delta_E = std::max(0.1, barrier_energy - particle_energy);
        double effective_mass = std::max(0.01, std::log1p(volume_mass));
        double hbar_dynamic = std::max(1.0, std::sqrt(delta_E * effective_mass) / 5.0); 
        double exponent = -2.0 * std::sqrt(2.0 * effective_mass * delta_E) / hbar_dynamic;
        if (exponent < -50.0) exponent = -50.0;
        return std::exp(exponent);
    }

    double calculate_s_matrix_scattering(double in_state_energy, double out_state_energy, double vacuum_density) {
        double delta_E = std::abs(out_state_energy - in_state_energy);
        double coupling = std::max(0.001, vacuum_density);
        double amplitude = coupling / (delta_E + coupling);
        return std::min(1.0, std::pow(amplitude, 2));
    }
};

PYBIND11_MODULE(schrodinger_engine, m) {
    m.doc() = "Quantum Cloud Solver v24.1 - Institutional Attraction";
    py::class_<QuantumCloudSolver>(m, "QuantumCloudSolver")
        .def(py::init<int, double>())
        .def("initialize_gaussian", &QuantumCloudSolver::initialize_gaussian, py::arg("x0"), py::arg("sigma"), py::arg("k0"))
        .def("update_potential", &QuantumCloudSolver::update_potential, py::arg("new_V"))
        .def("update_spatial_mass", &QuantumCloudSolver::update_spatial_mass, py::arg("new_mass"))
        .def("step_forward", &QuantumCloudSolver::step_forward, py::arg("dt"), py::arg("global_mass_scale"), py::arg("hbar_val"), py::arg("drift_k")=0.0)
        .def("shift_grid", &QuantumCloudSolver::shift_grid, py::arg("steps"))
        .def("calculate_stationary_state", &QuantumCloudSolver::calculate_stationary_state, py::arg("iterations"), py::arg("hbar_val"))
        .def("recenter_wave", &QuantumCloudSolver::recenter_wave_safe, py::arg("new_x0"), py::arg("sigma"))
        .def("get_probability_density", &QuantumCloudSolver::get_probability_density, py::return_value_policy::reference_internal)
        .def("get_center_of_mass", &QuantumCloudSolver::get_center_of_mass)
        .def("calculate_singularity_metrics", &QuantumCloudSolver::calculate_singularity_metrics, py::arg("price_min"), py::arg("price_max"))
        .def("calculate_tunneling_probability", &QuantumCloudSolver::calculate_tunneling_probability, py::arg("barrier_energy"), py::arg("particle_energy"), py::arg("volume_mass"))
        .def("calculate_s_matrix_scattering", &QuantumCloudSolver::calculate_s_matrix_scattering, py::arg("in_state_energy"), py::arg("out_state_energy"), py::arg("vacuum_density"));
}
