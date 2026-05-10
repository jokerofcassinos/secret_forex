#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <numeric>

namespace py = pybind11;

/**
 * 🌌 PHS ENGINE v1.0 - PERSISTENT HOMOLOGY SCANNER
 * Topologia de Dados (TDA) baseada em aproximações de Números de Betti.
 * Constrói embedding de Takens e calcula β0 (componentes conectados) e 
 * β1 (ciclos homológicos).
 */
class PHSEngine {
private:
    int time_steps;
    int embed_dim;
    int delay;
    std::vector<double> prices;
    std::vector<double> betti_0_history;
    std::vector<double> betti_1_history;

    // Distância Euclidiana no espaço de Takens
    double euclidean_dist(const std::vector<double>& p1, const std::vector<double>& p2) {
        double sum = 0;
        for (size_t i = 0; i < p1.size(); ++i) {
            double d = p1[i] - p2[i];
            sum += d * d;
        }
        return std::sqrt(sum);
    }

public:
    PHSEngine(int t_steps, int edim = 3, int dly = 1) : time_steps(t_steps), embed_dim(edim), delay(dly) {
        prices.resize(time_steps, 0.0);
    }

    void load_data(py::array_t<double> input_data) {
        py::buffer_info buf = input_data.request();
        if (buf.ndim != 1 || buf.shape[0] != time_steps) {
            throw std::runtime_error("PHS: Dimensão de entrada incompatível.");
        }

        double *ptr = static_cast<double *>(buf.ptr);
        for (int t = 0; t < time_steps; ++t) {
            prices[t] = ptr[t];
        }
    }

    void compute_homology(double epsilon = 0.0) {
        betti_0_history.assign(time_steps, 0.0);
        betti_1_history.assign(time_steps, 0.0);

        int lookback_window = 30; // Janela móvel para TDA
        
        for (int t = lookback_window; t < time_steps; ++t) {
            // Construir point cloud via Takens Embedding
            std::vector<std::vector<double>> point_cloud;
            for (int w = t - lookback_window + (embed_dim - 1) * delay; w <= t; ++w) {
                std::vector<double> pt(embed_dim, 0.0);
                for (int d = 0; d < embed_dim; ++d) {
                    pt[d] = prices[w - d * delay];
                }
                point_cloud.push_back(pt);
            }

            int n_pts = point_cloud.size();
            
            // Determinar epsilon dinâmico se não fornecido
            double eps = epsilon;
            if (eps == 0.0) {
                double avg_dist = 0.0;
                int count = 0;
                for (int i = 0; i < n_pts - 1; ++i) {
                    avg_dist += euclidean_dist(point_cloud[i], point_cloud[i+1]);
                    count++;
                }
                eps = (avg_dist / count) * 1.5; // Threshold adaptativo
            }

            // Construir Vietoris-Rips (grafo de vizinhança)
            std::vector<std::vector<int>> adj(n_pts);
            int edges = 0;
            for (int i = 0; i < n_pts; ++i) {
                for (int j = i + 1; j < n_pts; ++j) {
                    if (euclidean_dist(point_cloud[i], point_cloud[j]) <= eps) {
                        adj[i].push_back(j);
                        adj[j].push_back(i);
                        edges++;
                    }
                }
            }

            // Calcular Betti-0 (Componentes conectados) via BFS
            std::vector<bool> visited(n_pts, false);
            int connected_components = 0;
            for (int i = 0; i < n_pts; ++i) {
                if (!visited[i]) {
                    connected_components++;
                    std::vector<int> q = {i};
                    visited[i] = true;
                    while (!q.empty()) {
                        int curr = q.back();
                        q.pop_back();
                        for (int neighbor : adj[curr]) {
                            if (!visited[neighbor]) {
                                visited[neighbor] = true;
                                q.push_back(neighbor);
                            }
                        }
                    }
                }
            }

            // Heurística de Betti-1 (Ciclos 1D) 
            // Pela formula de Euler-Poincaré para grafos conexos: V - E = b0 - b1
            // Então b1 = E - V + b0
            int betti_1 = edges - n_pts + connected_components;
            if (betti_1 < 0) betti_1 = 0;
            if (connected_components < 1 && n_pts > 0) connected_components = 1;

            betti_0_history[t] = connected_components;
            betti_1_history[t] = betti_1;
        }
    }

    py::dict get_results() {
        py::dict d;
        d["betti_0"] = betti_0_history;
        d["betti_1"] = betti_1_history;
        return d;
    }
};

PYBIND11_MODULE(phs_engine, m) {
    m.doc() = "PHS Engine v1.0 - Persistent Homology Scanner";

    py::class_<PHSEngine>(m, "PHSEngine")
        .def(py::init<int, int, int>())
        .def("load_data", &PHSEngine::load_data)
        .def("compute_homology", &PHSEngine::compute_homology)
        .def("get_results", &PHSEngine::get_results);
}
