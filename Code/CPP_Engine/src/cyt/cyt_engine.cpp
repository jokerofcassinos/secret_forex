#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <numeric>
#include <stdexcept>
#include <algorithm>

namespace py = pybind11;

/**
 * @brief CYT Engine (Topologia Calabi-Yau - AGI-5 v3.0)
 * 
 * Implementação avançada de Ricci Flow e Contração de Variedade.
 * Detecta Singularidades Topológicas (Traps) e Entropia Estrutural.
 */

class CYTEngine {
public:
    CYTEngine() {}

    /**
     * @brief Calcula a deformação e a métrica de Volume.
     * Retorna um dicionário com 'deformation' (Ricci) e 'determinant' (Volume).
     */
    py::dict analyze_manifold_flow(py::array_t<double> data_10d) {
        py::buffer_info buf = data_10d.request();
        if (buf.ndim != 2 || buf.shape[0] != 10) {
            throw std::runtime_error("Input must be (10, N).");
        }

        size_t n_dims = buf.shape[0]; 
        size_t n_points = buf.shape[1];
        auto ptr = static_cast<double *>(buf.ptr);

        auto deformation = py::array_t<double>(n_points);
        auto determinant = py::array_t<double>(n_points);
        
        auto def_ptr = static_cast<double *>(deformation.request().ptr);
        auto det_ptr = static_cast<double *>(determinant.request().ptr);

        for (size_t i = 0; i < n_points; i++) {
            def_ptr[i] = 0.0;
            det_ptr[i] = 1.0;
        }

        for (size_t i = 1; i < n_points; i++) {
            double metric_det = 1.0;
            double curvature = 0.0;

            for (size_t d = 0; d < n_dims; d++) {
                double val = ptr[d * n_points + i];
                double prev_val = ptr[d * n_points + (i-1)];
                double delta = val - prev_val;

                // Curvatura de Ricci Proxy (L² Norm do Tensor de Deformação)
                curvature += std::pow(delta, 2);
                
                // Determinante da Métrica (Volume da variedade na vizinhança i)
                metric_det *= (1.0 + std::abs(delta));
            }

            def_ptr[i] = std::sqrt(curvature);
            det_ptr[i] = metric_det;
        }

        py::dict res;
        res["deformation"] = deformation;
        res["determinant"] = determinant;
        return res;
    }

    /**
     * @brief Calcula Zonas de Perigo com Supressão Tática e Detecção de Trap.
     * Integrado com Ricci Flow e Histerese Continental.
     */
    py::array_t<double> calculate_danger_zones(py::array_t<double> data_10d, size_t window, double threshold) {
        py::dict flow = analyze_manifold_flow(data_10d);
        auto def_array = flow["deformation"].cast<py::array_t<double>>();
        auto det_array = flow["determinant"].cast<py::array_t<double>>();
        
        auto def_ptr = static_cast<double *>(def_array.request().ptr);
        auto det_ptr = static_cast<double *>(det_array.request().ptr);
        size_t n_points = def_array.size();

        auto result = py::array_t<double>(n_points);
        auto r_ptr = static_cast<double *>(result.request().ptr);

        for (size_t i = 0; i < n_points; i++) r_ptr[i] = 0.0;

        if (n_points <= window) return result;

        double last_ema_score = 0.0;
        double alpha = 0.15; // Recuperação mais rápida (v3.1)

        for (size_t i = window; i < n_points; i++) {
            double sum = 0.0;
            for (size_t j = i - window; j < i; j++) sum += def_ptr[j];
            double mean = sum / window;

            double variance = 0.0;
            for (size_t j = i - window; j < i; j++) variance += std::pow(def_ptr[j] - mean, 2);
            variance /= window;
            double std_dev = std::sqrt(variance);

            double current_def = def_ptr[i];
            double current_det = det_ptr[i];
            
            double shock = 0.0;
            if (std_dev > 1e-9 && current_def > mean) {
                shock = (current_def - mean) / std_dev;
            }

            // O perigo agora é escalonado logaritmicamente para evitar bloqueios em expansões direcionais
            double raw_score = current_def * shock * std::log1p(current_det);
            
            double smoothed_score = (raw_score * alpha) + (last_ema_score * (1.0 - alpha));
            last_ema_score = smoothed_score;

            if (smoothed_score > threshold) {
                double excess = smoothed_score - threshold;
                r_ptr[i] = std::min(100.0, (excess / threshold) * 50.0 + 50.0);
            } else {
                r_ptr[i] = 0.0;
            }
        }

        return result;
    }
};

PYBIND11_MODULE(cyt_engine, m) {
    py::class_<CYTEngine>(m, "CYTEngine")
        .def(py::init<>())
        .def("analyze_manifold_flow", &CYTEngine::analyze_manifold_flow)
        .def("calculate_danger_zones", &CYTEngine::calculate_danger_zones);
}
