"""
QUANTUM SETUP ENGINE v2.0 — AETHELGARD ASI
7 Setups Híbridos de Execução Swing/Long Position.

Suporta dois modos:
  - LIVE mode: Todos os indicadores disponíveis (RHT, RMT, QRW, QGC, QTE, QDD, etc.)
  - BACKFILL mode: Apenas regime, LBM, QCD, QHO, Ricci disponíveis.
    Condições são relaxadas para produzir sinais com dados limitados.

Setups implementados:
  S1: Estilingue Gravitacional  (Reversal pós-stop-hunt) — Live only
  S2: Aniquilação de Vácuo      (FVG fill + regime change)
  S3: Condensado Bosônico       (Breakout de squeeze)
  S4: Ressonância Harmônica     (Pullback entry na tendência)
  S5: Colapso Topológico        (Reversão macro rara)
  S6: Tunelamento Institucional (Breakout carry) — Live only
  S7: Onda Tsunami Macro        (Position trade de semanas)
"""
import time


class QuantumSetupEngine:
    """
    Motor de Setups Quânticos: avalia 7 setups híbridos a cada tick.
    Mantém estado interno para tracking temporal (squeeze bars, streaks, etc).
    """

    def __init__(self):
        # ── State Tracking ──
        self.squeeze_bar_count = 0       # S3: barras consecutivas em BOSONIC_SQUEEZE
        self.prev_qdd_sign = 0           # S5: sinal anterior da fidelidade QDD
        self.rht_heat_streak = 0         # S7: barras consecutivas com calor no mesmo sentido
        self.qdd_streak = 0              # S7: barras consecutivas com fidelidade alta
        self.qrw_streak = 0              # S7: barras consecutivas com skew no mesmo sentido
        self.regime_streak = 0           # S7 backfill: regime consecutivo
        self.prev_regime_dir = 0         # S7 backfill: regime anterior
        self.prev_rht_heat_sign = 0      # S5: sinal de calor anterior
        self.last_setup_time = 0         # Cooldown: timestamp do último sinal emitido
        self.cooldown_seconds = 30       # Cooldown mínimo entre sinais do mesmo setup

        # ── Emitted Signals Log ──
        self.active_setups = []          # Lista de setups ativos no tick atual
        self.setup_history = []          # Histórico recente (últimos 50)

    def _parse_rmt_power(self, rmt_signal_str: str) -> float:
        """Extrai power_ratio da string RMT (ex: 'PURE_SIGNAL_x3.2' → 3.2)."""
        try:
            if "_x" in rmt_signal_str:
                return float(rmt_signal_str.split("_x")[-1])
        except (ValueError, IndexError):
            pass
        return 0.0

    def _is_rmt_pure(self, rmt_signal_str: str) -> bool:
        return "PURE_SIGNAL" in rmt_signal_str

    def _parse_qrw_direction(self, qrw_signal: str) -> int:
        """Retorna +1 (bull), -1 (bear), 0 (neutral)."""
        if "BULL" in qrw_signal or "LONG" in qrw_signal:
            return 1
        if "BEAR" in qrw_signal or "SHORT" in qrw_signal:
            return -1
        return 0

    def _parse_rht_flash_direction(self, rht_flash: float) -> int:
        """RHT flash: +1.0 = bull, -1.0 = bear, 0 = neutral."""
        if rht_flash > 0.5:
            return 1
        if rht_flash < -0.5:
            return -1
        return 0

    def _has_live_data(self, ctx) -> bool:
        """Detecta se os dados de live estão disponíveis."""
        return ctx.get("rht_flash", 0.0) != 0.0 or \
               self._is_rmt_pure(ctx.get("rmt_signal", "")) or \
               ctx.get("qgc_pull", 0.0) > 0 or \
               abs(ctx.get("qdd_fidelity", 0.0)) > 0.01

    # ──────────────────────────────────────────────────────────────────────
    # SETUP 3: CONDENSADO BOSÔNICO IGNIÇÃO 🔥
    # LBM Squeeze ≥N bars → QCD Fissão
    # Live: + RHT Flash + RMT Pure + QRW Skew (≥2 confirmações)
    # Backfill: Squeeze + Fissão é suficiente (≥0 confirmações)
    # ──────────────────────────────────────────────────────────────────────
    def _eval_s3_bosonic_ignition(self, ctx, backfill=False) -> dict | None:
        lbm = ctx.get("lbm_signal", "")
        qcd = ctx.get("qcd_signal", "")
        rht_flash = ctx.get("rht_flash", 0.0)
        rmt = ctx.get("rmt_signal", "")
        qrw = ctx.get("qrw_signal", "")

        min_squeeze = 3 if backfill else 5
        min_confirms = 0 if backfill else 2

        # Track squeeze duration
        if "BOSONIC_SQUEEZE" in lbm:
            self.squeeze_bar_count += 1
        else:
            # Check ignition RIGHT after squeeze ends
            if self.squeeze_bar_count >= min_squeeze:
                direction = 0
                if "FISSION_EXPANSION_UP" in qcd:
                    direction = 1
                elif "FISSION_EXPANSION_DOWN" in qcd:
                    direction = -1

                if direction != 0:
                    confirms = 0
                    if not backfill:
                        rht_dir = self._parse_rht_flash_direction(rht_flash)
                        qrw_dir = self._parse_qrw_direction(qrw)
                        rmt_pure = self._is_rmt_pure(rmt)
                        if rht_dir == direction: confirms += 1
                        if qrw_dir == direction: confirms += 1
                        if rmt_pure: confirms += 1

                    saved_count = self.squeeze_bar_count
                    self.squeeze_bar_count = 0

                    if confirms >= min_confirms:
                        return {
                            "setup": "S3_BOSONIC_IGNITION",
                            "direction": "LONG" if direction == 1 else "SHORT",
                            "dir_int": direction,
                            "confidence": max(1, confirms),
                            "squeeze_bars": saved_count,
                        }

            self.squeeze_bar_count = 0

        return None

    # ──────────────────────────────────────────────────────────────────────
    # SETUP 4: RESSONÂNCIA HARMÔNICA DIMENSIONAL 🌊
    # Regime TSUNAMI + QHO shell n=2/3
    # Live: + QGC gravity + QDD fidelity
    # Backfill: Regime + QHO pullback level é suficiente
    # ──────────────────────────────────────────────────────────────────────
    def _eval_s4_harmonic_resonance(self, ctx, backfill=False) -> dict | None:
        regime = ctx.get("regime", 0)
        conf = ctx.get("conf", 0)
        qho_n = ctx.get("qho_n", 0)
        qgc_pull = ctx.get("qgc_pull", 0.0)
        lbm = ctx.get("lbm_signal", "")
        qdd_f = ctx.get("qdd_fidelity", 0.0)

        if regime == 0 or conf < 80:
            return None

        # Price at intermediate energy shell (pullback to n=2 or n=3)
        if qho_n < 2 or qho_n > 3:
            return None

        direction = 1 if regime == 1 else -1
        confidence = 1

        if backfill:
            # In backfill: regime + QHO shell alignment is enough
            confidence = 2
        else:
            # Live: require QGC and QDD
            if qgc_pull < 1.5:
                return None
            fidelity_aligned = (direction == 1 and qdd_f > 0.5) or (direction == -1 and qdd_f < -0.5)
            if not fidelity_aligned:
                return None
            confidence = 3 if abs(qdd_f) > 0.7 else 2

        # LBM check (both modes)
        lbm_ok = ("RUPTURE_BULL" in lbm and direction == 1) or \
                 ("RUPTURE_BEAR" in lbm and direction == -1) or \
                 ("LAMINAR" in lbm) or ("SQUEEZE" in lbm)

        if not lbm_ok:
            return None

        return {
            "setup": "S4_HARMONIC_RESONANCE",
            "direction": "LONG" if direction == 1 else "SHORT",
            "dir_int": direction,
            "confidence": confidence,
            "qho_shell": qho_n,
        }

    # ──────────────────────────────────────────────────────────────────────
    # SETUP 1: ESTILINGUE GRAVITACIONAL 🏹
    # MHD Z-Pinch → QGC gravity → LBM reverse rupture → RHT flash → QHO n≥4
    # LIVE ONLY (requires Z-Pinch which is not available in backfill)
    # ──────────────────────────────────────────────────────────────────────
    def _eval_s1_gravitational_slingshot(self, ctx, backfill=False) -> dict | None:
        if backfill:
            return None  # Z-Pinch not available in backfill

        z_pinch = ctx.get("z_pinch_signal", "")
        qgc_pull = ctx.get("qgc_pull", 0.0)
        lbm = ctx.get("lbm_signal", "")
        rht_flash = ctx.get("rht_flash", 0.0)
        qho_n = ctx.get("qho_n", 0)

        if "Z_PINCH_PLASMA" not in z_pinch:
            return None

        sweep_is_top = "TOP" in z_pinch
        reversal_dir = -1 if sweep_is_top else 1

        if qgc_pull < 2.0:
            return None
        if qho_n < 4:
            return None

        rht_dir = self._parse_rht_flash_direction(rht_flash)
        lbm_reversal = ("RUPTURE_BULL" in lbm and reversal_dir == 1) or \
                       ("RUPTURE_BEAR" in lbm and reversal_dir == -1)

        confirms = 0
        if rht_dir == reversal_dir: confirms += 1
        if lbm_reversal: confirms += 1

        if confirms < 1:
            return None

        return {
            "setup": "S1_GRAVITATIONAL_SLINGSHOT",
            "direction": "LONG" if reversal_dir == 1 else "SHORT",
            "dir_int": reversal_dir,
            "confidence": confirms + 1,
            "sweep_type": "TOP_SWEEP" if sweep_is_top else "BOTTOM_SWEEP",
            "qho_energy": qho_n,
        }

    # ──────────────────────────────────────────────────────────────────────
    # SETUP 6: TUNELAMENTO INSTITUCIONAL 🔮
    # QTE > 0.85 + RMT Pure + QCD Fissão + QRW confirms
    # LIVE ONLY (requires QTE + RMT)
    # ──────────────────────────────────────────────────────────────────────
    def _eval_s6_institutional_tunneling(self, ctx, backfill=False) -> dict | None:
        if backfill:
            return None  # QTE not available in backfill

        qte_prob = ctx.get("qte_prob", 0.0)
        rmt = ctx.get("rmt_signal", "")
        qcd = ctx.get("qcd_signal", "")
        qrw = ctx.get("qrw_signal", "")

        if qte_prob < 0.80:
            return None
        if not self._is_rmt_pure(rmt):
            return None

        direction = 0
        if "FISSION_EXPANSION_UP" in qcd:
            direction = 1
        elif "FISSION_EXPANSION_DOWN" in qcd:
            direction = -1
        if direction == 0:
            return None

        qrw_dir = self._parse_qrw_direction(qrw)
        qrw_ok = (qrw_dir == direction)

        return {
            "setup": "S6_INSTITUTIONAL_TUNNELING",
            "direction": "LONG" if direction == 1 else "SHORT",
            "dir_int": direction,
            "confidence": 3 if qrw_ok else 2,
            "tunneling_prob": qte_prob,
            "rmt_power": self._parse_rmt_power(rmt),
        }

    # ──────────────────────────────────────────────────────────────────────
    # SETUP 7: ONDA TSUNAMI MACRO 🌊🌊
    # Live: Regime conf>100 + RHT streak + QDD streak + Ricci stable + QHO n≤2
    # Backfill: Regime conf>100 streak ≥ 8 bars + Ricci stable + QHO n≤2
    # ──────────────────────────────────────────────────────────────────────
    def _eval_s7_tsunami_macro(self, ctx, backfill=False) -> dict | None:
        regime = ctx.get("regime", 0)
        conf = ctx.get("conf", 0)
        ricci = ctx.get("ricci", 0.0)
        qho_n = ctx.get("qho_n", 0)

        if regime == 0 or conf < 100:
            self.rht_heat_streak = 0
            self.qdd_streak = 0
            self.qrw_streak = 0
            self.regime_streak = 0
            self.prev_regime_dir = 0
            return None

        direction = 1 if regime == 1 else -1

        if backfill:
            # In backfill: use regime streak instead of RHT/QDD/QRW
            if direction == self.prev_regime_dir:
                self.regime_streak += 1
            else:
                self.regime_streak = 1
            self.prev_regime_dir = direction

            if self.regime_streak < 8:
                return None
            if ricci > 1.5:
                return None
            if qho_n > 2:
                return None

            return {
                "setup": "S7_TSUNAMI_MACRO",
                "direction": "LONG" if direction == 1 else "SHORT",
                "dir_int": direction,
                "confidence": min(3, 1 + (self.regime_streak // 8)),
                "regime_streak": self.regime_streak,
            }
        else:
            # Live mode: full RHT/QDD/QRW streaks
            rht_flash = ctx.get("rht_flash", 0.0)
            qdd_f = ctx.get("qdd_fidelity", 0.0)
            qrw = ctx.get("qrw_signal", "")

            rht_dir = self._parse_rht_flash_direction(rht_flash)
            if rht_dir == direction:
                self.rht_heat_streak += 1
            else:
                self.rht_heat_streak = 0

            if (direction == 1 and qdd_f > 0.6) or (direction == -1 and qdd_f < -0.6):
                self.qdd_streak += 1
            else:
                self.qdd_streak = 0

            qrw_dir = self._parse_qrw_direction(qrw)
            if qrw_dir == direction:
                self.qrw_streak += 1
            else:
                self.qrw_streak = 0

            if self.rht_heat_streak < 10:
                return None
            if self.qdd_streak < 5:
                return None
            if ricci > 1.5:
                return None
            if qho_n > 2:
                return None

            return {
                "setup": "S7_TSUNAMI_MACRO",
                "direction": "LONG" if direction == 1 else "SHORT",
                "dir_int": direction,
                "confidence": min(5, 2 + (self.rht_heat_streak // 10)),
                "rht_streak": self.rht_heat_streak,
                "qdd_streak": self.qdd_streak,
            }

    # ──────────────────────────────────────────────────────────────────────
    # SETUP 2: ANIQUILAÇÃO DE VÁCUO 💥
    # Live: S-Matrix + QDD + QCD Fissão + CYT stress + Regime flip
    # Backfill: QCD Fissão + Ricci stress + Regime transition
    # ──────────────────────────────────────────────────────────────────────
    def _eval_s2_vacuum_annihilation(self, ctx, backfill=False) -> dict | None:
        qcd = ctx.get("qcd_signal", "")
        ricci = ctx.get("ricci", 0.0)
        regime = ctx.get("regime", 0)
        prev_regime = ctx.get("prev_regime", 0)

        # QCD fission (displacement) — required in both modes
        direction = 0
        if "FISSION_EXPANSION_UP" in qcd:
            direction = 1
        elif "FISSION_EXPANSION_DOWN" in qcd:
            direction = -1
        if direction == 0:
            return None

        # Topology must be stressed — required in both modes
        if ricci < 1.0:
            return None

        # Regime must be changing
        regime_transitioning = (prev_regime != regime and regime != 0) or \
                              (prev_regime == 0 and regime != 0)
        if not regime_transitioning:
            return None

        if not backfill:
            # Live: also require S-Matrix and QDD
            sec_metrics = ctx.get("sec_metrics")
            qdd_f = ctx.get("qdd_fidelity", 0.0)

            smatrix_strength = 0.0
            if sec_metrics and isinstance(sec_metrics, dict):
                smatrix_strength = sec_metrics.get("singularity_strength", 0.0)
            if smatrix_strength < 0.08:
                return None
            if abs(qdd_f) < 0.4:
                return None

        return {
            "setup": "S2_VACUUM_ANNIHILATION",
            "direction": "LONG" if direction == 1 else "SHORT",
            "dir_int": direction,
            "confidence": 2 if backfill else 3,
            "ricci": ricci,
        }

    # ──────────────────────────────────────────────────────────────────────
    # SETUP 5: COLAPSO TOPOLÓGICO TERMINAL ☠️
    # Live: CYT collapse + QHO n≥5 + QDD flip
    # Backfill: Ricci > 3.0 + QHO n≥5 + LBM rupture
    # ──────────────────────────────────────────────────────────────────────
    def _eval_s5_topological_collapse(self, ctx, backfill=False) -> dict | None:
        qho_n = ctx.get("qho_n", 0)
        lbm = ctx.get("lbm_signal", "")
        ricci = ctx.get("ricci", 0.0)

        if qho_n < 5:
            return None

        if backfill:
            # Backfill: Use extreme Ricci + QHO + LBM as proxy
            if ricci < 3.0:
                return None

            # Direction from LBM rupture
            direction = 0
            if "RUPTURE_BULL" in lbm:
                direction = 1
            elif "RUPTURE_BEAR" in lbm:
                direction = -1
            # If no rupture, use regime direction
            if direction == 0:
                regime = ctx.get("regime", 0)
                if regime == 1:
                    direction = -1  # Bull exhaustion → reverse SHORT
                elif regime == 2:
                    direction = 1   # Bear exhaustion → reverse LONG
                else:
                    return None

            return {
                "setup": "S5_TOPOLOGICAL_COLLAPSE",
                "direction": "LONG" if direction == 1 else "SHORT",
                "dir_int": direction,
                "confidence": 2,
                "qho_energy": qho_n,
            }
        else:
            # Live mode: full collapse detection
            is_collapsed = ctx.get("is_collapsed", False)
            qdd_f = ctx.get("qdd_fidelity", 0.0)

            if not is_collapsed:
                return None

            curr_qdd_sign = 1 if qdd_f > 0.3 else (-1 if qdd_f < -0.3 else 0)
            qdd_flipped = (self.prev_qdd_sign != 0 and curr_qdd_sign != 0 and
                           self.prev_qdd_sign != curr_qdd_sign)
            self.prev_qdd_sign = curr_qdd_sign

            if not qdd_flipped:
                return None

            direction = curr_qdd_sign
            confirms = 2
            z_pinch = ctx.get("z_pinch_signal", "")
            if "Z_PINCH" in z_pinch: confirms += 1
            if "RUPTURE" in lbm: confirms += 1

            return {
                "setup": "S5_TOPOLOGICAL_COLLAPSE",
                "direction": "LONG" if direction == 1 else "SHORT",
                "dir_int": direction,
                "confidence": confirms,
                "qho_energy": qho_n,
            }

    # ═══════════════════════════════════════════════════════════════════════
    # MASTER EVALUATOR
    # ═══════════════════════════════════════════════════════════════════════
    def evaluate(self, ctx: dict, backfill: bool = False) -> list:
        """
        Avalia todos os 7 setups contra o contexto atual.

        Args:
            ctx: Dict with all quantum state data
            backfill: If True, relax conditions for historical analysis

        Returns list of triggered setup dicts (can be empty).
        """
        self.active_setups = []

        evaluators = [
            self._eval_s3_bosonic_ignition,
            self._eval_s4_harmonic_resonance,
            self._eval_s1_gravitational_slingshot,
            self._eval_s6_institutional_tunneling,
            self._eval_s7_tsunami_macro,
            self._eval_s2_vacuum_annihilation,
            self._eval_s5_topological_collapse,
        ]

        for evaluator in evaluators:
            try:
                result = evaluator(ctx, backfill=backfill)
                if result is not None:
                    result["timestamp"] = time.time()
                    self.active_setups.append(result)
            except Exception:
                pass

        for s in self.active_setups:
            self.setup_history.append(s)
            if len(self.setup_history) > 50:
                self.setup_history.pop(0)

        return self.active_setups

    def get_strongest_signal(self) -> dict | None:
        """Retorna o setup com maior confiança entre os ativos."""
        if not self.active_setups:
            return None
        return max(self.active_setups, key=lambda s: s.get("confidence", 0))

    def format_telemetry(self) -> str:
        """Formata os setups ativos como string de telemetria para o HUD."""
        if not self.active_setups:
            return "NO_SETUP"

        parts = []
        for s in self.active_setups:
            name = s["setup"]
            direction = s["direction"]
            conf = s["confidence"]
            parts.append(f"{name}:{direction}:C{conf}")

        return "|".join(parts)
