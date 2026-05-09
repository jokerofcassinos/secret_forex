#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
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
    double decay_constant = 0.0002; // Aumentado para visibilidade
    double epsilon = 1.5;           // Softening Factor (evita picos infinitos)

public:
    QGCEngine() {}

    void add_zone(double price, double mass, double time) {
        // Lógica de Agrupamento (Merge) - Se já houver zona perto, reforça a massa em vez de criar nova
        for (auto& zone : zones) {
            if (std::abs(zone.price - price) < 5.0) { // Janela de 5 pontos para o GER40
                zone.current_mass += mass * 0.5;
                zone.mass += mass * 0.5;
                return;
            }
        }
        zones.push_back({price, mass, time, mass});
    }

    void update_evaporation(double current_time, double current_price) {
        for (auto& zone : zones) {
            double delta_t = current_time - zone.creation_time;
            double dist = std::abs(current_price - zone.price);
            
            // Decaimento Hawking Dinâmico: Mais rápido se o preço estiver longe
            double distance_penalty = 1.0 + (dist / 100.0);
            zone.current_mass = zone.mass * std::exp(-decay_constant * delta_t * distance_penalty);
        }
        
        zones.erase(std::remove_if(zones.begin(), zones.end(), [](const QuantumZone& z) {
            return z.current_mass < (z.mass * 0.1); // Threshold de 10%
        }), zones.end());
    }

    double calculate_gravity_pull(double current_price) {
        double total_pull = 0.0;
        for (const auto& zone : zones) {
            double dist = std::abs(current_price - zone.price);
            // Fórmula de Gravidade Suavizada (Plummer-like)
            total_pull += zone.current_mass / std::sqrt(dist * dist + epsilon * epsilon);
        }
        return total_pull;
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
    py::class_<QGCEngine>(m, "QGCEngine")
        .def(py::init<>())
        .def("add_zone", &QGCEngine::add_zone)
        .def("update_evaporation", &QGCEngine::update_evaporation)
        .def("calculate_gravity_pull", &QGCEngine::calculate_gravity_pull)
        .def("get_active_zones", &QGCEngine::get_active_zones);
}