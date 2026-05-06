#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <iostream>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

class LBMEngine {
private:
    int Nx;
    double tau;
    std::vector<double> f0, f1, f2;
    std::vector<double> f0_new, f1_new, f2_new;
    std::vector<double> rho;
    std::vector<double> u;
    const double w0 = 4.0 / 6.0;
    const double w1 = 1.0 / 6.0;
    const double w2 = 1.0 / 6.0;
    const double cs2 = 1.0 / 3.0;
    double mass_decay;

public:
    LBMEngine(int N, double relaxation_time = 1.0) : Nx(N), tau(relaxation_time), mass_decay(0.995) {
        if(tau < 0.501) tau = 0.501;
        if(tau < 1.0) {
            std::cout << "[LBM] WARNING: tau=" << tau << " is in over-relaxation zone. Recommend tau>=1.0" << std::endl;
        }
        f0.resize(Nx, w0); f1.resize(Nx, w1); f2.resize(Nx, w2);
        f0_new.resize(Nx, 0.0); f1_new.resize(Nx, 0.0); f2_new.resize(Nx, 0.0);
        rho.resize(Nx, 1.0); u.resize(Nx, 0.0);
    }

    void inject_liquidity(int idx, double volume_mass, double directional_momentum) {
        py::gil_scoped_release release;
        if(idx >= 0 && idx < Nx) {
            rho[idx] += volume_mass;
            double max_u = 0.3; 
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

        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            f0[i] *= mass_decay;
            f1[i] *= mass_decay;
            f2[i] *= mass_decay;
        }

        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            rho[i] = f0[i] + f1[i] + f2[i];
            if(rho[i] > 1e-9) {
                u[i] = (f1[i] - f2[i]) / rho[i];
            } else {
                u[i] = 0.0; rho[i] = 1e-9;
            }
            double u2 = u[i] * u[i];
            double feq0 = rho[i] * w0 * (1.0 - u2 / (2.0 * cs2));
            double feq1 = rho[i] * w1 * (1.0 + u[i] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));
            double feq2 = rho[i] * w2 * (1.0 - u[i] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));
            f0[i] = f0[i] - (1.0 / tau) * (f0[i] - feq0);
            f1[i] = f1[i] - (1.0 / tau) * (f1[i] - feq1);
            f2[i] = f2[i] - (1.0 / tau) * (f2[i] - feq2);
            if(f0[i] < 0) f0[i] = 0;
            if(f1[i] < 0) f1[i] = 0;
            if(f2[i] < 0) f2[i] = 0;
        }

        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            f0_new[i] = f0[i];
            if (i - 1 >= 0) f1_new[i] = f1[i - 1]; else f1_new[i] = f2[i];
            if (i + 1 < Nx) f2_new[i] = f2[i + 1]; else f2_new[i] = f1[i];
        }
        
        // Cópia paralela
        #pragma omp parallel for
        for (int i = 0; i < Nx; ++i) {
            f0[i] = f0_new[i];
            f1[i] = f1_new[i];
            f2[i] = f2_new[i];
        }
    }

    py::array_t<double> get_density() {
        return py::array_t<double>({Nx}, {sizeof(double)}, rho.data(), py::cast(this));
    }
    
    py::array_t<double> get_velocity() {
        return py::array_t<double>({Nx}, {sizeof(double)}, u.data(), py::cast(this));
    }

    double calculate_deborah_number(double anomaly_duration) {
        if (anomaly_duration <= 0.0) return 0.0;
        return tau / anomaly_duration;
    }

    bool is_viscoelastic_absorption(double anomaly_duration) {
        double De = calculate_deborah_number(anomaly_duration);
        return (De > 1.2); 
    }
};

PYBIND11_MODULE(lbm_engine, m) {
    m.doc() = "Lattice Boltzmann Method v3.0 - Viscoelastic Fluid Dynamics Engine (OpenMP)";
    py::class_<LBMEngine>(m, "LBMEngine")
        .def(py::init<int, double>(), py::arg("N"), py::arg("relaxation_time") = 1.0)
        .def("inject_liquidity", &LBMEngine::inject_liquidity)
        .def("step", &LBMEngine::step)
        .def("get_density", &LBMEngine::get_density, py::return_value_policy::reference_internal)
        .def("get_velocity", &LBMEngine::get_velocity, py::return_value_policy::reference_internal)
        .def("calculate_deborah_number", &LBMEngine::calculate_deborah_number, py::arg("anomaly_duration"))
        .def("is_viscoelastic_absorption", &LBMEngine::is_viscoelastic_absorption, py::arg("anomaly_duration"));
}