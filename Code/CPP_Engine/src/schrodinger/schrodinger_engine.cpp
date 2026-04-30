#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <complex>
#include <cmath>
#include <iostream>

namespace py = pybind11;

using Complex = std::complex<double>;

class QuantumCloudSolver {
private:
    int Nx;
    double dx;
    std::vector<Complex> psi;
    std::vector<double> V;
    std::vector<double> prob_density;
    
    // Arrays para o Algoritmo de Thomas (Tridiagonal Matrix Algorithm)
    std::vector<Complex> alpha;
    std::vector<Complex> beta;
    std::vector<Complex> gamma;

public:
    QuantumCloudSolver(int N, double dx_val) : Nx(N), dx(dx_val) {
        psi.resize(Nx, 0.0);
        V.resize(Nx, 0.0);
        prob_density.resize(Nx, 0.0);
        
        alpha.resize(Nx, 0.0);
        beta.resize(Nx, 0.0);
        gamma.resize(Nx, 0.0);
    }

    // Inicializar pacote de ondas Gaussiano
    void initialize_gaussian(double x0, double sigma, double k0) {
        double norm = 0.0;
        for (int i = 0; i < Nx; ++i) {
            double x = i * dx;
            double envelope = std::exp(-0.5 * std::pow((x - x0) / sigma, 2));
            psi[i] = Complex(envelope * std::cos(k0 * x), envelope * std::sin(k0 * x));
            norm += std::norm(psi[i]) * dx;
        }
        
        // Normalização
        norm = std::sqrt(norm);
        for (int i = 0; i < Nx; ++i) {
            psi[i] /= norm;
        }
        update_probability_density();
    }

    void update_potential(const std::vector<double>& new_V) {
        if (new_V.size() != Nx) {
            throw std::runtime_error("Potential array size must match Nx");
        }
        V = new_V;
    }

    // Avançar um passo no tempo usando Crank-Nicolson
    void step_forward(double dt, double mass) {
        Complex I(0.0, 1.0);
        double hbar = 1.0; // Usaremos unidades naturais financeiras
        
        // Constantes da equação discretizada
        Complex r = (I * hbar * dt) / (4.0 * mass * dx * dx);
        
        std::vector<Complex> d(Nx, 0.0);
        
        // Montar os vetores para o sistema tridiagonal: A * psi_next = B * psi_current
        for (int i = 1; i < Nx - 1; ++i) {
            Complex v_term = (I * dt * V[i]) / (2.0 * hbar);
            
            // Matriz A (Lado Esquerdo)
            alpha[i] = -r; // Subdiagonal
            beta[i]  = 1.0 + 2.0 * r + v_term; // Diagonal principal
            gamma[i] = -r; // Superdiagonal
            
            // Matriz B * Psi (Lado Direito)
            d[i] = r * psi[i-1] + (1.0 - 2.0 * r - v_term) * psi[i] + r * psi[i+1];
        }
        
        // Condições de contorno de Dirichlet (psi = 0 nas bordas)
        beta[0] = 1.0; d[0] = 0.0; gamma[0] = 0.0;
        beta[Nx-1] = 1.0; d[Nx-1] = 0.0; alpha[Nx-1] = 0.0;
        
        // --- Algoritmo de Thomas (TDMA) ---
        std::vector<Complex> c_prime(Nx, 0.0);
        std::vector<Complex> d_prime(Nx, 0.0);
        
        // Forward sweep
        c_prime[0] = gamma[0] / beta[0];
        d_prime[0] = d[0] / beta[0];
        
        for (int i = 1; i < Nx; ++i) {
            Complex m = 1.0 / (beta[i] - alpha[i] * c_prime[i-1]);
            c_prime[i] = gamma[i] * m;
            d_prime[i] = (d[i] - alpha[i] * d_prime[i-1]) * m;
        }
        
        // Back substitution
        psi[Nx-1] = d_prime[Nx-1];
        for (int i = Nx - 2; i >= 0; --i) {
            psi[i] = d_prime[i] - c_prime[i] * psi[i+1];
        }
        
        update_probability_density();
    }

    void update_probability_density() {
        for (int i = 0; i < Nx; ++i) {
            prob_density[i] = std::norm(psi[i]); // norm retorna magnitude ao quadrado
        }
    }

    // Zero-Copy access from Python
    py::array_t<double> get_probability_density() {
        return py::array_t<double>(
            {Nx},
            {sizeof(double)},
            prob_density.data(),
            py::cast(this) // Referência de propriedade para evitar GC
        );
    }
};

PYBIND11_MODULE(schrodinger_engine, m) {
    m.doc() = "Quantum Cloud Solver for Aethelgard";
    
    py::class_<QuantumCloudSolver>(m, "QuantumCloudSolver")
        .def(py::init<int, double>())
        .def("initialize_gaussian", &QuantumCloudSolver::initialize_gaussian, "Init Gaussian wave packet")
        .def("update_potential", &QuantumCloudSolver::update_potential, "Update Potential V(x)")
        .def("step_forward", &QuantumCloudSolver::step_forward, "Advance 1 time step")
        .def("get_probability_density", &QuantumCloudSolver::get_probability_density, py::return_value_policy::reference_internal);
}
