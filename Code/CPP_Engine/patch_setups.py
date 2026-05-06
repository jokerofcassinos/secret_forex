import glob
import os
import re

for setup_file in glob.glob("setup_*.py"):
    with open(setup_file, 'r') as f:
        content = f.read()
    
    # Simple replacement for known c_opts dictionary
    if "'msvc': ['/EHsc', '/O2']" in content:
        content = content.replace("'msvc': ['/EHsc', '/O2']", "'msvc': ['/EHsc', '/O2', '/openmp']")
        content = content.replace("'unix': ['-O3', '-ffast-math']", "'unix': ['-O3', '-ffast-math', '-fopenmp']")
        with open(setup_file, 'w') as f:
            f.write(content)
        print(f"Patched {setup_file} (BuildExt c_opts)")
    
    # For setup_rht.py style Extra Compile Args
    elif "extra_compile_args = ['/O2', '/fp:fast', '/DNDEBUG']" in content:
        content = content.replace("extra_compile_args = ['/O2', '/fp:fast', '/DNDEBUG']", "extra_compile_args = ['/O2', '/fp:fast', '/DNDEBUG', '/openmp']")
        with open(setup_file, 'w') as f:
            f.write(content)
        print(f"Patched {setup_file} (extra_compile_args)")

print("Done patching setups for OpenMP.")
