#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace py = pybind11;

/**
 * QHO ENGINE (Quantum Harmonic Oscillator)
 * Modela a reversão à média como estados de energia quantizados.
 */
class QHOEngine {
public:
    QHOEngine() {}

    /**
     * Calcula o Polinômio de Hermite H_n(x) recursivamente.
     */
    double hermite(int n, double x) {
        if (n == 0) return 1.0;
        if (n == 1) return 2.0 * x;
        
        double h0 = 1.0;
        double h1 = 2.0 * x;
        double h_n = 0.0;
        
        for (int i = 2; i <= n; ++i) {
            h_n = 2.0 * x * h1 - 2.0 * (i - 1) * h0;
            h0 = h1;
            h1 = h_n;
        }
        return h1;
    }

    /**
     * Calcula a Função de Onda psi_n(x) para o oscilador harmônico.
     * x é a distância normalizada do Fair Value.
     */
    double calculate_wavefunction(int n, double x) {
        double normalization = 1.0 / std::sqrt(std::pow(2.0, n) * tgamma(n + 1) * std::sqrt(M_PI));
        return normalization * std::exp(-x * x / 2.0) * hermite(n, x);
    }

    /**
     * Determina o Nível de Energia Quantizado (n) atual baseado na distância z-score.
     */
    int estimate_energy_level(double z_score) {
        // No QHO, a energia é proporcional ao quadrado da distância
        // E = (n + 1/2) * h_bar * omega
        double energy = 0.5 * z_score * z_score;
        int n = static_cast<int>(std::floor(energy));
        return std::max(0, n);
    }

    /**
     * Calcula a Probabilidade de Estabilidade (Fidelidade ao Estado n=0)
     */
    double calculate_stability_score(double z_score) {
        double psi0 = calculate_wavefunction(0, z_score);
        return std::clamp(psi0 * psi0 * std::sqrt(M_PI), 0.0, 1.0);
    }
};

PYBIND11_MODULE(qho_engine, m) {
    py::class_<QHOEngine>(m, "QHOEngine")
        .def(py::init<>())
        .def("calculate_wavefunction", &QHOEngine::calculate_wavefunction)
        .def("estimate_energy_level", &QHOEngine::estimate_energy_level)
        .def("calculate_stability_score", &QHOEngine::calculate_stability_score);
}
