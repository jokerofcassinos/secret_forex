import os
import sys
import subprocess

def build_cyt():
    print("[NEXUS] Compilando CYT Engine (Ricci Tensor & AdS/CFT)...")
    
    cpp_compiler = r"D:\msys64\mingw64\bin\g++.exe"
    python_include = r"D:\Python313\Include"
    pybind11_include = r"D:\Python313\Lib\site-packages\pybind11\include"
    python_lib = r"D:\Python313"
    
    output_name = "cyt_engine.cp313-win_amd64.pyd"
    source_file = "src/cyt/cyt_engine.cpp"
    
    cmd = [
        cpp_compiler,
        "-shared",
        "-O3",
        "-ffast-math",
        "-std=c++17",
        "-DNDEBUG",
        "-DMS_WIN64",
        "-fopenmp",
        f"-I{pybind11_include}",
        f"-I{python_include}",
        f"-L{python_lib}",
        "-lpython313",
        "-o", output_name,
        source_file
    ]
    
    try:
        subprocess.check_call(cmd)
        print(f"SUCCESS: CYT Engine compilado como {output_name}")
        
        import shutil
        shutil.copy(output_name, "../../" + output_name)
        
        bin_dir = "bin"
        if not os.path.exists(bin_dir): os.makedirs(bin_dir)
        shutil.move(output_name, os.path.join(bin_dir, output_name))
        
    except Exception as e:
        print(f"FAIL: Erro na compilação do CYT: {e}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_cyt()