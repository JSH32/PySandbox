# Python Sandbox
This python sandbox uses wasmer to execute untrusted python code in a sandbox. It is expiremental and limited in functionality. This was designed to be used in an assignment autograder.

## Components
- Rust WASM layer
  - [RustPython](https://github.com/RustPython/RustPython) is used as a dependency in the rust part of this library. RustPython doesn't aim to create sandboxed environments but we can create a simple API for interacting with it while it is being run in a `wasm32-wasi` runtime which would effectively sandbox it.
  - We use [WAI](https://github.com/wasmerio/wai) to generate glue implementations that we can use to interop between a regular Python environment and RustPython.
- Python Layer
  - The Python bindings are also generated with WAI and a helper is provided for setup.

## Development
You will need Rust and `wai-bindgen` installed from [WAI](https://github.com/wasmerio/wai).
- To compile the Rust code to a WASI binary, run `cargo build --release --target wasm32-wasi`
  - Replace `py_sandbox/py_sandbox.wasm` with `target/wasm32-wasi/release/py_sandbox.wasm` after building to see changes.
- To build new `bindings.py` from `sandbox.wai`, run `wai-bindgen wasmer-py --import ./sandbox.wai`

## Usage
```py
from py_sandbox import create_sandbox

# each sandbox has its own memory.
sandbox = create_sandbox()

# returns stdout/err
stdout = sandbox.exec("""
def hello(x):
    return x + 5
""")

# result has both stdout/err and return value
result = sandbox.eval("2+2")
print(result.value.value)
```