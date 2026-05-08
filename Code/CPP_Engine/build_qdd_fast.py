import os
import subprocess
import sys

# NEXUS QDD FAST BUILDER
import sysconfig
target = "qdd"
cpp_file = f"src/{target}/{target}_engine.cpp"
# Usa o sufixo nativo do Python (ex: .cp313-win_amd64.pyd)
output_name = f"{target}_engine{sysconfig.get_config_var('EXT_SUFFIX')}"

# Configuração de Caminhos
python_include = f"{sys.prefix}/include"
python_lib = f"{sys.prefix}/libs"
pybind11_include = f"{sys.prefix}/Lib/site-packages/pybind11/include"

print(f"Executing Fast Build for: {target}_engine")

cmd = [
    "g++", "-O3", "-shared", "-std=c++17", "-fPIC", "-fopenmp",
    "-static-libgcc", "-static-libstdc++",
    f"-I{python_include}",
    f"-I{pybind11_include}",
    cpp_file,
    "-o", output_name,
    f"-L{python_lib}",
    "-lpython313"
]

try:
    subprocess.run(cmd, check=True)
    print(f"SUCCESS: {output_name}.pyd created.")
    
    # Deploy para bin/ e root
    import shutil
    shutil.copy(f"{output_name}.pyd", f"bin/{output_name}.pyd")
    shutil.copy(f"{output_name}.pyd", f"../../{output_name}.pyd")
    print("Deployed to bin/ and root.")
except Exception as e:
    print(f"ERROR: {e}")
