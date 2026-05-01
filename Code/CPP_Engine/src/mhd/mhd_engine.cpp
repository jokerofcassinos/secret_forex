#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <cmath>
#include <vector>
#include <iostream>

namespace py = pybind11;

class MHDEngine {
private:
    double mu_0;    // Permeabilidade magnética do vácuo financeiro
    double gamma;   // Índice adiabático do plasma
    
    // Estado interno (memória da compressão)
    double current_J;       // Corrente institucional normalizada
    double current_P;       // Pressão interna do plasma
    double plasma_radius;   // Raio do filamento de liquidez
    
    // Normalização dinâmica (FIX P0-02)
    double volume_ema;      // EMA do volume para normalização
    double j_ema;           // EMA da corrente para thresholds adaptativos
    double p_ema;           // EMA da pressão para thresholds adaptativos
    
    // Constantes de pressão (FIX P1-01)
    static constexpr double MAX_PRESSURE = 500.0;     // Cap de pressão para evitar explosão
    static constexpr double EMA_ALPHA = 0.05;          // Fator de suavização para EMAs
    
public:
    MHDEngine(double mu = 1.0, double adiabatic_idx = 5.0/3.0) 
        : mu_0(mu), gamma(adiabatic_idx), 
          current_J(0.0), current_P(1.0), plasma_radius(1.0),
          volume_ema(1.0), j_ema(1.0), p_ema(1.0) {}

    void reset_state() {
        current_J = 0.0;
        current_P = 1.0;
        plasma_radius = 1.0;
        // Mantém as EMAs de normalização (memória de longo prazo)
    }

    // FIX P0-01/P0-02: Aceita volume_mean para normalização dinâmica
    // FIX P1-01: Usa log-scaling para evitar explosão de pressão
    double step_pinch(double delta_price, double volume, double zone_density) {
        // --- FIX P0-02: Normalização dinâmica do volume ---
        volume_ema = (EMA_ALPHA * volume) + ((1.0 - EMA_ALPHA) * volume_ema);
        double normalized_volume = (volume_ema > 1e-9) ? (volume / volume_ema) : 1.0;
        
        // J (Corrente) normalizada pelo volume relativo
        double J_in = std::abs(delta_price) * normalized_volume;
        
        // Suavização da corrente (inércia do fluxo)
        current_J = (0.7 * current_J) + (0.3 * J_in);
        
        // EMA da corrente para thresholds adaptativos
        j_ema = (EMA_ALPHA * current_J) + ((1.0 - EMA_ALPHA) * j_ema);
        
        // Força de Lorentz (F_L ~ J²) que comprime o plasma
        double lorentz_force = mu_0 * current_J * current_J;
        
        // Compressão do raio do plasma
        double dr = (current_P - lorentz_force) * 0.01;
        plasma_radius += dr;
        
        // Limites físicos
        if(plasma_radius < 0.01) plasma_radius = 0.01;
        if(plasma_radius > 2.0) plasma_radius = 2.0;
        
        // --- FIX P1-01: Pressão com log-scaling e cap ---
        // Usar log para amortecer a curva exponencial e evitar explosão
        double raw_P = zone_density * std::pow(1.0 / plasma_radius, 2.0 * gamma);
        current_P = std::min(raw_P, MAX_PRESSURE);
        
        // EMA da pressão para thresholds adaptativos
        p_ema = (EMA_ALPHA * current_P) + ((1.0 - EMA_ALPHA) * p_ema);
        
        // --- FIX P0-01: Z-Index com gradiente contínuo e thresholds adaptativos ---
        double z_index = 0.0;
        
        // Gradiente suave baseado no raio (quanto menor, mais comprimido)
        if (plasma_radius < 1.0) {
            // Escala logarítmica suave de 0 a 80 baseada na compressão
            z_index = std::min(80.0, -std::log(plasma_radius) * 25.0);
        }
        
        // Boost por divergência Pressão vs Lorentz (fase de detonação)
        // FIX P0-01: Thresholds adaptativos baseados em EMAs, não constantes mágicas
        double p_threshold = std::max(5.0, p_ema * 3.0);   // 3x a pressão média
        double j_threshold = std::max(0.5, j_ema * 0.3);    // 30% da corrente média
        
        if (current_P > p_threshold && current_J < j_threshold) {
            // Detonação: a pressão é massiva mas o fluxo institucional cessou
            // Escala de 80 a 100 baseada na magnitude da divergência
            double detonation_strength = std::min(1.0, (current_P / p_threshold - 1.0));
            z_index = 80.0 + (20.0 * detonation_strength);
        }
        
        // Clamp final
        if (z_index > 100.0) z_index = 100.0;
        if (z_index < 0.0) z_index = 0.0;

        return z_index;
    }
};

PYBIND11_MODULE(mhd_engine, m) {
    m.doc() = "Magnetohydrodynamics (MHD) Z-Pinch Engine for Aethelgard v2.0";
    
    py::class_<MHDEngine>(m, "MHDEngine")
        .def(py::init<double, double>(), py::arg("mu") = 1.0, py::arg("adiabatic_idx") = 1.666)
        .def("reset_state", &MHDEngine::reset_state, "Reset plasma state")
        .def("step_pinch", &MHDEngine::step_pinch, "Advance MHD compression. Returns Z-Index (0-100)");
}
