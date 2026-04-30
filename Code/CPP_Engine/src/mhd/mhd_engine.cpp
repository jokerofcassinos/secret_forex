#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
#include <iostream>

namespace py = pybind11;

class MHDEngine {
private:
    double mu_0; // Permeabilidade magnética do vácuo financeiro (constante de ajuste)
    double gamma; // Índice adiabático do plasma
    
    // Estado interno (memória da compressão)
    double current_J; // Corrente institucional (Momentum de volume direcional)
    double current_P; // Pressão interna do plasma (Resistência da zona de liquidez)
    double plasma_radius; // "Raio" do filamento (distância percorrida dentro da zona de liquidez)
    
public:
    MHDEngine(double mu = 1.0, double adiabatic_idx = 5.0/3.0) 
        : mu_0(mu), gamma(adiabatic_idx), current_J(0.0), current_P(1.0), plasma_radius(1.0) {}

    // Reseta o estado quando entramos em um novo regime ou saímos da zona
    void reset_state() {
        current_J = 0.0;
        current_P = 1.0;
        plasma_radius = 1.0;
    }

    // Avança 1 ciclo (1 tick ou candle) dentro da zona de liquidez
    // Retorna o Índice de Compressão Z-Pinch (0 a 100)
    double step_pinch(double delta_price, double volume, double zone_density) {
        // J (Corrente) é análogo à força da agressão. 
        // Agressão rápida = alta corrente.
        double J_in = std::abs(delta_price) * volume * 0.001; 
        
        // Suavização da corrente (inércia do fluxo)
        current_J = (0.7 * current_J) + (0.3 * J_in);
        
        // Força de Lorentz (F_L ~ J^2) que comprime o plasma
        double lorentz_force = mu_0 * current_J * current_J;
        
        // Compressão do raio do plasma
        // Se a força de Lorentz for maior que a pressão, o raio diminui (esmagamento)
        double dr = (current_P - lorentz_force) * 0.01; // Taxa de compressão
        plasma_radius += dr;
        
        // Limites físicos (não pode esmagar até zero, nem expandir infinito em 1 tick)
        if(plasma_radius < 0.01) plasma_radius = 0.01;
        if(plasma_radius > 2.0) plasma_radius = 2.0;
        
        // Aumento da Pressão interna devido à compressão adiabática: P * V^gamma = const
        // Como o volume V ~ radius^2 (aproximação cilíndrica 2D), P ~ 1 / (radius^(2*gamma))
        // Adicionamos a densidade base da zona (zone_density)
        current_P = zone_density * std::pow(1.0 / plasma_radius, 2.0 * gamma);
        
        // Cálculo do Z-Index (Quão perto estamos da ruptura)
        // Quando lorentz_force é massiva, radius cai para ~0.01, e P explode.
        // O pinch máximo (Z-Pinch) ocorre quando P reage instantaneamente contra a força.
        double z_index = 0.0;
        if (plasma_radius < 0.1) {
             // Raio muito pequeno = Alta compressão. Escalar de 0 a 100.
             z_index = (0.1 - plasma_radius) * 1000.0; 
        }
        
        if (z_index > 100.0) z_index = 100.0;
        
        // Se o fluxo institucional (J) cair de repente enquanto a pressão (P) está muito alta,
        // a força de Lorentz some e ocorre a explosão (reversão violenta).
        if (current_P > 50.0 && current_J < 5.0) {
             z_index = 100.0; // Detonação instantânea confirmada
        }

        return z_index;
    }
};

PYBIND11_MODULE(mhd_engine, m) {
    m.doc() = "Magnetohydrodynamics (MHD) Z-Pinch Engine for Aethelgard";
    
    py::class_<MHDEngine>(m, "MHDEngine")
        .def(py::init<double, double>(), py::arg("mu") = 1.0, py::arg("adiabatic_idx") = 1.666)
        .def("reset_state", &MHDEngine::reset_state, "Reset plasma state")
        .def("step_pinch", &MHDEngine::step_pinch, "Advance MHD compression. Returns Z-Index (0-100)");
}
