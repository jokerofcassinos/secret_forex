"""
Fix: Remove aggressive ObjectsDeleteAll that causes visual flickering.
QCD and Setup objects are now updated in-place, not destroyed+recreated.
"""
with open(r'd:\AI Brain\US30\Code\MQL5\Nexus_Observer.mq5', 'r', encoding='utf-8') as f:
    content = f.read()

changes = 0

# 1. Remove NEXUS_QCD_ from the aggressive purge block
old1 = '   ObjectsDeleteAll(0, "NEXUS_QCD_");\n'
if old1 in content:
    content = content.replace(old1, '   // [ANTI-FLICKER] QCD objects updated in-place, not purged\n')
    changes += 1
    print("FIX 1: Removed NEXUS_QCD_ from global purge")

# 2. Remove NEXUS_SH_ purge from setup history section  
old2 = '     ObjectsDeleteAll(0, "NEXUS_SH_");\n'
if old2 in content:
    content = content.replace(old2, '     // [ANTI-FLICKER] Setup history objects updated in-place\n')
    changes += 1
    print("FIX 2: Removed NEXUS_SH_ from setup history purge")

# 3. Remove NEXUS_SETUP_ purge from DrawSetupSignal
old3 = '   // Clean previous setup markers\n   ObjectsDeleteAll(0, "NEXUS_SETUP_");\n'
if old3 in content:
    # Replace with indexed cleanup (max 5 items)
    new3 = '''   // [ANTI-FLICKER] Clean excess setup markers by index
   for(int c=5; c<10; c++) {
      ObjectDelete(0, "NEXUS_SETUP_DIA_" + IntegerToString(c));
      ObjectDelete(0, "NEXUS_SETUP_LBL_" + IntegerToString(c));
   }
'''
    content = content.replace(old3, new3)
    changes += 1
    print("FIX 3: Replaced NEXUS_SETUP_ purge with indexed cleanup")

# 4. Also remove NEX_MS_SIG_ and NEX_MSNR_ purge (remnants, now dead code)
old4 = '   ObjectsDeleteAll(0, "NEX_MS_SIG_");\n   ObjectsDeleteAll(0, "NEX_MSNR_");\n'
if old4 in content:
    content = content.replace(old4, '')
    changes += 1
    print("FIX 4: Removed dead NEX_MS_SIG_ and NEX_MSNR_ purge")

with open(r'd:\AI Brain\US30\Code\MQL5\Nexus_Observer.mq5', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"\nDONE: {changes} anti-flicker fixes applied")
