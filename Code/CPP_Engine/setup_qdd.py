import os
import sys
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import pybind11

class get_pybind_include(object):
    def __init__(self, user=False):
        self.user = user
    def __str__(self):
        return pybind11.get_include(self.user)

ext_modules = [
    Extension(
        'qdd_engine',
        ['src/qdd/qdd_engine.cpp'],
        include_dirs=[
            get_pybind_include(),
            get_pybind_include(user=True)
        ],
        language='c++'
    ),
]

class BuildExt(build_ext):
    c_opts = {
        'msvc': ['/EHsc', '/O2', '/openmp'],
        'unix': ['-O3', '-ffast-math', '-fopenmp', '-std=c++17']
    }
    
    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        for ext in self.extensions:
            ext.extra_compile_args = opts
        build_ext.build_extensions(self)

setup(
    name='qdd_engine',
    version='5.5.0',
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
)
