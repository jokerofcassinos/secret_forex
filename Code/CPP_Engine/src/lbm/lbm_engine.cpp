#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <iostream>
#include <algorithm>

#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

class LBMEngine {
private:
    int Nx;
    double tau0;
    double Cs; // Constante de Smagorinsky
    std::vector<double> f0, f1, f2;
    std::vector<double> f0_new, f1_new, f2_new;
    std::vector<double> rho;
    std::vector<double> u;
    std::vector<double> pressure;
    std::vector<double> reynolds;
    std::vector<double> tau_eff;
    
    const double w0 = 4.0 / 6.0;
    const double w1 = 1.0 / 6.0;
    const double w2 = 1.0 / 6.0;
    const double cs2 = 1.0 / 3.0;
    double mass_decay;

public:
    LBMEngine(int N, double relaxation_time = 1.0, double smagorinsky_const = 0.15) 
        : Nx(N), tau0(relaxation_time), Cs(smagorinsky_const), mass_decay(0.999) {
        
        if (tau0 <= 0.5) tau0 = 0.501; // Limite termodinâmico para o LBM não explodir
        
        f0.resize(Nx, w0); f1.resize(Nx, w1); f2.resize(Nx, w2);
        f0_new.resize(Nx, 0.0); f1_new.resize(Nx, 0.0); f2_new.resize(Nx, 0.0);
        rho.resize(Nx, 1.0); u.resize(Nx, 0.0);
        pressure.resize(Nx, cs2); reynolds.resize(Nx, 0.0); tau_eff.resize(Nx, tau0);
    }

    void inject_liquidity(int idx, double volume_mass, double directional_momentum) {
        py::gil_scoped_release release;
        if(idx >= 0 && idx < Nx) {
            rho[idx] += volume_mass;
            
            // Limitador de velocidade mach (D1Q3 explode se |u| > 0.577)
            double max_u = 0.45; 
            double clamped_momentum = std::max(-max_u, std::min(max_u, directional_momentum));
            
            double total_mass = rho[idx];
            if(total_mass > 1e-9) {
                u[idx] = (u[idx] * (total_mass - volume_mass) + clamped_momentum * volume_mass) / total_mass;
            }
            
            double u2 = u[idx] * u[idx];
            f0[idx] = rho[idx] * w0 * (1.0 - u2 / (2.0 * cs2));
            f1[idx] = rho[idx] * w1 * (1.0 + u[idx] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));
            f2[idx] = rho[idx] * w2 * (1.0 - u[idx] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));
            
            if(f0[idx] < 0) f0[idx] = 0;
            if(f1[idx] < 0) f1[idx] = 0;
            if(f2[idx] < 0) f2[idx] = 0;
        }
    }

    void step() {
        py::gil_scoped_release release;

        // 1. Natural Market Decay (Dissipação institucional base)
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            f0[i] *= mass_decay;
            f1[i] *= mass_decay;
            f2[i] *= mass_decay;
        }

        // 2. Cálculo das Variáveis Macroscópicas
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            rho[i] = f0[i] + f1[i] + f2[i];
            if(rho[i] > 1e-9) {
                u[i] = (f1[i] - f2[i]) / rho[i];
                // Limite Termodinâmico de Barreira do Som LBM (Impede explosão da grade)
                u[i] = std::max(-0.45, std::min(0.45, u[i])); 
            } else {
                u[i] = 0.0; rho[i] = 1e-9;
            }
            
            // Termodinâmica ASI-5: Pressão P = \rho * c_s^2
            pressure[i] = rho[i] * cs2;
        }

        // 3. Colisão com Tempo de Relaxamento Dinâmico (Smagorinsky Subgrid Turbulence)
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            // Magnitude do Tensor de Taxa de Cisalhamento (|S|) em 1D
            double S_mag = 0.0;
            if (i > 0 && i < Nx - 1) {
                S_mag = std::abs(u[i+1] - u[i-1]) / 2.0;
            } else if (i == 0) {
                S_mag = std::abs(u[1] - u[0]);
            } else {
                S_mag = std::abs(u[Nx-1] - u[Nx-2]);
            }

            // Viscosidade Turbulenta de Smagorinsky (\nu_t)
            double nu_t = (Cs * Cs) * S_mag;
            
            // Tempo de Relaxamento Efetivo (\tau_{eff})
            double t_eff = tau0 + (nu_t / cs2);
            tau_eff[i] = t_eff;
            
            // Cálculo do Número de Reynolds Re = (|u| * L) / \nu_eff
            double nu_eff = cs2 * (t_eff - 0.5);
            reynolds[i] = (std::abs(u[i]) * 10.0) / (nu_eff + 1e-9); // L_char = 10 (escala da grade)

            // Funções de Equilíbrio
            double u2 = u[i] * u[i];
            double feq0 = rho[i] * w0 * (1.0 - u2 / (2.0 * cs2));
            double feq1 = rho[i] * w1 * (1.0 + u[i] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));
            double feq2 = rho[i] * w2 * (1.0 - u[i] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));
            
            // Colisão BGK usando \tau_{eff}
            // Clamping removido nas saídas f(x) pois causava criação irreal de massa e explosão no LBM
            f0[i] -= (1.0 / t_eff) * (f0[i] - feq0);
            f1[i] -= (1.0 / t_eff) * (f1[i] - feq1);
            f2[i] -= (1.0 / t_eff) * (f2[i] - feq2);
        }

        // 4. Propagação (Streaming Step com Bounce-Back nas bordas)
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            f0_new[i] = f0[i];
            if (i - 1 >= 0) f1_new[i] = f1[i - 1]; else f1_new[i] = f2[i]; // Bounce back
            if (i + 1 < Nx) f2_new[i] = f2[i + 1]; else f2_new[i] = f1[i]; // Bounce back
        }
        
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            f0[i] = f0_new[i];
            f1[i] = f1_new[i];
            f2[i] = f2_new[i];
        }
    }

    py::array_t<double> get_density() { return py::array_t<double>({Nx}, {sizeof(double)}, rho.data(), py::cast(this)); }
    py::array_t<double> get_velocity() { return py::array_t<double>({Nx}, {sizeof(double)}, u.data(), py::cast(this)); }
    py::array_t<double> get_pressure() { return py::array_t<double>({Nx}, {sizeof(double)}, pressure.data(), py::cast(this)); }
    py::array_t<double> get_reynolds() { return py::array_t<double>({Nx}, {sizeof(double)}, reynolds.data(), py::cast(this)); }

    double calculate_deborah_number(double anomaly_duration) {
        if (anomaly_duration <= 0.0) return 0.0;
        return tau0 / anomaly_duration;
    }
};

PYBIND11_MODULE(lbm_engine, m) {
    m.doc() = "LBM Engine v5.0 - ASI-5 Smagorinsky Subgrid Turbulence Model";
    py::class_<LBMEngine>(m, "LBMEngine")
        .def(py::init<int, double, double>(), py::arg("N"), py::arg("relaxation_time") = 1.0, py::arg("smagorinsky_const") = 0.15)
        .def("inject_liquidity", &LBMEngine::inject_liquidity)
        .def("step", &LBMEngine::step)
        .def("get_density", &LBMEngine::get_density, py::return_value_policy::reference_internal)
        .def("get_velocity", &LBMEngine::get_velocity, py::return_value_policy::reference_internal)
        .def("get_pressure", &LBMEngine::get_pressure, py::return_value_policy::reference_internal)
        .def("get_reynolds", &LBMEngine::get_reynolds, py::return_value_policy::reference_internal)
        .def("calculate_deborah_number", &LBMEngine::calculate_deborah_number, py::arg("anomaly_duration"));
}