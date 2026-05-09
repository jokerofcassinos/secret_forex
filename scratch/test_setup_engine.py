"""Test: Quantum Setup Engine v2.0 — Backfill mode validation"""
import sys
sys.path.insert(0, '.')
from Code.N_Core.quantum_setups import QuantumSetupEngine

# ═══════════════════════════════════════════════════════════════════
# TEST 1: S3 Bosonic Ignition (Backfill — lower squeeze threshold)
# ═══════════════════════════════════════════════════════════════════
print("=== TEST 1: S3 Bosonic (Backfill) ===")
e = QuantumSetupEngine()

# Simulate 3 bars of squeeze (backfill threshold)
for i in range(3):
    e.evaluate({"lbm_signal": "BOSONIC_SQUEEZE", "qcd_signal": "CONFINED"}, backfill=True)

# Squeeze ends + QCD Fission UP
result = e.evaluate({
    "lbm_signal": "LAMINAR_FLOW",
    "qcd_signal": "FISSION_EXPANSION_UP",
    "rht_flash": 0.0, "rmt_signal": "NOISE_x1.0", "qrw_signal": "NEUTRAL"
}, backfill=True)

assert len(result) == 1 and result[0]['setup'] == 'S3_BOSONIC_IGNITION', f"FAIL: Expected S3, got {result}"
print(f"  ✅ S3 BACKFILL PASS: {result[0]['setup']} {result[0]['direction']}")

# ═══════════════════════════════════════════════════════════════════
# TEST 2: S4 Harmonic Resonance (Backfill — no QGC/QDD required)
# ═══════════════════════════════════════════════════════════════════
print("\n=== TEST 2: S4 Harmonic (Backfill) ===")
e2 = QuantumSetupEngine()
result2 = e2.evaluate({
    "regime": 1, "conf": 120, "qho_n": 2,
    "lbm_signal": "LAMINAR_FLOW",
    "qgc_pull": 0.0,  # Not available in backfill
    "qdd_fidelity": 0.0,  # Not available in backfill
}, backfill=True)

assert len(result2) > 0, "FAIL: No S4 signal"
s4 = [s for s in result2 if 'S4' in s['setup']]
assert len(s4) == 1, f"FAIL: Expected S4, got {result2}"
print(f"  ✅ S4 BACKFILL PASS: {s4[0]['setup']} {s4[0]['direction']}")

# ═══════════════════════════════════════════════════════════════════
# TEST 3: S7 Tsunami Macro (Backfill — regime streak)
# ═══════════════════════════════════════════════════════════════════
print("\n=== TEST 3: S7 Tsunami (Backfill — Regime Streak) ===")
e3 = QuantumSetupEngine()
triggered = False
for i in range(15):
    r = e3.evaluate({
        "regime": 1, "conf": 120, "ricci": 0.5, "qho_n": 1,
    }, backfill=True)
    if r and any('S7' in s['setup'] for s in r):
        print(f"  ✅ S7 BACKFILL triggered at bar {i+1}: {r[0]['setup']} {r[0]['direction']}")
        triggered = True
        break

assert triggered, "FAIL: S7 never triggered"

# ═══════════════════════════════════════════════════════════════════
# TEST 4: S2 Vacuum Annihilation (Backfill — QCD + Ricci + Regime)
# ═══════════════════════════════════════════════════════════════════
print("\n=== TEST 4: S2 Vacuum (Backfill) ===")
e4 = QuantumSetupEngine()
result4 = e4.evaluate({
    "regime": 1, "conf": 80, "prev_regime": 0,
    "qcd_signal": "FISSION_EXPANSION_UP",
    "ricci": 2.5,
}, backfill=True)

s2 = [s for s in result4 if 'S2' in s['setup']]
assert len(s2) == 1, f"FAIL: Expected S2, got {result4}"
print(f"  ✅ S2 BACKFILL PASS: {s2[0]['setup']} {s2[0]['direction']}")

# ═══════════════════════════════════════════════════════════════════
# TEST 5: S5 Topological Collapse (Backfill — Ricci + QHO)
# ═══════════════════════════════════════════════════════════════════
print("\n=== TEST 5: S5 Collapse (Backfill) ===")
e5 = QuantumSetupEngine()
result5 = e5.evaluate({
    "qho_n": 6, "ricci": 4.0,
    "lbm_signal": "FLUID_RUPTURE_BEAR",
    "regime": 1,
}, backfill=True)

s5 = [s for s in result5 if 'S5' in s['setup']]
assert len(s5) == 1, f"FAIL: Expected S5, got {result5}"
print(f"  ✅ S5 BACKFILL PASS: {s5[0]['setup']} {s5[0]['direction']}")

# ═══════════════════════════════════════════════════════════════════
# TEST 6: S1 and S6 should NOT fire in backfill
# ═══════════════════════════════════════════════════════════════════
print("\n=== TEST 6: S1 & S6 DISABLED in Backfill ===")
e6 = QuantumSetupEngine()
result6 = e6.evaluate({
    "z_pinch_signal": "Z_PINCH_PLASMA_TOP", "qgc_pull": 5.0,
    "lbm_signal": "FLUID_RUPTURE_BULL", "rht_flash": 1.0, "qho_n": 5,
    "qte_prob": 0.95, "rmt_signal": "PURE_SIGNAL_x3.0",
    "qcd_signal": "FISSION_EXPANSION_UP", "qrw_signal": "QUANTUM_ACCUMULATION_BULL",
}, backfill=True)

s1_found = any('S1' in s['setup'] for s in result6)
s6_found = any('S6' in s['setup'] for s in result6)
assert not s1_found, f"FAIL: S1 should not fire in backfill"
assert not s6_found, f"FAIL: S6 should not fire in backfill"
print(f"  ✅ S1 DISABLED: {not s1_found}")
print(f"  ✅ S6 DISABLED: {not s6_found}")

print("\n🏆 ALL TESTS PASSED — Backfill mode operational")
