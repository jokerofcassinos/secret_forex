import re

with open(r'd:\AI Brain\US30\Code\MQL5\Nexus_Observer.mq5', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace MSNR parsing block
old1 = '// --- MSNR PARSING (v6.0) ---'
new1_start = '// --- SETUP ENGINE PARSING (v1.0) ---'

if old1 in content:
    # Find the full block from MSNR PARSING to DrawMSNRHistorySignals
    start_idx = content.index(old1)
    # Find end marker
    end_marker = 'DrawMSNRHistorySignals(msnrHistory);'
    end_idx = content.index(end_marker) + len(end_marker)
    
    old_block = content[start_idx:end_idx]
    
    new_block = '''// --- SETUP ENGINE PARSING (v1.0) ---
     string setupTel = (ArraySize(parts) > 39) ? parts[39] : "NO_SETUP";

   DrawModernDashboard(statusTxt, instAvgPrice, health, rhtStatus, lbm_signal, z_signal, qrw_signal, secData, rmt_signal, ricci_c, h_entropy, (is_collapsed == "1"), rhtFlash, qddFidelity, qteProb, qteAdvice, qhoN, qhoStability, qhoStatus, mhdStrength, setupTel);

     // --- SETUP VISUALS ---
     DrawSetupSignal(setupTel);'''
    
    content = content.replace(old_block, new_block)
    print('BLOCK 1 REPLACED')
else:
    print('BLOCK 1 NOT FOUND')

# 2. Replace MSNR Fidelity HUD row
old2 = '// --- MSNR FIDELITY ---'
if old2 in content:
    start_idx = content.index(old2)
    end_marker = "rowY += 12;\n"
    # Find the specific rowY += 12 after MSNR block
    search_from = start_idx
    end_idx = content.index(end_marker, search_from) + len(end_marker)
    
    old_block2 = content[start_idx:end_idx]
    
    new_block2 = '''// --- ACTIVE SETUP DISPLAY ---
     string setupDisplayName = "No Setup";
     color setupClr2 = RGB(80, 85, 100);
     if(StringFind(setupTel, "S1_") >= 0) { setupDisplayName = "Slingshot"; setupClr2 = RGB(255, 165, 0); }
     else if(StringFind(setupTel, "S2_") >= 0) { setupDisplayName = "Vacuum Kill"; setupClr2 = RGB(255, 50, 50); }
     else if(StringFind(setupTel, "S3_") >= 0) { setupDisplayName = "Bosonic Fire"; setupClr2 = RGB(255, 215, 0); }
     else if(StringFind(setupTel, "S4_") >= 0) { setupDisplayName = "Harmonic PB"; setupClr2 = RGB(0, 255, 180); }
     else if(StringFind(setupTel, "S5_") >= 0) { setupDisplayName = "!! COLLAPSE !!"; setupClr2 = RGB(255, 0, 85); }
     else if(StringFind(setupTel, "S6_") >= 0) { setupDisplayName = "Tunneling"; setupClr2 = RGB(0, 200, 255); }
     else if(StringFind(setupTel, "S7_") >= 0) { setupDisplayName = "TSUNAMI MACRO"; setupClr2 = RGB(0, 255, 255); }
     
     string setupDir2 = "";
     if(StringFind(setupTel, "LONG") >= 0) setupDir2 = " LONG";
     else if(StringFind(setupTel, "SHORT") >= 0) setupDir2 = " SHORT";
     
     DrawHUDRow("NEXUS_HUD_L_SETUP", "Active Setup", setupDisplayName + setupDir2, setupClr2, baseX, rowY, panelW, corner);
     rowY += rowH;
'''
    
    content = content.replace(old_block2, new_block2)
    print('BLOCK 2 REPLACED')
else:
    print('BLOCK 2 NOT FOUND')

with open(r'd:\AI Brain\US30\Code\MQL5\Nexus_Observer.mq5', 'w', encoding='utf-8') as f:
    f.write(content)
print('DONE - All MSNR references purged from MQ5')
