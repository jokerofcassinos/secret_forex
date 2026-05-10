import os
import subprocess
import sys
import sysconfig
import pybind11
import shutil

GCC = r"D:\msys64\mingw64\bin\g++.exe"
PYBIND_INC = pybind11.get_include()
PY_INC = sysconfig.get_path('include')
PY_LIBS = r"D:\Python313"
EXT_SUFFIX = sysconfig.get_config_var('EXT_SUFFIX') or '.cp313-win_amd64.pyd'

def build_schrodinger():
    name = "schrodinger_engine"
    src = "src/schrodinger/schrodinger_engine.cpp"
    output = f"{name}{EXT_SUFFIX}"
    
    print(f"--- Compilando {name} v24.0 (NEXUS ASI) ---")
    
    cmd = [
        GCC, "-shared", "-O3", "-ffast-math", "-std=c++17", "-fopenmp",
        "-D_USE_MATH_DEFINES", "-DNDEBUG", "-DMS_WIN64",
        f"-I{PYBIND_INC}", f"-I{PY_INC}", f"-L{PY_LIBS}",
        "-lpython313", "-o", output, src,
    ]
    
    print(f"Executando GCC...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"[OK] {name} gerado com sucesso.")
        
        # Deploy para a raiz
        dst_pyd = os.path.join("../../", output)
        print(f"Copiando para a raiz: {dst_pyd}")
        shutil.copy2(output, dst_pyd)
        print("[DEPLOY OK]")
        return True
    else:
        print(f"[ERRO] Falha na compilação de {name}")
        print(result.stderr)
        return False

if __name__ == "__main__":
    # Garante que estamos no diretório do script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_schrodinger()
