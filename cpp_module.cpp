#include <Python.h>
#include <thread>
#include <optional>

class TLSObject {
public:
    TLSObject() : data(new int(42)) {}
    ~TLSObject() {
        delete data;
        data = reinterpret_cast<int*>(0xdeadbeef); // Make it obvious it's freed
    }
    int* get_data() { return data; }
private:
    int* data;
};

// Use thread_local with automatic storage - destructor will be called automatically
thread_local std::optional<TLSObject> tls_obj;

static PyObject* initialize_tls(PyObject* self, PyObject* args) {
    tls_obj.emplace(); // Construct TLSObject in-place
    Py_RETURN_NONE;
}

static PyObject* atexit_handler(PyObject* self, PyObject* args) {
    // Force access to TLS object - this will segfault after TLS destruction
    // TLS destructors run before atexit handlers, so this should crash
    if (!tls_obj.has_value()) {
        // Optional is empty - force a segfault by dereferencing invalid memory
        volatile int* invalid_ptr = reinterpret_cast<int*>(0xdeadbeef);
        volatile int val = *invalid_ptr;  // This WILL segfault
        (void)val;
    } else {
        int* ptr = tls_obj->get_data();
        volatile int val = *ptr;  // This might also segfault if pointer is invalid
        (void)val;
    }

    Py_RETURN_NONE;
}

// Keep this for manual testing
static void cleanup_tls() {
    if (tls_obj.has_value()) {
        tls_obj.reset(); // This destroys the TLSObject
    }
}

// Register cleanup to happen before atexit handlers
static PyObject* force_cleanup(PyObject* self, PyObject* args) {
    cleanup_tls();
    Py_RETURN_NONE;
}

static PyMethodDef CppModuleMethods[] = {
    {"initialize_tls", initialize_tls, METH_NOARGS, "Initialize TLS object"},
    {"atexit_handler", atexit_handler, METH_NOARGS, "Atexit handler that accesses TLS"},
    {"force_cleanup", force_cleanup, METH_NOARGS, "Force cleanup of TLS"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef cpp_module = {
    PyModuleDef_HEAD_INIT,
    "cpp_tls_atexit",
    "C++ module demonstrating TLS destruction at exit",
    -1,
    CppModuleMethods
};

PyMODINIT_FUNC PyInit_cpp_tls_atexit(void) {
    return PyModule_Create(&cpp_module);
}
