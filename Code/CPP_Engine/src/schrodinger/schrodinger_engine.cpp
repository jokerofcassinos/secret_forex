#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <complex>
#include <cmath>
#include <iostream>
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
    std::vector<Complex> alpha;
    std::vector<Complex> beta;
    std::vector<Complex> gamma_arr;
    int absorb_width;
    std::vector<double> absorb_profile;

    void build_absorbing_profile() {
        absorb_profile.resize(Nx, 0.0);
        for(int i = 0; i < absorb_width; ++i) {
            double frac = (double)(absorb_width - i) / (double)absorb_width;
            double strength = 50.0 * frac * frac;
            absorb_profile[i] = strength;
            absorb_profile[Nx - 1 - i] = strength;
        }
    }

public:
    QuantumCloudSolver(int N, double dx_val) : Nx(N), dx(dx_val) {
        psi.resize(Nx, 0.0); V.resize(Nx, 0.0); prob_density.resize(Nx, 0.0);
        alpha.resize(Nx, 0.0); beta.resize(Nx, 0.0); gamma_arr.resize(Nx, 0.0);
        absorb_width = std::max(5, Nx / 10);
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
        
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) prob_density[i] = std::norm(psi[i]);
    }

    void update_potential(const std::vector<double>& new_V) {
        if ((int)new_V.size() != Nx) throw std::runtime_error("Potential array size must match Nx");
        V = new_V;
    }

    void step_forward(double dt, double mass) {
        py::gil_scoped_release release;
        Complex I(0.0, 1.0);
        double hbar = 1.0;
        double r_mag = dt / (4.0 * mass * dx * dx);
        double effective_dt = dt;
        if(r_mag > 1.0) effective_dt = 0.25 * 4.0 * mass * dx * dx;
        int substeps = std::max(1, (int)std::ceil(dt / effective_dt));
        effective_dt = dt / (double)substeps;

        for(int sub = 0; sub < substeps; ++sub) {
            Complex r = (I * hbar * effective_dt) / (4.0 * mass * dx * dx);
            std::vector<Complex> d(Nx, 0.0);
            
            #pragma omp parallel for
            for (int i = 1; i < Nx - 1; ++i) {
                Complex v_complex(V[i], -absorb_profile[i]);
                Complex v_term = (I * effective_dt * v_complex) / (2.0 * hbar);
                alpha[i] = -r; beta[i] = 1.0 + 2.0 * r + v_term; gamma_arr[i] = -r;
                d[i] = r * psi[i-1] + (1.0 - 2.0 * r - v_term) * psi[i] + r * psi[i+1];
            }
            beta[0] = 1.0; d[0] = 0.0; gamma_arr[0] = 0.0;
            beta[Nx-1] = 1.0; d[Nx-1] = 0.0; alpha[Nx-1] = 0.0;

            std::vector<Complex> c_prime(Nx, 0.0), d_prime(Nx, 0.0);
            c_prime[0] = gamma_arr[0] / beta[0]; d_prime[0] = d[0] / beta[0];
            
            // Thomas Algorithm (Sequential)
            for (int i = 1; i < Nx; ++i) {
                Complex denom = beta[i] - alpha[i] * c_prime[i-1];
                if(std::abs(denom) < 1e-15) denom = Complex(1e-15, 0.0);
                Complex m_val = 1.0 / denom;
                c_prime[i] = gamma_arr[i] * m_val;
                d_prime[i] = (d[i] - alpha[i] * d_prime[i-1]) * m_val;
            }
            psi[Nx-1] = d_prime[Nx-1];
            for (int i = Nx - 2; i >= 0; --i) psi[i] = d_prime[i] - c_prime[i] * psi[i+1];
        }
        
        double norm = 0.0;
        #pragma omp parallel for reduction(+:norm)
        for (int i = 0; i < Nx; ++i) norm += std::norm(psi[i]) * dx;
        norm = std::sqrt(norm);
        
        if(norm > 1e-15) {
            #pragma omp parallel for
            for (int i = 0; i < Nx; ++i) psi[i] /= norm;
        }
        
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) prob_density[i] = std::norm(psi[i]);
    }

    void recenter_wave(double new_x0, double sigma) {
        py::gil_scoped_release release;
        double com = 0.0, total_prob = 0.0;
        
        #pragma omp parallel for reduction(+:com, total_prob)
        for(int i = 0; i < Nx; ++i) {
            double p = std::norm(psi[i]); com += i * dx * p; total_prob += p;
        }
        if(total_prob > 1e-15) com /= total_prob;
        
        if(std::abs(new_x0 - com) > sigma * 10.0) {
            // we must acquire GIL if calling another Python-exposed function? 
            // No, initialize_gaussian handles its own internal things.
            // But wait, initialize_gaussian releases GIL internally, so we shouldn't nest GIL release inside a GIL release without care.
            // However, we just call the C++ function here. The nested release in pybind11 is generally fine or can be avoided.
        }
    }
    
    // We refactor recenter_wave to avoid double gil release issues
    void recenter_wave_safe(double new_x0, double sigma) {
        double com = 0.0, total_prob = 0.0;
        for(int i = 0; i < Nx; ++i) {
            double p = std::norm(psi[i]); com += i * dx * p; total_prob += p;
        }
        if(total_prob > 1e-15) com /= total_prob;
        if(std::abs(new_x0 - com) > sigma * 10.0) {
            double norm = 0.0;
            for (int i = 0; i < Nx; ++i) {
                double x = i * dx;
                double envelope = std::exp(-0.5 * std::pow((x - new_x0) / sigma, 2));
                psi[i] = Complex(envelope, 0.0);
                norm += std::norm(psi[i]) * dx;
            }
            norm = std::sqrt(norm);
            if(norm > 1e-15) { for (int i = 0; i < Nx; ++i) psi[i] /= norm; }
            for (int i = 0; i < Nx; ++i) prob_density[i] = std::norm(psi[i]);
        }
    }

    void update_probability_density() {
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) prob_density[i] = std::norm(psi[i]);
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
            if (p > max_p) {
                max_p = p;
                peak_idx = i;
            }
        }
        
        double strength = (total_mass > 1e-15) ? (max_p / total_mass) : 0.0;
        double rs = strength * 50.0; 
        
        py::dict res;
        res["singularity_strength"] = strength;
        res["schwarzschild_radius"] = rs;
        res["peak_price"] = price_min + (peak_idx * (price_max - price_min) / Nx);
        res["is_collapsed"] = (strength > 0.04);

        return res;
    }

    double calculate_tunneling_probability(double barrier_energy, double particle_energy, double volume_mass) {
        if (particle_energy > barrier_energy) return 1.0; 
        
        // --- CALIBRAÇÃO ABSOLUTA: Constante de Planck Dinâmica ---
        // A constante de Planck não pode ser fixa (1.0) em mercados onde a energia escala em milhares.
        // Transformamos a massa bruta e as energias em razões escalares para evitar underflow extremo.
        double delta_E = std::max(0.1, barrier_energy - particle_energy);
        double effective_mass = std::max(0.01, std::log1p(volume_mass)); // Massa logarítmica
        
        // Fator de escala dinâmico (Planck Financeiro). 
        // Impede que o expoente ultrapasse limites de ponto flutuante (exp(-700) = 0)
        double hbar_dynamic = std::max(1.0, std::sqrt(delta_E * effective_mass) / 5.0); 
        
        double L = 1.0; 
        double exponent = -2.0 * L * std::sqrt(2.0 * effective_mass * delta_E) / hbar_dynamic;
        
        // Limita o expoente para evitar underflow absoluto na CPU
        if (exponent < -50.0) exponent = -50.0;
        
        return std::exp(exponent);
    }

    /**
     * @brief Calcula a Amplitude de Transição da Matriz-S (S-Matrix Scattering).
     * Mede a aniquilação de Vácuos de Dirac (antigos FVGs) como espalhamento bosônico.
     * Retorna a probabilidade da transição de estado (0.0 a 1.0).
     */
    double calculate_s_matrix_scattering(double in_state_energy, double out_state_energy, double vacuum_density) {
        // Amplitude de Transição S_fi = <out|S|in>
        // Aproximação Born para espalhamento em potencial central (Vácuo de Dirac)
        double delta_E = std::abs(out_state_energy - in_state_energy);
        
        // Se a diferença de energia for muito alta, a probabilidade de espalhamento cai (decoerência)
        // A densidade do vácuo atua como a constante de acoplamento (coupling constant)
        double coupling = std::max(0.001, vacuum_density);
        
        double amplitude = coupling / (delta_E + coupling);
        
        // A probabilidade de aniquilação é a amplitude ao quadrado (Regra de Born)
        double annihilation_prob = std::pow(amplitude, 2);
        
        return std::min(1.0, annihilation_prob);
    }
};

PYBIND11_MODULE(schrodinger_engine, m) {
    m.doc() = "Quantum Cloud Solver v5.0 - Holographic Principle & S-Matrix Scattering";
    py::class_<QuantumCloudSolver>(m, "QuantumCloudSolver")
        .def(py::init<int, double>())
        .def("initialize_gaussian", &QuantumCloudSolver::initialize_gaussian, py::arg("x0"), py::arg("sigma"), py::arg("k0"))
        .def("update_potential", &QuantumCloudSolver::update_potential, py::arg("new_V"))
        .def("step_forward", &QuantumCloudSolver::step_forward, py::arg("dt"), py::arg("mass"))
        .def("recenter_wave", &QuantumCloudSolver::recenter_wave_safe, py::arg("new_x0"), py::arg("sigma"))
        .def("get_probability_density", &QuantumCloudSolver::get_probability_density, py::return_value_policy::reference_internal)
        .def("get_center_of_mass", &QuantumCloudSolver::get_center_of_mass)
        .def("calculate_singularity_metrics", &QuantumCloudSolver::calculate_singularity_metrics, py::arg("price_min"), py::arg("price_max"))
        .def("calculate_tunneling_probability", &QuantumCloudSolver::calculate_tunneling_probability, py::arg("barrier_energy"), py::arg("particle_energy"), py::arg("volume_mass"))
        .def("calculate_s_matrix_scattering", &QuantumCloudSolver::calculate_s_matrix_scattering, py::arg("in_state_energy"), py::arg("out_state_energy"), py::arg("vacuum_density"));
}