//! ClaudeBeacon Python bindings using PyO3
//!
//! Exposes Rust core to Python as a native extension module

use pyo3::prelude::*;
use beacon_core::BeaconCore;
use pyo3::types::{PyDict, PyString};

#[pyclass]
pub struct Beacon {
    core: tokio::runtime::Runtime,
    beacon: Option<BeaconCore>,
}

#[pymethods]
impl Beacon {
    #[new]
    pub fn new(db_path: &str) -> PyResult<Self> {
        let rt = tokio::runtime::Runtime::new()
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        Ok(Beacon {
            core: rt,
            beacon: None,
        })
    }

    pub fn init(&mut self, db_path: &str) -> PyResult<()> {
        let beacon = self.core.block_on(async {
            BeaconCore::new(db_path).await
        }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        
        self.beacon = Some(beacon);
        Ok(())
    }

    pub fn save_memory(&mut self, context: &PyDict) -> PyResult<bool> {
        let context_json = serde_json::to_value(context)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?;
        
        if let Some(beacon) = &mut self.beacon {
            self.core.block_on(async {
                beacon.save_memory(context_json).await
            }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            Ok(true)
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Beacon not initialized"))
        }
    }

    pub fn observe(&self) -> PyResult<PyObject> {
        if let Some(beacon) = &self.beacon {
            let result = self.core.block_on(async {
                beacon.observe().await
            }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            
            Python::with_gil(|py| {
                Ok(PyString::new(py, &result.to_string()).into())
            })
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Beacon not initialized"))
        }
    }

    pub fn audit(&self, filter: Option<&PyDict>) -> PyResult<PyObject> {
        if let Some(beacon) = &self.beacon {
            let filter_json = if let Some(f) = filter {
                Some(serde_json::to_value(f)
                    .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(e.to_string()))?)
            } else {
                None
            };

            let result = self.core.block_on(async {
                beacon.audit(filter_json).await
            }).map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
            
            Python::with_gil(|py| {
                Ok(PyString::new(py, &serde_json::to_string(&result)?).into())
            })
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Beacon not initialized"))
        }
    }
}

#[pymodule]
fn _core(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<Beacon>()?;
    Ok(())
}
