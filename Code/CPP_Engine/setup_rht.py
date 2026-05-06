from setuptools import setup, Extension
import pybind11
import sys
import os

# Configuração de compilação otimizada para Windows
extra_compile_args = ['/O2', '/fp:fast', '/DNDEBUG', '/openmp'] if sys.platform == 'win32' else ['-O3', '-ffast-math']

ext_modules = [
    Extension(
        'rht_engine',
        ['src/rht/rht_engine.cpp'],
        include_dirs=[pybind11.get_include()],
        language='c++',
        extra_compile_args=extra_compile_args,
    ),
]

setup(
    name='rht_engine',
    version='1.0.0',
    author='NEXUS AGI',
    description='Ressonancia Holografica de Tensores (RHT) em C++',
    ext_modules=ext_modules,
    zip_safe=False,
)