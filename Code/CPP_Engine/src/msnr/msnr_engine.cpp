#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <vector>
#include <cmath>
#include <algorithm>
#include <complex>

namespace py = pybind11;

/**
 * @brief MSNR Engine - Alquimia Espectral (ASI v6.0)
 * 
 * Implementa a Poda Espectral via Transformada de Fourier e Filtragem de Autovalores.
 * O objetivo é extrair a Ressonância Institucional pura do ruído do varejo.
 */

class MSNREngine {
public:
    MSNREngine() {}

    /**
     * @brief Realiza a Poda Espectral para redução de ruído.
     * Filtra frequências que não possuem coerência de fase com o fluxo macro.
     */
    py::array_t<double> spectral_denoising(py::array_t<double> prices, double cut_off_ratio) {
        py::buffer_info buf = prices.request();
        double* ptr = static_cast<double*>(buf.ptr);
        size_t n = buf.size;

        // 1. Padding para potência de 2 (Otimização FFT)
        size_t n_fft = 1;
        while (n_fft < n) n_fft <<= 1;

        std::vector<std::complex<double>> signal(n_fft, 0.0);
        for (size_t i = 0; i < n; i++) signal[i] = std::complex<double>(ptr[i], 0.0);

        // 2. FFT Simples (Cooley-Tukey Iterativo)
        fft(signal, false);

        // 3. Poda Espectral (Spectral Pruning)
        // Mantemos apenas as baixas frequências (Trending Institucional)
        size_t cut_off = static_cast<size_t>(n_fft * cut_off_ratio);
        for (size_t i = cut_off; i < n_fft - cut_off; i++) {
            signal[i] = 0.0;
        }

        // 4. IFFT (Inversa)
        fft(signal, true);

        auto result = py::array_t<double>(n);
        double* res_ptr = static_cast<double*>(result.request().ptr);
        for (size_t i = 0; i < n; i++) res_ptr[i] = signal[i].real();

        return result;
    }

    /**
     * @brief Calcula a Ressonância de Sinal (Signal-to-Noise Ratio Quântico)
     */
    double calculate_resonance_fidelity(py::array_t<double> raw, py::array_t<double> filtered) {
        py::buffer_info buf_raw = raw.request();
        py::buffer_info buf_filt = filtered.request();
        double* p_raw = static_cast<double*>(buf_raw.ptr);
        double* p_filt = static_cast<double*>(buf_filt.ptr);
        size_t n = buf_raw.size;

        double signal_energy = 0.0;
        double noise_energy = 0.0;

        for (size_t i = 0; i < n; i++) {
            signal_energy += p_filt[i] * p_filt[i];
            double noise = p_raw[i] - p_filt[i];
            noise_energy += noise * noise;
        }

        if (noise_energy < 1e-12) return 1.0;
        return 1.0 / (1.0 + (noise_energy / (signal_energy + 1e-9)));
    }

private:
    void fft(std::vector<std::complex<double>>& a, bool invert) {
        size_t n = a.size();
        for (size_t i = 1, j = 0; i < n; i++) {
            size_t bit = n >> 1;
            for (; j & bit; bit >>= 1) j ^= bit;
            j ^= bit;
            if (i < j) std::swap(a[i], a[j]);
        }

        for (size_t len = 2; len <= n; len <<= 1) {
            double ang = 2 * M_PI / len * (invert ? -1 : 1);
            std::complex<double> wlen(std::cos(ang), std::sin(ang));
            for (size_t i = 0; i < n; i += len) {
                std::complex<double> w(1);
                for (size_t j = 0; j < len / 2; j++) {
                    std::complex<double> u = a[i + j], v = a[i + j + len / 2] * w;
                    a[i + j] = u + v;
                    a[i + j + len / 2] = u - v;
                    w *= wlen;
                }
            }
        }

        if (invert) {
            for (auto& x : a) x /= static_cast<double>(n);
        }
    }
};

PYBIND11_MODULE(msnr_engine, m) {
    m.doc() = "MSNR Engine - Spectral Alchemist C++";
    py::class_<MSNREngine>(m, "MSNREngine")
        .def(py::init<>())
        .def("spectral_denoising", &MSNREngine::spectral_denoising)
        .def("calculate_resonance_fidelity", &MSNREngine::calculate_resonance_fidelity);
}
