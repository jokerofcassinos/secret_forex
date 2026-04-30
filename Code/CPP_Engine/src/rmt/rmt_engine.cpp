#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <iostream>
#include <stdexcept>

namespace py = pybind11;

class RMTEngine {
private:
    int N; // Número de Features (Séries Temporais)
    int T; // Número de Observações no tempo
    std::vector<std::vector<double>> data_matrix;
    std::vector<std::vector<double>> covariance_matrix;
    
public:
    RMTEngine(int features, int time_steps) : N(features), T(time_steps) {
        if (N <= 0 || T <= 0) throw std::invalid_argument("Dimensões devem ser positivas.");
        data_matrix.resize(N, std::vector<double>(T, 0.0));
        covariance_matrix.resize(N, std::vector<double>(N, 0.0));
    }

    // Carrega dados da matriz numpy 2D (Features x Time)
    void load_data(py::array_t<double> input_data) {
        py::buffer_info buf = input_data.request();
        if (buf.ndim != 2 || buf.shape[0] != N || buf.shape[1] != T) {
            throw std::runtime_error("Formato de array numpy incompatível.");
        }

        double *ptr = static_cast<double *>(buf.ptr);
        for (int i = 0; i < N; ++i) {
            // Normalização Z-Score (Média 0, Desvio 1) por série para RMT
            double sum = 0.0, sq_sum = 0.0;
            for (int t = 0; t < T; ++t) {
                double val = ptr[i * T + t];
                data_matrix[i][t] = val;
                sum += val;
            }
            double mean = sum / T;
            for (int t = 0; t < T; ++t) {
                double val = data_matrix[i][t];
                sq_sum += (val - mean) * (val - mean);
            }
            double std_dev = std::sqrt(sq_sum / (T - 1) + 1e-12);
            
            for (int t = 0; t < T; ++t) {
                data_matrix[i][t] = (data_matrix[i][t] - mean) / std_dev;
            }
        }
    }

    // Calcula a Matriz de Covariância C = (1/T) * X * X^T
    void compute_covariance() {
        for (int i = 0; i < N; ++i) {
            for (int j = i; j < N; ++j) { // Simétrica
                double cov = 0.0;
                for (int t = 0; t < T; ++t) {
                    cov += data_matrix[i][t] * data_matrix[j][t];
                }
                cov /= T;
                covariance_matrix[i][j] = cov;
                covariance_matrix[j][i] = cov;
            }
        }
    }

    // Método da Potência para extrair o Autovalor Dominante (Assinatura Institucional)
    // Retorna [Eigenvalue, Signal_Power_Ratio]
    std::vector<double> extract_dominant_eigenvalue(int max_iterations = 1000, double tol = 1e-9) {
        compute_covariance();
        
        std::vector<double> v(N, 1.0 / std::sqrt(N)); // Vetor inicial unitário
        std::vector<double> v_new(N, 0.0);
        double lambda = 0.0, prev_lambda = 0.0;

        for (int iter = 0; iter < max_iterations; ++iter) {
            // Multiplicação Matriz-Vetor: v_new = C * v
            double norm = 0.0;
            for (int i = 0; i < N; ++i) {
                v_new[i] = 0.0;
                for (int j = 0; j < N; ++j) {
                    v_new[i] += covariance_matrix[i][j] * v[j];
                }
                norm += v_new[i] * v_new[i];
            }
            norm = std::sqrt(norm);
            
            // Normaliza v_new e calcula Quociente de Rayleigh (lambda)
            lambda = 0.0;
            for (int i = 0; i < N; ++i) {
                v_new[i] /= norm;
                double temp = 0.0;
                for (int j = 0; j < N; ++j) {
                    temp += covariance_matrix[i][j] * v_new[j];
                }
                lambda += v_new[i] * temp;
            }

            if (std::abs(lambda - prev_lambda) < tol) break;
            prev_lambda = lambda;
            v = v_new;
        }

        // --- Marchenko-Pastur Limites Teóricos ---
        // Q = T/N. Limite Superior do Ruído Aleatório
        double Q = (double)T / (double)N;
        double lambda_max_mp = 1.0 + (1.0 / Q) + 2.0 * std::sqrt(1.0 / Q);
        
        // Signal Power Ratio = Quão mais forte o Institucional está em relação ao ruído máximo
        double signal_power = lambda / lambda_max_mp;

        return {lambda, signal_power, lambda_max_mp};
    }
};

PYBIND11_MODULE(rmt_engine, m) {
    m.doc() = "Random Matrix Theory (RMT) Eigen-Decomposition Engine";
    
    py::class_<RMTEngine>(m, "RMTEngine")
        .def(py::init<int, int>())
        .def("load_data", &RMTEngine::load_data, "Load 2D Feature Matrix")
        .def("extract_dominant_eigenvalue", &RMTEngine::extract_dominant_eigenvalue, 
             py::arg("max_iterations") = 1000, py::arg("tol") = 1e-9, 
             "Compute Principal Component Energy");
}
