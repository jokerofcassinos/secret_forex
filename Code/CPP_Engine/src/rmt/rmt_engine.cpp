#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <algorithm>

namespace py = pybind11;

class RMTEngine {
private:
    int N; // Número de Features (Séries Temporais)
    int T; // Número de Observações no tempo
    std::vector<std::vector<double>> data_matrix;
    std::vector<std::vector<double>> correlation_matrix;
    std::vector<double> eigenvalues;
    std::vector<std::vector<double>> eigenvectors;
    
public:
    RMTEngine(int features, int time_steps) : N(features), T(time_steps) {
        if (N <= 0 || T <= 0) throw std::invalid_argument("Dimensões devem ser positivas.");
        data_matrix.resize(N, std::vector<double>(T, 0.0));
        correlation_matrix.resize(N, std::vector<double>(N, 0.0));
        eigenvalues.resize(N, 0.0);
        eigenvectors.resize(N, std::vector<double>(N, 0.0));
    }

    void load_data(py::array_t<double> input_data) {
        py::buffer_info buf = input_data.request();
        if (buf.ndim != 2 || buf.shape[0] != N || buf.shape[1] != T) {
            throw std::runtime_error("Formato de array numpy incompatível.");
        }

        double *ptr = static_cast<double *>(buf.ptr);
        for (int i = 0; i < N; ++i) {
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

    void compute_correlation() {
        #pragma omp parallel for collapse(2)
        for (int i = 0; i < N; ++i) {
            for (int j = 0; j < N; ++j) {
                double cov = 0.0;
                for (int t = 0; t < T; ++t) {
                    cov += data_matrix[i][t] * data_matrix[j][t];
                }
                correlation_matrix[i][j] = cov / T;
            }
        }
    }

    // Jacobi Eigenvalue Algorithm for symmetric matrices
    void jacobi_decomposition(int max_iter = 1000) {
        std::vector<std::vector<double>> A = correlation_matrix;
        
        for (int i = 0; i < N; i++) {
            for (int j = 0; j < N; j++) {
                eigenvectors[i][j] = (i == j) ? 1.0 : 0.0;
            }
        }

        int iters = 0;
        double state = N; // Tolerance state
        
        while (state > 0 && iters < max_iter) {
            state = 0;
            for (int p = 0; p < N - 1; p++) {
                for (int q = p + 1; q < N; q++) {
                    if (std::abs(A[p][q]) > 1e-9) {
                        state = 1;
                        double tau = (A[q][q] - A[p][p]) / (2.0 * A[p][q]);
                        double t;
                        if (tau >= 0) t = 1.0 / (tau + std::sqrt(1.0 + tau * tau));
                        else t = -1.0 / (-tau + std::sqrt(1.0 + tau * tau));
                        
                        double c = 1.0 / std::sqrt(1 + t * t);
                        double s = t * c;
                        
                        double app = A[p][p];
                        double aqq = A[q][q];
                        A[p][p] = c * c * app - 2.0 * s * c * A[p][q] + s * s * aqq;
                        A[q][q] = s * s * app + 2.0 * s * c * A[p][q] + c * c * aqq;
                        A[p][q] = 0.0;
                        A[q][p] = 0.0;
                        
                        for (int j = 0; j < N; j++) {
                            if (j != p && j != q) {
                                double apj = A[p][j];
                                double aqj = A[q][j];
                                A[p][j] = c * apj - s * aqj;
                                A[j][p] = A[p][j];
                                A[q][j] = s * apj + c * aqj;
                                A[j][q] = A[q][j];
                            }
                            double vip = eigenvectors[j][p];
                            double viq = eigenvectors[j][q];
                            eigenvectors[j][p] = c * vip - s * viq;
                            eigenvectors[j][q] = s * vip + c * viq;
                        }
                    }
                }
            }
            iters++;
        }
        
        for (int i = 0; i < N; i++) {
            eigenvalues[i] = A[i][i];
        }
    }

    py::dict perform_spectral_cleaning() {
        compute_correlation();
        jacobi_decomposition();
        
        double Q = (double)T / (double)N;
        double sigma_sq = 1.0; 
        double lambda_max_mp = sigma_sq * std::pow(1.0 + std::sqrt(1.0 / Q), 2.0);
        
        double dominant_eigenvalue = 0.0;
        double noise_trace = 0.0;
        double signal_trace = 0.0;
        
        std::vector<double> clean_eigenvalues = eigenvalues;
        
        for (int i = 0; i < N; ++i) {
            if (eigenvalues[i] > dominant_eigenvalue) {
                dominant_eigenvalue = eigenvalues[i];
            }
            
            if (eigenvalues[i] <= lambda_max_mp) {
                noise_trace += eigenvalues[i];
                clean_eigenvalues[i] = 0.0; // Clipping
            } else {
                signal_trace += eigenvalues[i];
            }
        }
        
        double signal_power = dominant_eigenvalue / lambda_max_mp;
        double signal_to_noise = (noise_trace > 0) ? (signal_trace / noise_trace) : signal_trace;

        py::dict result;
        result["dominant_eigenvalue"] = dominant_eigenvalue;
        result["lambda_max_mp"] = lambda_max_mp;
        result["signal_power"] = signal_power;
        result["signal_to_noise"] = signal_to_noise;
        result["eigenvalues"] = eigenvalues;
        result["clean_eigenvalues"] = clean_eigenvalues;

        return result;
    }
};

PYBIND11_MODULE(rmt_engine, m) {
    m.doc() = "Random Matrix Theory Engine v5.0 - ASI-5 Spectral Alchemist (Jacobi & Marchenko-Pastur)";
    
    py::class_<RMTEngine>(m, "RMTEngine")
        .def(py::init<int, int>())
        .def("load_data", &RMTEngine::load_data)
        .def("perform_spectral_cleaning", &RMTEngine::perform_spectral_cleaning);
}