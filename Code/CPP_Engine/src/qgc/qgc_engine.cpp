#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include <vector>
#include <cmath>
#include <algorithm>

namespace py = pybind11;

struct QuantumZone {
    double price;
    double mass;
    double creation_time;
    double current_mass;
};

class QGCEngine {
private:
    std::vector<QuantumZone> zones;
    double epsilon = 1.5;

public:
    QGCEngine() {}

    void add_zone(double price, double mass, double time) {
        // Lógica de Agrupamento Dinâmico
        for (auto& zone : zones) {
            if (std::abs(zone.price - price) < 5.0) { 
                zone.current_mass += mass * 0.5;
                zone.mass += mass * 0.5;
                return;
            }
        }
        zones.push_back({price, mass, time, mass});
    }

    void update_evaporation(double current_time, double current_price, double current_atr) {
        double safe_atr = std::max(current_atr, 1.0); 
        
        for (auto& zone : zones) {
            double dist = std::abs(current_price - zone.price);
            
            double proximity_factor = std::exp(-dist / safe_atr); 
            double temporal_decay = 0.002; 
            
            double radiation = temporal_decay + (0.15 * proximity_factor); 
            
            // Integração irreversível da Termodinâmica
            zone.current_mass = zone.current_mass * std::exp(-radiation * 1.0);
        }
        
        zones.erase(std::remove_if(zones.begin(), zones.end(), [](const QuantumZone& z) {
            return z.current_mass < 0.05; 
        }), zones.end());
    }

    double calculate_gravity_pull(double current_price) {
        double total_pull = 0.0;
        for (const auto& zone : zones) {
            double dist = std::abs(current_price - zone.price);
            total_pull += zone.current_mass / std::sqrt(dist * dist + epsilon * epsilon);
        }
        return total_pull;
    }

    py::dict compute_hawking_decay(py::array_t<double> prices, py::array_t<double> volumes, py::array_t<double> atrs, double m_thr) {
        py::buffer_info p_buf = prices.request();
        py::buffer_info v_buf = volumes.request();
        py::buffer_info a_buf = atrs.request();
        
        if (p_buf.size != v_buf.size || p_buf.size != a_buf.size) {
            throw std::runtime_error("QGC_ASI5: Input arrays must have the same size.");
        }

        double *p_ptr = static_cast<double *>(p_buf.ptr);
        double *v_ptr = static_cast<double *>(v_buf.ptr);
        double *a_ptr = static_cast<double *>(a_buf.ptr);
        int steps = p_buf.size;
        
        std::vector<QuantumZone> sim_zones;
        
        for (int t = 0; t < steps; ++t) {
            // Ignita zonas quando o volume excede o threshold
            if (v_ptr[t] > m_thr) {
                bool merged = false;
                for (auto& z : sim_zones) {
                    if (std::abs(z.price - p_ptr[t]) < 5.0) {
                        z.current_mass += v_ptr[t] * 0.5;
                        z.mass += v_ptr[t] * 0.5;
                        merged = true;
                        break;
                    }
                }
                if (!merged) {
                    sim_zones.push_back({p_ptr[t], v_ptr[t], (double)t, v_ptr[t]});
                }
            }
            
            // Aplica decaimento dinâmico
            double safe_atr = std::max(a_ptr[t], 1.0);
            for (auto& z : sim_zones) {
                double dist = std::abs(p_ptr[t] - z.price);
                double proximity_factor = std::exp(-dist / safe_atr);
                double radiation = 0.002 + (0.15 * proximity_factor); 
                // Integração irreversível
                z.current_mass = z.current_mass * std::exp(-radiation * 1.0);
            }
            
            sim_zones.erase(std::remove_if(sim_zones.begin(), sim_zones.end(), [](const QuantumZone& z) {
                return z.current_mass < 0.05;
            }), sim_zones.end());
        }
        
        std::vector<double> res_masses;
        std::vector<double> centers;
        std::vector<double> ages;
        
        for (const auto& z : sim_zones) {
            res_masses.push_back(z.current_mass);
            centers.push_back(z.price);
            ages.push_back(steps - z.creation_time);
        }
        
        py::dict out;
        out["residual_masses"] = res_masses;
        out["centers_of_mass"] = centers;
        out["ages"] = ages;
        return out;
    }

    py::list get_active_zones() {
        py::list out;
        for (const auto& zone : zones) {
            py::dict d;
            d["price"] = zone.price;
            d["mass"] = zone.current_mass;
            d["ratio"] = zone.current_mass / zone.mass;
            d["age"] = zone.creation_time;
            out.append(d);
        }
        return out;
    }
};

PYBIND11_MODULE(qgc_engine, m) {
    m.doc() = "QGC Engine v5.0 - ASI-5 Quantum Glass Condensates with Hawking Radiation";
    py::class_<QGCEngine>(m, "QGCEngine")
        .def(py::init<>())
        .def("add_zone", &QGCEngine::add_zone)
        .def("update_evaporation", &QGCEngine::update_evaporation)
        .def("calculate_gravity_pull", &QGCEngine::calculate_gravity_pull)
        .def("compute_hawking_decay", &QGCEngine::compute_hawking_decay)
        .def("get_active_zones", &QGCEngine::get_active_zones);
}
