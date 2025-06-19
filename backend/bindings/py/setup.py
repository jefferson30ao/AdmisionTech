import setuptools
import pybind11

from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools.command.build_ext import build_ext as _build_ext

class BuildExt(_build_ext):
    def build_extensions(self):
        if self.compiler.compiler_type == 'mingw32':
            for ext in self.extensions:
                ext.extra_compile_args = ['-std=c++17']
                # ext.extra_link_args = [] # Optional
        super().build_extensions()

ext_modules = [
    Pybind11Extension(
        "pyevalcore",
        ["pyevalcore_binding.cpp", "../../src/evaluator_serial.cpp"],
        include_dirs=[pybind11.get_include(), "../../include"],
        language="c++",
    ),
]

setup_kwargs = {
    "ext_modules": ext_modules,
    "cmdclass": {"build_ext": BuildExt},
}

setuptools.setup(
    name="pyevalcore",
    version="0.0.1",
    author="Your Name",
    author_email="your.email@example.com",
    description="A C++ extension for evaluating expressions",
    long_description="A C++ extension for evaluating expressions",
    ext_modules=ext_modules,
    cmdclass=setup_kwargs["cmdclass"],
    zip_safe=False,
    setup_requires=["pybind11>=2.6.0"],
)