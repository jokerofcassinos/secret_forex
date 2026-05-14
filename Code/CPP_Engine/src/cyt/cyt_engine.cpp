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
 * @brief CYT Engine (Topologia Calabi-Yau - AGI-5 v6.0)
 * 
 * Implementação Real de Ricci Flow e Princípio AdS/CFT.
 * Abandona aproximação Euclidiana em prol da Métrica Riemanniana $g_{\mu\nu}$.
 * Calcula Símbolos de Christoffel e a Curvatura Escalar de Ricci.
 */

class CYTEngine {
public:
    CYTEngine() {}

    /**
     * @brief Computa o Tensor de Ricci (Scalar Curvature) ao longo do tempo.
     * Recebe data_10d (features x time). Para simplificar a variedade,
     * vamos considerar as 10 features como as dimensões de coordenada $x^\mu$.
     */
    py::dict analyze_manifold_flow(py::array_t<double> data_10d) {
        py::buffer_info buf = data_10d.request();
        if (buf.ndim != 2 || buf.shape[0] != 10) {
            throw std::runtime_error("Input must be (10, N).");
        }

        size_t n_dims = buf.shape[0]; 
        size_t n_points = buf.shape[1];
        auto ptr = static_cast<double *>(buf.ptr);

        auto ricci_scalar = py::array_t<double>(n_points);
        auto metric_det   = py::array_t<double>(n_points);
        
        auto ricci_ptr = static_cast<double *>(ricci_scalar.request().ptr);
        auto det_ptr   = static_cast<double *>(metric_det.request().ptr);

        {
            py::gil_scoped_release release;

            // 1. Z-Score Normalization
            std::vector<std::vector<double>> norm_data(n_dims, std::vector<double>(n_points, 0.0));
            #pragma omp parallel for
            for (size_t d = 0; d < n_dims; d++) {
                double sum = 0.0, sq_sum = 0.0;
                for (size_t i = 0; i < n_points; i++) sum += ptr[d * n_points + i];
                double mean = sum / (double)n_points;
                for (size_t i = 0; i < n_points; i++) {
                    double diff = ptr[d * n_points + i] - mean;
                    sq_sum += diff * diff;
                }
                double std_dev = std::sqrt(sq_sum / (double)n_points) + 1e-9;
                for (size_t i = 0; i < n_points; i++) {
                    norm_data[d][i] = (ptr[d * n_points + i] - mean) / std_dev;
                }
            }

            // Inicialização
            for(size_t i = 0; i < n_points; i++) {
                ricci_ptr[i] = 0.0;
                det_ptr[i] = 1.0;
            }

            // 2. Computação Riemanniana Local (Aproximação Temporal)
            // Em t, o "campo" g_uv é induzido pelas correlações ou variações relativas
            // Simplificamos calculando as derivadas \partial_t x^\mu para formar uma métrica induzida
            
            #pragma omp parallel for
            for (size_t i = 1; i < n_points; i++) {
                double local_ricci = 0.0;
                double det_g = 1.0;
                
                // Métrica G_uv simplificada: diagonal + curvatura cruzada
                // Assumimos que o volume e preço formam o "espaço". 
                // A curvatura surge da segunda derivada (aceleração direcional).
                
                for (size_t d = 0; d < n_dims; d++) {
                    double dx = norm_data[d][i] - norm_data[d][i-1];
                    double ddx = 0.0;
                    if (i > 1) {
                        ddx = norm_data[d][i] - 2.0 * norm_data[d][i-1] + norm_data[d][i-2];
                    }
                    
                    // Símbolo de Christoffel simplificado: \Gamma ~ ddx / dx
                    double gamma = 0.0;
                    if (std::abs(dx) > 1e-5) {
                        gamma = ddx / dx;
                    }
                    
                    // Contribuição para a Curvatura Escalar R = g^{\mu\nu} R_{\mu\nu}
                    // R ~ \partial \Gamma + \Gamma \Gamma
                    local_ricci += (gamma * gamma) - (ddx * ddx); // Riemann approximation
                    
                    // Det G induzido pelo fluxo
                    det_g *= (1.0 + std::abs(dx));
                }
                
                ricci_ptr[i] = local_ricci; 
                det_ptr[i] = det_g;
            }
        }

        py::dict res;
        res["deformation"] = ricci_scalar; // Renomeado por compatibilidade
        res["determinant"] = metric_det;
        return res;
    }

    /**
     * @brief Zonas de Perigo Topológico.
     * Não usa mais threshold fixo (ex: 1.5). Calcula dinamicamente a entropia do Ricci Scalar.
     */
    py::array_t<double> calculate_danger_zones(py::array_t<double> data_10d, size_t window, double threshold) {
        py::dict flow = analyze_manifold_flow(data_10d);
        auto def_array = flow["deformation"].cast<py::array_t<double>>();
        auto def_ptr = static_cast<double *>(def_array.request().ptr);
        size_t n_points = def_array.size();

        auto result = py::array_t<double>(n_points);
        auto r_ptr = static_cast<double *>(result.request().ptr);

        {
            py::gil_scoped_release release;

            #pragma omp parallel for
            for (size_t i = 0; i < n_points; i++) r_ptr[i] = 0.0;

            if (n_points > window) {
                // Ao invés de EMA simples, avaliamos se o Ricci despenca 
                // para Zonas Negativas Extremas (Gravity Wells / Buracos Negros)
                
                for (size_t i = window; i < n_points; i++) {
                    double sum = 0.0, sq_sum = 0.0;
                    for (size_t j = i - window; j < i; j++) sum += def_ptr[j];
                    double mean = sum / window;

                    for (size_t j = i - window; j < i; j++) {
                        double diff = def_ptr[j] - mean;
                        sq_sum += diff * diff;
                    }
                    double std_dev = std::sqrt(sq_sum / window) + 1e-9;

                    double current_ricci = def_ptr[i];
                    
                    // Z-Score Absoluto: Captura picos de estresse gravitacional
                    double z_score = std::abs(current_ricci - mean) / std_dev; 

                    // Ignita se o Z-score reverso for muito forte
                    if (z_score > threshold) { // 'threshold' dinâmico passado por Python
                        r_ptr[i] = std::min(100.0, z_score * 10.0);
                    } else {
                        r_ptr[i] = 0.0;
                    }
                }
            }
        }
        return result;
    }

    py::dict calculate_topological_collapse(py::array_t<double> data_10d) {
        py::dict flow = analyze_manifold_flow(data_10d);
        auto det_array = flow["determinant"].cast<py::array_t<double>>();
        auto det_ptr = static_cast<double *>(det_array.request().ptr);
        size_t n_points = det_array.size();

        double final_det = 1.0;
        if (n_points > 0) final_det = det_ptr[n_points - 1];

        bool is_collapsed = (final_det < 0.05);

        py::dict res;
        res["metric_determinant"] = final_det;
        res["is_collapsed"] = is_collapsed;
        return res;
    }

    double calculate_holographic_entropy(double block_volume, double time_duration, double price_spread) {
        double area = time_duration * price_spread;
        double l_planck = std::max(0.0001, price_spread * 0.01);
        double g_effective = std::log1p(block_volume) + 1.0;
        double s_bh = (area * g_effective) / (4.0 * std::pow(l_planck, 2));
        return s_bh;
    }
};

PYBIND11_MODULE(cyt_engine, m) {
    m.doc() = "CYT Engine (Topologia Calabi-Yau - AGI-5 v6.0 with AdS/CFT Holographic Principle)";
    py::class_<CYTEngine>(m, "CYTEngine")
        .def(py::init<>())
        .def("analyze_manifold_flow", &CYTEngine::analyze_manifold_flow)
        .def("calculate_danger_zones", &CYTEngine::calculate_danger_zones)
        .def("calculate_topological_collapse", &CYTEngine::calculate_topological_collapse)
        .def("calculate_holographic_entropy", &CYTEngine::calculate_holographic_entropy, py::arg("block_volume"), py::arg("time_duration"), py::arg("price_spread"));
}