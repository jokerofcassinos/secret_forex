#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <iostream>

namespace py = pybind11;

class LBMEngine {
private:
    int Nx; // Tamanho da malha (bins de preço)
    double tau; // Tempo de relaxação (Viscosidade cinemática)
    
    // Matrizes de Distribuição: f_i (i = 0, 1, 2)
    // 0: Parado, 1: Direita (Bull), 2: Esquerda (Bear)
    std::vector<double> f0, f1, f2;
    std::vector<double> f0_new, f1_new, f2_new;
    
    // Variáveis macroscópicas
    std::vector<double> rho; // Densidade (Volume termodinâmico)
    std::vector<double> u;   // Velocidade (Agressão de Momentum)

    // Pesos da rede D1Q3
    const double w0 = 4.0 / 6.0;
    const double w1 = 1.0 / 6.0;
    const double w2 = 1.0 / 6.0;
    const double cs2 = 1.0 / 3.0; // Velocidade do som ao quadrado

public:
    LBMEngine(int N, double relaxation_time) : Nx(N), tau(relaxation_time) {
        f0.resize(Nx, w0); f1.resize(Nx, w1); f2.resize(Nx, w2);
        f0_new.resize(Nx, 0.0); f1_new.resize(Nx, 0.0); f2_new.resize(Nx, 0.0);
        rho.resize(Nx, 1.0); u.resize(Nx, 0.0);
    }

    // N-Core Injeta Liquidez Bruta
    void inject_liquidity(int idx, double volume_mass, double directional_momentum) {
        if(idx >= 0 && idx < Nx) {
            rho[idx] += volume_mass;
            u[idx] = directional_momentum; // Positivo para Bull, Negativo para Bear
            
            // Recalcula o equilíbrio imediato após injeção
            double u2 = u[idx] * u[idx];
            f0[idx] = rho[idx] * w0 * (1.0 - u2 / (2.0 * cs2));
            f1[idx] = rho[idx] * w1 * (1.0 + u[idx] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));
            f2[idx] = rho[idx] * w2 * (1.0 - u[idx] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));
        }
    }

    // Avança 1 ciclo termodinâmico da Grade D1Q3 (Colisão -> Streaming)
    void step() {
        // Passo 1: Colisão (BGK Approximation) e Cálculo Macroscópico
        for (int i = 0; i < Nx; ++i) {
            rho[i] = f0[i] + f1[i] + f2[i];
            // Evitar divisão por zero se o grid secar totalmente
            if(rho[i] > 1e-9) {
                u[i] = (f1[i] - f2[i]) / rho[i];
            } else {
                u[i] = 0.0;
            }

            double u2 = u[i] * u[i];
            
            // Distribuição de Equilíbrio
            double feq0 = rho[i] * w0 * (1.0 - u2 / (2.0 * cs2));
            double feq1 = rho[i] * w1 * (1.0 + u[i] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));
            double feq2 = rho[i] * w2 * (1.0 - u[i] / cs2 + u2 / (2.0 * cs2 * cs2) - u2 / (2.0 * cs2));

            // Relaxamento BGK
            f0[i] = f0[i] - (1.0 / tau) * (f0[i] - feq0);
            f1[i] = f1[i] - (1.0 / tau) * (f1[i] - feq1);
            f2[i] = f2[i] - (1.0 / tau) * (f2[i] - feq2);
        }

        // Passo 2: Streaming (Propagação Vetorial das Ordens)
        for (int i = 0; i < Nx; ++i) {
            f0_new[i] = f0[i]; // Ordens Limit (paradas)

            // Streaming Direita (Agressão Compra)
            if (i - 1 >= 0) f1_new[i] = f1[i - 1]; 
            else f1_new[i] = f2[i]; // Bounce boundary

            // Streaming Esquerda (Agressão Venda)
            if (i + 1 < Nx) f2_new[i] = f2[i + 1];
            else f2_new[i] = f1[i]; // Bounce boundary
        }

        // Troca ponteiros / Copia de volta
        f0 = f0_new; f1 = f1_new; f2 = f2_new;
    }

    // Acesso Zero-Copy das Variáveis Macroscópicas
    py::array_t<double> get_density() {
        return py::array_t<double>({Nx}, {sizeof(double)}, rho.data(), py::cast(this));
    }

    py::array_t<double> get_velocity() {
        return py::array_t<double>({Nx}, {sizeof(double)}, u.data(), py::cast(this));
    }
};

PYBIND11_MODULE(lbm_engine, m) {
    m.doc() = "Lattice Boltzmann Method Fluid Dynamics Engine for Aethelgard";
    
    py::class_<LBMEngine>(m, "LBMEngine")
        .def(py::init<int, double>())
        .def("inject_liquidity", &LBMEngine::inject_liquidity, "Inject Mass and Momentum")
        .def("step", &LBMEngine::step, "Advance 1 BGK Collision/Streaming cycle")
        .def("get_density", &LBMEngine::get_density, py::return_value_policy::reference_internal)
        .def("get_velocity", &LBMEngine::get_velocity, py::return_value_policy::reference_internal);
}
