#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <numeric>
#include <stdexcept>
#include <algorithm>
#ifdef _OPENMP
#include <omp.h>
#endif

namespace py = pybind11;

/**
 * @brief CYT Engine (Topologia Calabi-Yau - AGI-5 v3.0)
 * 
 * Implementação avançada de Ricci Flow e Contração de Variedade.
 * Otimizado com liberação do GIL (Global Interpreter Lock) e OpenMP
 * para suportar a latência sub-milissegundo da Teoria do Campo Unificado.
 */

class CYTEngine {
public:
    CYTEngine() {}

    /**
     * @brief Calcula a deformação e a métrica de Volume.
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

        {
            // OTIMIZAÇÃO: Liberação do GIL e Paralelização OpenMP
            py::gil_scoped_release release;

            #pragma omp parallel for
            for (size_t i = 0; i < n_points; i++) {
                def_ptr[i] = 0.0;
                det_ptr[i] = 1.0;
            }

            #pragma omp parallel for
            for (size_t i = 1; i < n_points; i++) {
                double metric_det = 1.0;
                double curvature = 0.0;

                for (size_t d = 0; d < n_dims; d++) {
                    double val = ptr[d * n_points + i];
                    double prev_val = ptr[d * n_points + (i-1)];
                    double delta = val - prev_val;

                    // Curvatura de Ricci Proxy
                    curvature += delta * delta;
                    
                    // Determinante da Métrica
                    metric_det *= (1.0 + std::abs(delta));
                }

                def_ptr[i] = std::sqrt(curvature);
                det_ptr[i] = metric_det;
            }
        }

        py::dict res;
        res["deformation"] = deformation;
        res["determinant"] = determinant;
        return res;
    }

    /**
     * @brief Calcula Zonas de Perigo.
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

        {
            py::gil_scoped_release release;

            #pragma omp parallel for
            for (size_t i = 0; i < n_points; i++) r_ptr[i] = 0.0;

            if (n_points > window) {
                double last_ema_score = 0.0;
                double alpha = 0.15; 

                // Nota: O laço a seguir carrega dependência serial (last_ema_score).
                // Não pode ser paralelizado trivialmente com OpenMP, mas a liberação do GIL
                // já garante que o Python não seja bloqueado.
                for (size_t i = window; i < n_points; i++) {
                    double sum = 0.0;
                    for (size_t j = i - window; j < i; j++) sum += def_ptr[j];
                    double mean = sum / window;

                    double variance = 0.0;
                    for (size_t j = i - window; j < i; j++) {
                        double diff = def_ptr[j] - mean;
                        variance += diff * diff;
                    }
                    variance /= window;
                    double std_dev = std::sqrt(variance);

                    double current_def = def_ptr[i];
                    double current_det = det_ptr[i];
                    
                    double shock = 0.0;
                    if (std_dev > 1e-9 && current_def > mean) {
                        shock = (current_def - mean) / std_dev;
                    }

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
            }
        }

        return result;
    }

    /**
     * @brief Avalia colapso estrutural métrico.
     */
    py::dict calculate_topological_collapse(py::array_t<double> data_10d) {
        py::dict flow = analyze_manifold_flow(data_10d);
        auto det_array = flow["determinant"].cast<py::array_t<double>>();
        auto det_ptr = static_cast<double *>(det_array.request().ptr);
        size_t n_points = det_array.size();

        double final_det = 1.0;
        if (n_points > 0) {
            final_det = det_ptr[n_points - 1];
        }

        bool is_collapsed = (final_det < 0.05);

        py::dict res;
        res["metric_determinant"] = final_det;
        res["is_collapsed"] = is_collapsed;
        return res;
    }

    /**
     * @brief Computa a Entropia de Bekenstein-Hawking da Sombra de Liquidez (AdS/CFT).
     * O gráfico 2D é o holograma. Computamos a entropia do "Bulk" (The Black Hole).
     * S_BH = (A * k_B * c^3) / (4 * G * hbar)
     * Simplificado para o domínio financeiro: S_BH = Area_Holografica / (4 * L_Planck_Financeiro)
     */
    double calculate_holographic_entropy(double block_volume, double time_duration, double price_spread) {
        // Area do Horizonte de Eventos projetado (2D Boundary)
        double area = time_duration * price_spread;
        
        // Comprimento de Planck Financeiro (Incerteza mínima do grid, spread + latência)
        // Usamos um valor normalizado para evitar infinitos.
        double l_planck = std::max(0.0001, price_spread * 0.01);
        
        // Gravidade efetiva (proporcional ao volume)
        double g_effective = std::log1p(block_volume) + 1.0;

        // Entropia Termodinâmica do Buraco Negro de Liquidez
        double s_bh = (area * g_effective) / (4.0 * std::pow(l_planck, 2));

        return s_bh;
    }
};

PYBIND11_MODULE(cyt_engine, m) {
    m.doc() = "CYT Engine (Topologia Calabi-Yau - AGI-5 v5.0 with AdS/CFT Holographic Principle)";
    py::class_<CYTEngine>(m, "CYTEngine")
        .def(py::init<>())
        .def("analyze_manifold_flow", &CYTEngine::analyze_manifold_flow)
        .def("calculate_danger_zones", &CYTEngine::calculate_danger_zones)
        .def("calculate_topological_collapse", &CYTEngine::calculate_topological_collapse)
        .def("calculate_holographic_entropy", &CYTEngine::calculate_holographic_entropy, py::arg("block_volume"), py::arg("time_duration"), py::arg("price_spread"));
}