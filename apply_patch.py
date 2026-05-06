import re

# PATCH q_math_node.py
file_path = r'D:\AI Brain\US30\q_math_node.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
'''            # 7. CYT Ricci Flow Step
            ricci_curvature = 0.0
            try:''',
'''            # 7. CYT Ricci Flow Step
            ricci_curvature = 0.0
            cyt_danger = 0.0
            try:'''
)

content = content.replace(
'''                flow = self.cyt.analyze_manifold_flow(data_10d)
                def_array = flow["deformation"]
                if len(def_array) > 0:
                    ricci_curvature = def_array[-1]
            except Exception as e:''',
'''                flow = self.cyt.analyze_manifold_flow(data_10d)
                def_array = flow["deformation"]
                danger_array = self.cyt.calculate_danger_zones(data_10d, window=20, threshold=0.5)
                if len(def_array) > 0:
                    ricci_curvature = def_array[-1]
                    cyt_danger = danger_array[-1]
            except Exception as e:'''
)

content = content.replace(
'''                self.current_state["qcd_signal"] = qcd_signal
                self.current_state["ricci_curvature"] = ricci_curvature''',
'''                self.current_state["qcd_signal"] = qcd_signal
                self.current_state["ricci_curvature"] = ricci_curvature
                self.current_state["cyt_danger"] = cyt_danger'''
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

# PATCH Aethelgard_Swarm.py
file_path_swarm = r'D:\AI Brain\US30\Aethelgard_Swarm.py'
with open(file_path_swarm, 'r', encoding='utf-8') as f:
    content_swarm = f.read()

content_swarm = content_swarm.replace(
'''        self.qrw_cache = []
        self.rht_cache = []
        self.genesis_count = 0''',
'''        self.qrw_cache = []
        self.rht_cache = []
        self.qcd_cache = []
        self.cyt_danger_cache = []
        self.genesis_count = 0'''
)

content_swarm = content_swarm.replace(
'''                self.z_pinch_cache.append("0")
                self.qrw_cache.append("0")
                scores_hist.append(0)''',
'''                self.z_pinch_cache.append("0")
                self.qrw_cache.append("0")
                self.qcd_cache.append("0")
                self.cyt_danger_cache.append("0")
                scores_hist.append(0)'''
)

content_swarm = content_swarm.replace(
'''            self.z_pinch_cache.append("0")
            self.qrw_cache.append("0")
            self.sec_cache.append("0|0|0")''',
'''            self.z_pinch_cache.append("0")
            self.qrw_cache.append("0")
            self.qcd_cache.append("0")
            self.cyt_danger_cache.append("0")
            self.sec_cache.append("0|0|0")'''
)

content_swarm = content_swarm.replace(
'''                    # 1. Limpa os caches neurais para forçar recalculo no Python
                    self.regimes_cache.clear()
                    self.sec_cache.clear()
                    self.dots_cache.clear()''',
'''                    # 1. Limpa os caches neurais para forçar recalculo no Python
                    self.regimes_cache.clear()
                    self.sec_cache.clear()
                    self.dots_cache.clear()
                    self.qcd_cache.clear()
                    self.cyt_danger_cache.clear()'''
)

content_swarm = content_swarm.replace(
'''                            self.z_pinch_cache.pop(0); self.z_pinch_cache.append("0")
                            self.qrw_cache.pop(0); self.qrw_cache.append("0")
                            self.sec_cache.append("0|0|0")''',
'''                            self.z_pinch_cache.pop(0); self.z_pinch_cache.append("0")
                            self.qrw_cache.pop(0); self.qrw_cache.append("0")
                            self.qcd_cache.pop(0); self.qcd_cache.append("0")
                            self.cyt_danger_cache.pop(0); self.cyt_danger_cache.append("0")
                            self.sec_cache.append("0|0|0")'''
)

content_swarm = content_swarm.replace(
'''                        if qrw_signal == "HIDDEN_ACCUMULATION_BULL": self.qrw_cache[-1] = "1"
                        elif qrw_signal == "HIDDEN_DISTRIBUTION_BEAR": self.qrw_cache[-1] = "2"
                        
                        sec_str = "0|0|0"''',
'''                        if qrw_signal == "HIDDEN_ACCUMULATION_BULL": self.qrw_cache[-1] = "1"
                        elif qrw_signal == "HIDDEN_DISTRIBUTION_BEAR": self.qrw_cache[-1] = "2"
                        
                        qcd_signal = q_state.get("qcd_signal", "CONFINED")
                        cyt_danger = q_state.get("cyt_danger", 0.0)
                        
                        if "FISSION_EXPANSION_UP" in qcd_signal: self.qcd_cache[-1] = "1"
                        elif "FISSION_EXPANSION_DOWN" in qcd_signal: self.qcd_cache[-1] = "2"
                        else: self.qcd_cache[-1] = "0"
                        
                        self.cyt_danger_cache[-1] = str(int(cyt_danger))
                        
                        sec_str = "0|0|0"'''
)

content_swarm = content_swarm.replace(
'''                        cyt_danger_cache = ["0"] * len(self.regimes_cache) # Pode ser implementado no yield_governor depois
                        rht_status_local = "PURIFYING"
                        
                        nexus_data_str = f"0;0;{status_final};{self.signals_cache[-1]};{','.join(display_regimes)};{inst_avg:.2f};{health/100:.2f};{','.join(self.signals_cache)};{','.join(self.dots_cache)};{inst_avg:.2f};{cloud_str};{lbm_signal};{z_pinch_signal};{rmt_signal};{qrw_signal};{','.join(self.lbm_cache)};{','.join(self.z_pinch_cache)};{','.join(self.qrw_cache)};{','.join(cyt_danger_cache)};{sec_str};{','.join(self.sec_cache)};{rht_status_local};{','.join(self.rht_cache)}"''',
'''                        rht_status_local = "PURIFYING"
                        
                        nexus_data_str = f"0;0;{status_final};{self.signals_cache[-1]};{','.join(display_regimes)};{inst_avg:.2f};{health/100:.2f};{','.join(self.signals_cache)};{','.join(self.dots_cache)};{inst_avg:.2f};{cloud_str};{lbm_signal};{z_pinch_signal};{rmt_signal};{qrw_signal};{','.join(self.lbm_cache)};{','.join(self.z_pinch_cache)};{','.join(self.qrw_cache)};{','.join(self.cyt_danger_cache)};{sec_str};{','.join(self.sec_cache)};{rht_status_local};{','.join(self.rht_cache)};{qcd_signal};{','.join(self.qcd_cache)}"'''
)

with open(file_path_swarm, 'w', encoding='utf-8') as f:
    f.write(content_swarm)
print("Patch aplicado.")