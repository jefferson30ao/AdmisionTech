import setuptools
import pybind11
import os
from setuptools.command.build_ext import build_ext as _build_ext
from pybind11.setup_helpers import Pybind11Extension

# Custom build_ext to handle CUDA compilation
class CustomBuildExt(_build_ext):
    def build_extensions(self):
        cuda_compiler = os.environ.get('NVCC', 'nvcc')
        cuda_path = os.environ.get('CUDA_PATH')

        for ext in self.extensions:
            # Separate .cu sources from other sources
            cu_sources = [s for s in ext.sources if s.endswith('.cu')]
            ext.sources = [s for s in ext.sources if not s.endswith('.cu')]

            # Compile .cu files using nvcc
            for s in cu_sources:
                output_obj = os.path.join(self.build_temp, os.path.basename(s).replace('.cu', '.obj'))
                
                # CUDA compile arguments
                cuda_compile_args = [
                    '-c', s, '-o', output_obj,
                    '-Xcompiler', '/EHsc,/MD', # For MSVC host compiler
                    '-I' + pybind11.get_include(),
                    '-I' + os.path.abspath('../../include')
                ]
                if cuda_path:
                    cuda_compile_args.append(f'-I{cuda_path}/include')

                self.spawn([cuda_compiler] + cuda_compile_args)
                ext.extra_objects.append(output_obj)

            # Add common compile args for C++ files
            if self.compiler.compiler_type == 'msvc':
                ext.extra_compile_args += ['/EHsc', '/O2']
                if cuda_path:
                    ext.extra_compile_args.append(f'/I{cuda_path}/include')
            else:
                ext.extra_compile_args += ['-O3', '-std=c++17']

            # Add CUDA link args
            if cuda_path:
                if self.compiler.compiler_type == 'msvc':
                    ext.extra_link_args += [f'/LIBPATH:{cuda_path}/lib/x64', 'cudart_static.lib', 'cuda.lib']
                else:
                    ext.extra_link_args += [f'-L{cuda_path}/lib64', '-lcudart_static', '-lcuda'] # Assuming lib64 for Linux/Unix

        super().build_extensions()

ext_modules = [
    Pybind11Extension(
        "pyevalcore",
        ["pyevalcore_binding.cpp", "../../src/evaluator_serial.cpp", "../../src/evaluator_openmp.cpp", "../../../src/evaluator_cuda.cu"],
        include_dirs=[pybind11.get_include(), "../../include"],
        language="c++",
    ),
]

setuptools.setup(
    name="pyevalcore",
    version="0.0.1",
    author="Your Name",
    author_email="your.email@example.com",
    description="A C++ extension for evaluating expressions",
    long_description="A C++ extension for evaluating expressions",
    ext_modules=ext_modules,
    cmdclass={"build_ext": CustomBuildExt},
    zip_safe=False,
    setup_requires=["pybind11>=2.6.0"],
)
