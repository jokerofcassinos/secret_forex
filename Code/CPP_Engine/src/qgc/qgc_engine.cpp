#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>

namespace py = pybind11;

/**
 * @brief QGC Engine (Quantum Glass Condensate) - AGI-Ph.D
 * Computa o decaimento termodinâmico de Order Blocks via Radiação Hawking
 * e a dispersão acústica de Fônons na fronteira da liquidez.
 */
class QGCEngine {
public:
    QGCEngine() {}

    /**
     * @brief Computa a Evaporação da Singularidade (Decaimento Hawking)
     * Avalia blocos massivos do passado e calcula sua massa residual no presente.
     */
    py::dict compute_hawking_decay(py::array_t<double> prices, py::array_t<double> volumes, py::array_t<double> atrs, double initial_mass_threshold) {
        py::buffer_info p_buf = prices.request();
        py::buffer_info v_buf = volumes.request();
        py::buffer_info a_buf = atrs.request();
        
        int n = p_buf.shape[0];
        double *p_ptr = static_cast<double *>(p_buf.ptr);
        double *v_ptr = static_cast<double *>(v_buf.ptr);
        double *a_ptr = static_cast<double *>(a_buf.ptr);

        std::vector<double> active_masses;
        std::vector<double> active_centers;
        std::vector<int> active_ages;

        {
            py::gil_scoped_release release; // Paralelismo assíncrono (seguro de acessar memória raw sem GIL)

            // Varredura temporal: encontrar os condensados iniciais e decai-los
            for (int i = 0; i < n - 1; ++i) {
                if (v_ptr[i] > initial_mass_threshold) {
                    double M_0 = v_ptr[i];
                    double center = p_ptr[i];
                    double current_mass = M_0;
                    int age = n - 1 - i; // Idade relativa ao final da matriz
                    
                    // Decaimento cronológico: de 'i' até o 'presente' (n-1)
                    for (int j = i + 1; j < n; ++j) {
                        double dist = std::abs(p_ptr[j] - center);
                        double local_volatility = a_ptr[j];
                        
                        // A Constante de Decaimento Lambda aumenta se o preço orbita perto do Vidro
                        double lambda = 0.005; // Evaporação natural pelo tempo
                        if (local_volatility > 0) {
                            // Flutuações quânticas consumindo a massa gravitacional da barreira
                            double proximity_factor = std::max(0.0, 1.0 - (dist / (local_volatility * 3.0)));
                            lambda += 0.05 * proximity_factor; 
                        }
                        
                        // Decaimento Exponencial: M(t) = M0 * e^(-lambda)
                        current_mass = current_mass * std::exp(-lambda);
                        
                        // Singularidade Evaporada: Massa Residual < 10% da Original
                        if (current_mass < (M_0 * 0.1)) {
                            current_mass = 0; 
                            break; // Vidro estilhaçado ou evaporado
                        }
                    }
                    
                    // Se a zona sobreviveu até o presente com massa gravitacional
                    if (current_mass > 0) {
                        active_masses.push_back(current_mass);
                        active_centers.push_back(center);
                        active_ages.push_back(age);
                    }
                }
            }
        } // O GIL é readquirido automaticamente aqui ao final do escopo
        
        py::dict res;
        res["residual_masses"] = py::cast(active_masses);
        res["centers_of_mass"] = py::cast(active_centers);
        res["ages"] = py::cast(active_ages);
        return res;
    }
    
    /**
     * @brief Dispersão de Fônons (Phonon Scattering)
     * Determina a probabilidade do preço ricochetear ou estilhaçar o Condensado de Vidro.
     */
    double phonon_scattering(double kinetic_energy, double glass_binding_energy) {
        if (glass_binding_energy <= 0) return 1.0; // Slippage Absoluto (Vácuo)
        
        // Razão entre a agressão da onda de preço e a tensão da membrana
        double ratio = kinetic_energy / glass_binding_energy;
        if (ratio > 1.0) {
            return 1.0; // Vidro quebra. Falso Rompimento / Slippage massivo
        } else {
            // Probabilidade de penetração da onda acústica. 1 - ratio^2 é a chance de Reversão Total.
            return ratio * ratio; 
        }
    }
};

PYBIND11_MODULE(qgc_engine, m) {
    m.doc() = "Quantum Glass Condensate Engine v5.0 (Hawking Radiation & Phonon Scattering)";
    py::class_<QGCEngine>(m, "QGCEngine")
        .def(py::init<>())
        .def("compute_hawking_decay", &QGCEngine::compute_hawking_decay, 
             py::arg("prices"), py::arg("volumes"), py::arg("atrs"), py::arg("initial_mass_threshold"))
        .def("phonon_scattering", &QGCEngine::phonon_scattering,
             py::arg("kinetic_energy"), py::arg("glass_binding_energy"));
}