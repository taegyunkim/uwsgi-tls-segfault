#!/usr/bin/env python3
"""
Test script to demonstrate TLS destruction segfaults at exit time.
"""

import atexit
import os


def test_cpp_module():
    print("Testing C++ module...")
    try:
        import cpp_tls_atexit

        # Initialize TLS object
        cpp_tls_atexit.initialize_tls()

        # Register the atexit handler that will access the freed TLS object
        atexit.register(cpp_tls_atexit.atexit_handler)

        print("C++ module: TLS initialized and atexit handler registered")

    except ImportError as e:
        print(f"Failed to import C++ module: {e}")
        print("Build with: python setup.py build_ext --inplace")


def test_rust_module():
    print("Testing Rust module...")
    try:
        import rust_tls_atexit

        # Initialize TLS object
        rust_tls_atexit.initialize_tls()

        # Register the atexit handler that will access the freed TLS object
        atexit.register(rust_tls_atexit.atexit_handler)

        print("Rust module: TLS initialized and atexit handler registered")

    except ImportError as e:
        print(f"Failed to import Rust module: {e}")
        print("Build with: python setup.py build_ext --inplace")


print("TLS Atexit Segfault Demonstration")
print("=" * 40)

# Check TEST_MODULE environment variable, default to "cpp"
module = os.environ.get("TEST_MODULE", "cpp")

if module == 'cpp':
    test_cpp_module()
elif module == 'rust':
    test_rust_module()
else:
    print("Unsupported TEST_MODULE")

print("\nExiting... (segfault may occur here)")
print("The segfault happens because TLS objects are destroyed")
print("before atexit handlers run, causing access to freed memory.")


def application():
    pass
