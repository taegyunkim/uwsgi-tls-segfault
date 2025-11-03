# uwsgi-tls-segfault

A demonstration of Thread Local Storage (TLS) destruction ordering differences between standalone Python and uWSGI environments.

## Overview

This repository demonstrates a critical difference in TLS destruction and Python `atexit` handler execution between standalone Python and uWSGI deployments. The ordering is well-defined in both cases, but differs significantly, leading to segmentation faults under uWSGI.

## The Problem

The issue stems from different execution contexts having different destruction orders:

- **Standalone Python**: `atexit` handlers are run first and TLS is destroyed. No segmentation fault. 
- **uWSGI Environment**: Worker processes have a different destruction sequence where:
  1. TLS objects are destroyed as part of thread/process cleanup
  2. `atexit` handlers are called later during Python interpreter finalization
  3. Atexit handlers attempt to access already-destroyed TLS memory → **SEGFAULT**

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
```

### Standalone Testing (Safe)

```bash
python test_segfault.py
# Exit code: 0 (runs without segfault)
```

### uWSGI Testing (Demonstrates Segfault)

Run one of the following commands, then press `Ctrl-C` after the application is loaded. 

```bash
# C++ version - segfaults
uwsgi --need-app --die-on-term --socket /tmp/uwsgi.sock --wsgi-file test_segfault.py --enable-threads --processes 1 --master

# Rust version - panics gracefully  
TEST_MODULE=rust uwsgi --need-app --die-on-term --socket /tmp/uwsgi.sock --wsgi-file test_segfault.py --enable-threads --processes 1 --master
```

#### Example Stack trace

```
^CSIGINT/SIGTERM received...killing workers...
!!! uWSGI process 750617 got Segmentation Fault !!!
*** backtrace of 750617 ***
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(uwsgi_backtrace+0x33) [0x609c416057d3]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(uwsgi_segfault+0x27) [0x609c41605c07]
/lib/x86_64-linux-gnu/libc.so.6(+0x42520) [0x7db95567f520]
/home/bits/go/src/github.com/DataDog/tls-atexit/cpp_tls_atexit.cpython-312-x86_64-linux-gnu.so(+0x12c4) [0x7db952ee42c4]
/home/bits/.pyenv/versions/3.12.12/lib/libpython3.12.so.1.0(+0x1d3de4) [0x7db955a39de4]
/home/bits/.pyenv/versions/3.12.12/lib/libpython3.12.so.1.0(+0x31a757) [0x7db955b80757]
/home/bits/.pyenv/versions/3.12.12/lib/libpython3.12.so.1.0(Py_FinalizeEx+0x67) [0x7db955b4bf47]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(uwsgi_plugins_atexit+0x71) [0x609c41602751]
/lib/x86_64-linux-gnu/libc.so.6(+0x45495) [0x7db955682495]
/lib/x86_64-linux-gnu/libc.so.6(on_exit+0) [0x7db955682610]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(+0x40275) [0x609c415b7275]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(end_me+0x2b) [0x609c4160279b]
/lib/x86_64-linux-gnu/libc.so.6(+0x42520) [0x7db95567f520]
/lib/x86_64-linux-gnu/libc.so.6(epoll_wait+0x1a) [0x7db955762e5a]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(event_queue_wait+0x39) [0x609c415f7ff9]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(wsgi_req_accept+0x11a) [0x609c415b499a]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(simple_loop_run+0xb6) [0x609c416014d6]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(simple_loop+0x7b) [0x609c416015bb]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(uwsgi_ignition+0x1f0) [0x609c41605eb0]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(uwsgi_worker_run+0x29a) [0x609c4160a68a]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(uwsgi_run+0x465) [0x609c4160abd5]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(+0x3ce04) [0x609c415b3e04]
/lib/x86_64-linux-gnu/libc.so.6(+0x29d90) [0x7db955666d90]
/lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0x80) [0x7db955666e40]
/home/bits/.pyenv/versions/3.12.12/bin/uwsgi(_start+0x25) [0x609c415b3e35]
*** end of backtrace ***
worker 1 buried after 1 seconds
goodbye to uWSGI.
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

The call chain shows: `uwsgi_plugins_atexit` → `Py_FinalizeEx` → atexit handlers, confirming this happens during uWSGI's controlled shutdown process where TLS has already been destroyed but Python atexit handlers are still being executed.
