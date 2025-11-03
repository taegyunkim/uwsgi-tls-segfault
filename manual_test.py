#!/usr/bin/env python3
"""
Manual test to verify TLS object access after cleanup.
"""


def test_cpp_manual():
    print("Testing C++ module manually...")
    try:
        import cpp_tls_atexit

        # Initialize TLS object
        cpp_tls_atexit.initialize_tls()
        print("TLS initialized")

        # Force cleanup (this should free the TLS object)
        cpp_tls_atexit.force_cleanup()
        print("TLS cleanup forced")

        # Now try to access it (should segfault)
        print("Attempting to access freed TLS object...")
        cpp_tls_atexit.atexit_handler()
        print("Access succeeded - no segfault occurred")

    except Exception as e:
        print(f"Exception occurred: {e}")


def test_rust_manual():
    print("Testing Rust module manually...")
    try:
        import rust_tls_atexit

        # Initialize TLS object
        rust_tls_atexit.initialize_tls()
        print("TLS initialized")

        # Force cleanup (this should free the TLS object)
        rust_tls_atexit.force_cleanup()
        print("TLS cleanup forced")

        # Now try to access it (should segfault)
        print("Attempting to access freed TLS object...")
        rust_tls_atexit.atexit_handler()
        print("Access succeeded - no segfault occurred")

    except Exception as e:
        print(f"Exception occurred: {e}")


if __name__ == "__main__":
    print("Manual TLS Segfault Test")
    print("=" * 30)

    test_cpp_manual()
    print()
    test_rust_manual()
