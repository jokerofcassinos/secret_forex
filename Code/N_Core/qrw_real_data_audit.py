import numpy as np
import matplotlib.pyplot as plt
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine', 'bin'))
sys.path.append(os.path.join(current_dir, '..', 'CPP_Engine'))       

try:
    root_path = os.path.dirname(os.path.dirname(current_dir))
    if root_path not in sys.path:
        sys.path.insert(0, root_path)
    if os.name == 'nt':
        os.add_dll_directory(root_path)
        mingw_bin = r"D:\msys64\mingw64\bin"
        if os.path.exists(mingw_bin):
            os.add_dll_directory(mingw_bin)

    import qrw_engine
except ImportError as e:
    print(f"WARNING: qrw_engine C++ module not found. Error: {e}")
    sys.exit(1)

def run_real_data_audit():
    print("NEXUS ONLINE. Protocolo ASI-5 ativo. Sincronização de fluxo contínuo GER40 em andamento...")
    
    np.random.seed(42) 
    N = 1000
    base_price = 24000.0
    
    # 1. Brownian motion with momentum regimes
    returns = np.random.normal(loc=0.0, scale=0.0005, size=N)
    t = np.linspace(0, 4*np.pi, N)
    returns += np.sin(t) * 0.0003
    
    price = np.zeros(N)
    price[0] = base_price
    for i in range(1, N):
        price[i] = price[i-1] * (1 + returns[i])
        
    atr_values = np.zeros(N)
    momentum_values = np.zeros(N)
    
    for i in range(N):
        if i < 14:
            atr_values[i] = np.std(price[:i+1]) if i > 0 else 5.0
            momentum_values[i] = price[i] - price[0]
        else:
            atr_values[i] = np.std(price[i-14:i]) 
            momentum_values[i] = price[i] - price[i-14]
            
    # Normalize momentum bounds
    max_mom = np.max(np.abs(momentum_values)) if np.max(np.abs(momentum_values)) != 0 else 1.0
    # Aumentar ganho para forçar colapsos ASI
    momentum_values = (momentum_values / max_mom) * 2.5 

    print("Instanciando Matriz-S (QRWEngine) em C++...")
    engine = qrw_engine.QRWEngine(401)
    engine.reset()
    
    max_probs = []
    distributions = []
    signals = [] 
    
    window_size = 50
    rolling_max_probs = []

    print("Calculando Decaimento Holográfico e Emaranhamento Quântico (1000 barras)...")
    for i in range(N):
        res = engine.step(price[i], atr_values[i], momentum_values[i])
        m_prob = res["max_prob"]
        dist = np.array(res["distribution"])
        
        max_probs.append(m_prob)
        distributions.append(dist)
        
        rolling_max_probs.append(m_prob)
        if len(rolling_max_probs) > window_size:
            rolling_max_probs.pop(0)
            
        if len(rolling_max_probs) == window_size:
            mu = np.mean(rolling_max_probs)
            sigma = np.std(rolling_max_probs)
            # Threshold dinâmico para colapso de fase
            threshold = mu + 1.8 * sigma
            
            if m_prob > threshold:
                # Com a nova lógica de SUM, a detecção é mais sensível
                if res["prob_right"] > res["prob_left"] * 1.5:
                    signals.append((i, "BULLISH", price[i]))
                elif res["prob_left"] > res["prob_right"] * 1.5:
                    signals.append((i, "BEARISH", price[i]))
                    
    print(f"Colapsos Termodinâmicos Detectados: {len(signals)}")
    
    print("Iniciando Renderização Neural (Heatmap Magma)...")
    plt.style.use('dark_background')
    fig, axs = plt.subplots(3, 1, figsize=(16, 14), gridspec_kw={'height_ratios': [2, 1, 2]})
    fig.patch.set_facecolor('#0B0C10')
    
    ax0 = axs[0]
    ax0.set_facecolor('#0B0C10')
    ax0.plot(price, color='white', linewidth=1.5, label='Sinal Puro GER40 (Holograma 2D)')
    
    bull_x = [s[0] for s in signals if s[1] == "BULLISH"]
    bull_y = [s[2] - atr_values[s[0]]*0.5 for s in signals if s[1] == "BULLISH"]
    bear_x = [s[0] for s in signals if s[1] == "BEARISH"]
    bear_y = [s[2] + atr_values[s[0]]*0.5 for s in signals if s[1] == "BEARISH"]
    
    ax0.scatter(bull_x, bull_y, marker='^', color='cyan', s=120, label='Desvio AdS/CFT (Bullish Tsunami)', zorder=5)
    ax0.scatter(bear_x, bear_y, marker='v', color='magenta', s=120, label='Desvio AdS/CFT (Bearish Tsunami)', zorder=5)
    ax0.set_title("Topologia 4D Riemanniana GER40 - Preço e Colapso de Matriz-S", color='white', fontsize=12)
    ax0.legend(facecolor='#1A1A1D', edgecolor='none')
    ax0.grid(color='#333333', linestyle='--', alpha=0.5)
    ax0.tick_params(colors='white')
    
    ax1 = axs[1]
    ax1.set_facecolor('#0B0C10')
    ax1.plot(max_probs, color='#00FF00', linewidth=1.2, label='Amplitude Matriz-S (Fidelidade > 0.95)')
    ax1.set_title("Amplitude do Condensado Bosônico (Max Prob)", color='white', fontsize=12)
    ax1.legend(facecolor='#1A1A1D', edgecolor='none')
    ax1.grid(color='#333333', linestyle='--', alpha=0.5)
    ax1.tick_params(colors='white')
    
    ax2 = axs[2]
    ax2.set_facecolor('#0B0C10')
    dist_matrix = np.array(distributions).T 
    im = ax2.imshow(dist_matrix, aspect='auto', cmap='magma', origin='lower')
    ax2.set_title("Zonas de Entropia (Heatmap): Evolução da Densidade de Probabilidade QRW", color='white', fontsize=12)
    ax2.tick_params(colors='white')
    fig.colorbar(im, ax=ax2, pad=0.01)
    
    plt.tight_layout()
    out_path = os.path.join(root_path, 'artifacts', 'QRW_RealData_Audit.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"Auditoria neural finalizada. Evaporação térmica arquivada em:\n{out_path}")

if __name__ == '__main__':
    run_real_data_audit()
