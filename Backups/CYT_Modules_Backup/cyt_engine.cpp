#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <numeric>
#include <stdexcept>

namespace py = pybind11;

/**
 * @brief CYT Engine (Topologia Calabi-Yau)
 * 
 * Calcula a deformação de variedades em 10 dimensões para detectar colapsos
 * de mercado invisíveis (anomalias topológicas).
 */

class CYTEngine {
public:
    CYTEngine() {}

    /**
     * @brief Calcula a métrica de deformação de Ricci simplificada.
     * Recebe uma matriz 10xN representando as 10 dimensões ao longo do tempo.
     * Retorna a deformação topológica (Ricci Flow Proxy) por passo de tempo.
     */
    py::array_t<double> calculate_deformation(py::array_t<double> data_10d) {
        py::buffer_info buf = data_10d.request();
        if (buf.ndim != 2 || buf.shape[0] != 10) {
            throw std::runtime_error("Input must be a 2D array with shape (10, N).");
        }

        size_t n_dims = buf.shape[0]; // Sempre 10
        size_t n_points = buf.shape[1];
        auto ptr = static_cast<double *>(buf.ptr);

        auto result = py::array_t<double>(n_points);
        auto r_ptr = static_cast<double *>(result.request().ptr);

        // Algoritmo de Curvatura de Ricci Proxy:
        // Mede a divergência local e a compressão do volume dimensional.
        for (size_t i = 1; i < n_points; i++) {
            double metric_tensor_det = 1.0;
            double curvature = 0.0;

            for (size_t d = 0; d < n_dims; d++) {
                // Valor atual e variação na dimensão d
                double val = ptr[d * n_points + i];
                double prev_val = ptr[d * n_points + (i-1)];
                double delta = val - prev_val;

                // Acumula curvatura (proxy de Ricci)
                curvature += std::pow(delta, 2);
                
                // Compressão de volume (proxy de determinante)
                metric_tensor_det *= (1.0 + std::abs(delta));
            }

            // Deformação = Logaritmo da compressão * magnitude da curvatura
            r_ptr[i] = std::log1p(metric_tensor_det) * std::sqrt(curvature);
        }
        r_ptr[0] = 0.0;

        return result;
    }

    /**
     * @brief Calcula o Escudo de Neutrons (Métrica de Proteção).
     * Retorna um valor de 0.0 a 1.0 indicando a necessidade de trava.
     */
    double calculate_neutron_shield(py::array_t<double> deformations, double threshold) {
        py::buffer_info buf = deformations.request();
        auto ptr = static_cast<double *>(buf.ptr);
        size_t n = buf.size;

        if (n < 5) return 0.0;

        // Média das deformações recentes (janela de 5)
        double recent_avg = 0.0;
        for (size_t i = n - 5; i < n; i++) recent_avg += ptr[i];
        recent_avg /= 5.0;

        // Se a deformação ultrapassar o threshold, o escudo sobe exponencialmente
        if (recent_avg > threshold) {
            return std::min(1.0, std::exp(recent_avg - threshold) - 1.0);
        }

        return 0.0;
    }
};

PYBIND11_MODULE(cyt_engine, m) {
    py::class_<CYTEngine>(m, "CYTEngine")
        .def(py::init<>())
        .def("calculate_deformation", &CYTEngine::calculate_deformation)
        .def("calculate_neutron_shield", &CYTEngine::calculate_neutron_shield);
}
