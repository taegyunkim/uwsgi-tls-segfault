use pyo3::prelude::*;
use std::cell::RefCell;

struct TLSObject {
    value: *mut i32,
}

impl TLSObject {
    fn new() -> Self {
        TLSObject { 
            value: Box::into_raw(Box::new(42))
        }
    }
    
    fn get_value(&self) -> i32 {
        unsafe { *self.value }  // This will segfault if value is freed
    }
}

impl Drop for TLSObject {
    fn drop(&mut self) {
        if !self.value.is_null() {
            unsafe {
                let _ = Box::from_raw(self.value);
            }
            // Don't null the pointer - leave it dangling for segfault
            self.value = 0xdeadbeef as *mut i32;
        }
    }
}

// Thread-local storage that will be automatically destroyed
thread_local! {
    static TLS_OBJECT: RefCell<Option<TLSObject>> = RefCell::new(None);
}

#[pyfunction]
fn initialize_tls() -> PyResult<()> {
    TLS_OBJECT.with(|obj| {
        *obj.borrow_mut() = Some(TLSObject::new());
    });
    Ok(())
}

#[pyfunction] 
fn atexit_handler() -> PyResult<()> {
    // This will segfault because TLS may have been cleaned up
    // We try to access it anyway without checking validity
    TLS_OBJECT.with(|obj| {
        let binding = obj.borrow();
        let tls_obj = binding.as_ref().unwrap(); // This will panic if None
        let _val = tls_obj.get_value();  // This will segfault after cleanup
    });
    Ok(())
}

#[pyfunction]
fn force_cleanup() -> PyResult<()> {
    TLS_OBJECT.with(|obj| {
        *obj.borrow_mut() = None;  // This triggers Drop
    });
    Ok(())
}

#[pymodule]
fn rust_tls_atexit(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(initialize_tls, m)?)?;
    m.add_function(wrap_pyfunction!(atexit_handler, m)?)?;
    m.add_function(wrap_pyfunction!(force_cleanup, m)?)?;
    Ok(())
}