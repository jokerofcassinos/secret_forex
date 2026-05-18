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

def run_phd_audit():
    print("Iniciando Auditoria Ph.D. do Sistema QRW ASI-5...")
    print("Gerando Distribuição Quântica com SU(2) Rotations e Shift OMP...")
    engine = qrw_engine.QRWEngine(401)
    
    steps = 100
    atr = 2.5
    current_price = 18500.0
    
    scenarios = [
        {"name": "Bullish Tsunami (Constructive Interference Right)", "momentum": 0.8},
        {"name": "Bearish Tsunami (Constructive Interference Left)", "momentum": -0.8},
        {"name": "Neutral Quantum Vacuum", "momentum": 0.0}
    ]
    
    plt.style.use('dark_background')
    fig, axs = plt.subplots(3, 1, figsize=(15, 12))
    fig.patch.set_facecolor('#0B0C10')
    
    for idx, sc in enumerate(scenarios):
        engine.reset()
        res = None
        history_max_probs = []
        for _ in range(steps):
            res = engine.step(current_price, atr, sc["momentum"])
            history_max_probs.append(res["max_prob"])
            
        mu = np.mean(history_max_probs)
        sigma = np.std(history_max_probs)
        threshold = mu + 1.5 * sigma
        
        bias_str = "NEUTRAL"
        if res["max_prob"] > threshold:
            if res["prob_right"] > res["prob_left"] * 2.0:
                bias_str = "BULLISH_BIAS"
            elif res["prob_left"] > res["prob_right"] * 2.0:
                bias_str = "BEARISH_BIAS"
                
        dist = res["distribution"]
        
        ax = axs[idx]
        ax.set_facecolor('#0B0C10')
        color = 'cyan' if sc["momentum"] > 0 else ('magenta' if sc["momentum"] < 0 else 'white')
        
        ax.plot(dist, label=f"Prob Distribution ({sc['name']})", color=color, linewidth=2)
        ax.fill_between(range(len(dist)), dist, alpha=0.3, color=color)
        
        title = f"QRW Ph.D. Audit - {sc['name']} | Bias: {bias_str} | Max Prob: {res['max_prob']:.4f} (Thr: {threshold:.4f})"
        ax.set_title(title, color='white', fontsize=12)
        ax.grid(color='#333333', linestyle='--', alpha=0.5)
        ax.legend(facecolor='#1A1A1D', edgecolor='none')
        ax.tick_params(colors='white')
        
    plt.tight_layout()
    # Save the output according to the instructions
    out_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), 'artifacts', 'QRW_Interference_Audit.png')
    plt.savefig(out_path, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
    print(f"✅ Auditoria visual de Interferência Quântica salva com sucesso em:\n{out_path}")

if __name__ == '__main__':
    run_phd_audit()
