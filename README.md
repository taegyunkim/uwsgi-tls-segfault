# uwsgi-tls-segfault

A demonstration of Thread Local Storage (TLS) destruction timing issues that cause segmentation faults in uWSGI environments.

## Overview

This repository demonstrates a critical timing issue between Thread Local Storage (TLS) destruction and Python's `atexit` handlers in uWSGI deployments. While the code runs safely in standalone Python scripts, it segfaults when executed under uWSGI due to differences in process lifecycle management.

## The Problem

- **Standalone Python**: TLS objects are destroyed during normal interpreter shutdown, and atexit handlers may not execute reliably
- **uWSGI Environment**: Worker processes are forcibly terminated, creating a race condition where:
  1. `atexit` handlers are called during `Py_FinalizeEx()` 
  2. TLS objects are destroyed before/during atexit handler execution
  3. Atexit handlers attempt to access already-freed TLS memory → **SEGFAULT**

## Language Comparison

The repository includes implementations in both C++ and Rust to demonstrate different approaches to error handling:

- **C++ Version**: Direct segfault when accessing destroyed TLS objects (explicit dereference of `0xdeadbeef`)
- **Rust Version**: Graceful panic with `AccessError` when TLS access is attempted during destruction

## Usage

### Environment Variable Control

The test script uses the `TEST_MODULE` environment variable:

```bash
# Test C++ module (default)
python test_segfault.py

# Test Rust module  
TEST_MODULE=rust python test_segfault.py

# Test both modules
TEST_MODULE=both python test_segfault.py
```

### Standalone Testing (Safe)

```bash
python test_segfault.py
# Exit code: 0 (runs without segfault)
```

### uWSGI Testing (Demonstrates Segfault)

```bash
# C++ version - segfaults
uwsgi --need-app --die-on-term --socket /tmp/uwsgi.sock --wsgi-file test_segfault.py --enable-threads --processes 1 --master

# Rust version - panics gracefully  
TEST_MODULE=rust uwsgi --need-app --die-on-term --socket /tmp/uwsgi.sock --wsgi-file test_segfault.py --enable-threads --processes 1 --master
```

## Building

```bash
python setup.py build_ext --inplace
```

## Files

- `test_segfault.py` - Main test script with WSGI application entry point
- `cpp_module.cpp` - C++ implementation using `std::optional<TLSObject>` with `thread_local`
- `rust_module/src/lib.rs` - Rust implementation using `thread_local!` macro with `RefCell<Option<TLSObject>>`
- `setup.py` - Build configuration for both C++ and Rust extensions

## Technical Details

The segfault occurs in the backtrace at:
```
cpp_tls_atexit.cpython-312-x86_64-linux-gnu.so(+0x12c4)
```

This corresponds to the `atexit_handler` function attempting to dereference the invalid pointer (`0xdeadbeef`) after TLS cleanup has occurred.

The call chain shows: `uwsgi_plugins_atexit` → `Py_FinalizeEx` → atexit handlers, confirming this happens during uWSGI's controlled shutdown process.