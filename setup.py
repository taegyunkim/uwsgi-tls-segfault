from setuptools import setup, Extension
from setuptools_rust import Binding, RustExtension
import pybind11
from pybind11.setup_helpers import build_ext


cpp_module = Extension(
    "cpp_tls_atexit",
    sources=["cpp_module.cpp"],
    include_dirs=[pybind11.get_include()],
    language="c++",
    extra_compile_args=["-std=c++17"],
)

rust_extensions = [
    RustExtension(
        "rust_tls_atexit",
        path="rust_module/Cargo.toml",
        binding=Binding.PyO3,
    )
]

setup(
    name="tls-atexit",
    ext_modules=[cpp_module],
    rust_extensions=rust_extensions,
    cmdclass={"build_ext": build_ext},
    zip_safe=False,
    python_requires=">=3.7",
    setup_requires=["setuptools-rust"],
)
