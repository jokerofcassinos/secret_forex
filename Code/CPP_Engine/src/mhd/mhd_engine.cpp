#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <omp.h>

namespace py = pybind11;

/**
 * @brief Ideal MHD Engine - Aethelgard Ph.D. Edition
 * Modela o mercado como um Plasma Magnetizado.
 * Preço = Velocidade do Fluido (v)
 * Volume/Momentum = Campo Magnético (B)
 */
class MHDIdealEngine {
private:
    int grid_size;
    double mu_0;
    double eta; // Resistividade magnética (baixa para regime ideal)
    
    std::vector<double> B_field;  // Campo Magnético (T)
    std::vector<double> V_field;  // Velocidade do Fluido (m/s)
    std::vector<double> density;  // Densidade de Massa (kg/m^3)
    std::vector<double> pressure; // Pressão Térmica (Pa)

public:
    MHDIdealEngine(int size = 128, double mu = 1.0, double resistivity = 1e-5) 
        : grid_size(size), mu_0(mu), eta(resistivity) {
        B_field.assign(grid_size, 0.01);
        V_field.assign(grid_size, 0.0);
        density.assign(grid_size, 1.0);
        pressure.assign(grid_size, 1.0);
    }

    void reset_state() {
        std::fill(B_field.begin(), B_field.end(), 0.01);
        std::fill(V_field.begin(), V_field.end(), 0.0);
        std::fill(density.begin(), density.end(), 1.0);
        std::fill(pressure.begin(), pressure.end(), 1.0);
    }

    /**
     * @brief Injeta dados de mercado na malha de plasma.
     * @param price_norm Preço normalizado (0.0 a 1.0) dentro da zona.
     * @param v_inst Velocidade instantânea (delta_price).
     * @param b_inst Intensidade magnética instantânea (volume).
     * @param p_inst Pressão térmica instantânea (ATR/Volatilidade).
     */
    void inject_flux(double price_norm, double v_inst, double b_inst, double p_inst) {
        int idx = static_cast<int>(price_norm * (grid_size - 1));
        idx = std::max(0, std::min(grid_size - 1, idx));

        #pragma omp parallel for
        for (int i = 0; i < grid_size; ++i) {
            double dist = std::abs(i - idx);
            double kernel = std::exp(- (dist * dist) / 8.0); // Gaussiana de influência
            
            V_field[i] = (0.85 * V_field[i]) + (0.15 * v_inst * kernel);
            B_field[i] = (0.85 * B_field[i]) + (0.15 * b_inst * kernel);
            pressure[i] = (0.9 * pressure[i]) + (0.1 * p_inst * kernel);
            density[i] = (0.95 * density[i]) + (0.05 * std::abs(b_inst) * kernel);
        }
    }

    struct MHDState {
        double magnetic_stability;
        bool magnetic_reconnection;
        double avg_beta;
        double max_alfven_velocity;
        double magnetic_pressure;
        double magnetic_tension;
        std::vector<double> b_grid;
    };

    /**
     * @brief Resolve a Equação de Indução e calcula métricas de plasma.
     * dB/dt = curl(v x B) + eta * laplacian(B)
     */
    MHDState evolve(double dt) {
        std::vector<double> new_B = B_field;
        bool reconnection = false;
        double total_stability = 0.0;
        double total_beta = 0.0;
        double max_vA = 0.0;
        double total_p_mag = 0.0;
        double max_tension = 0.0;
        
        double dx = 1.0 / grid_size;

        #pragma omp parallel for reduction(+:total_stability, total_beta, total_p_mag) reduction(max:max_vA, max_tension)
        for (int i = 1; i < grid_size - 1; ++i) {
            // 1. Equação de Indução (Simplificação 1D Advectiva-Difusiva)
            // dB/dt = - d(vB)/dx + eta * d^2B/dx^2
            double advection = - (V_field[i+1]*B_field[i+1] - V_field[i-1]*B_field[i-1]) / (2.0 * dx);
            double diffusion = eta * (B_field[i+1] - 2.0*B_field[i] + B_field[i-1]) / (dx * dx);
            
            new_B[i] = B_field[i] + dt * (advection + diffusion);

            // 2. Pressão Magnética: P_mag = B^2 / 2mu_0
            double p_mag = (B_field[i] * B_field[i]) / (2.0 * mu_0 + 1e-9);
            total_p_mag += p_mag;

            // 3. Tensão Magnética (Força de Lorentz component): (B . grad) B
            double tension = std::abs(B_field[i] * (B_field[i+1] - B_field[i-1]) / (2.0 * dx));
            if (tension > max_tension) max_tension = tension;

            // 4. Plasma Beta: beta = P_thermal / P_mag
            double beta = pressure[i] / (p_mag + 1e-9);
            total_beta += beta;

            // 5. Velocidade de Alfvén: v_A = B / sqrt(mu_0 * rho)
            double v_A = std::abs(B_field[i]) / std::sqrt(mu_0 * density[i] + 1e-9);
            if (v_A > max_vA) max_vA = v_A;

            // 6. Detecção de Reconexão Magnética (X-Points)
            // Identificada por inversão abrupta de campo ou singularidade de corrente
            if (B_field[i] * B_field[i-1] < -0.01 || B_field[i] * B_field[i+1] < -0.01) {
                #pragma omp critical
                reconnection = true;
            }

            // 7. Estabilidade (Inversa da Taxa de Variação de Entropia Magnética)
            total_stability += 1.0 / (1.0 + std::abs(advection) + std::abs(diffusion));
        }

        B_field = new_B;

        MHDState state;
        state.magnetic_stability = (total_stability / (grid_size - 2)) * 100.0;
        state.magnetic_reconnection = reconnection;
        state.avg_beta = total_beta / (grid_size - 2);
        state.max_alfven_velocity = max_vA;
        state.magnetic_pressure = total_p_mag / (grid_size - 2);
        state.magnetic_tension = max_tension;
        state.b_grid = B_field;

        return state;
    }
};

PYBIND11_MODULE(mhd_engine, m) {
    m.doc() = "Aethelgard MHD Ideal Engine - Ph.D. Level Solver";

    py::class_<MHDIdealEngine::MHDState>(m, "MHDState")
        .def_readonly("magnetic_stability", &MHDIdealEngine::MHDState::magnetic_stability)
        .def_readonly("magnetic_reconnection", &MHDIdealEngine::MHDState::magnetic_reconnection)
        .def_readonly("avg_beta", &MHDIdealEngine::MHDState::avg_beta)
        .def_readonly("max_alfven_velocity", &MHDIdealEngine::MHDState::max_alfven_velocity)
        .def_readonly("magnetic_pressure", &MHDIdealEngine::MHDState::magnetic_pressure)
        .def_readonly("magnetic_tension", &MHDIdealEngine::MHDState::magnetic_tension)
        .def_readonly("b_grid", &MHDIdealEngine::MHDState::b_grid);

    py::class_<MHDIdealEngine>(m, "MHDIdealEngine")
        .def(py::init<int, double, double>(), py::arg("size") = 128, py::arg("mu") = 1.0, py::arg("resistivity") = 1e-5)
        .def("reset_state", &MHDIdealEngine::reset_state)
        .def("inject_flux", &MHDIdealEngine::inject_flux)
        .def("evolve", &MHDIdealEngine::evolve);
}
