import os
from .bindings import Sandbox
from wasmer import Store, Module, wasi

current_dir = os.path.dirname(os.path.abspath(__file__))
wasm_bin = os.path.join(current_dir, "py_sandbox.wasm")

def create_sandbox() -> Sandbox:
    """
    Creates a new sandbox environment for executing Python code.

    Returns:
        Sandbox: A sandbox object that provides an isolated environment for executing Python code.
    """
    store = Store()

    with open(wasm_bin, "rb") as wasm_file:
        module = Module(store, wasm_file.read())

    wasi_version = wasi.get_version(module, strict=True)
    wasi_env = wasi.StateBuilder('py_sandbox').finalize()
    import_object = wasi_env.generate_import_object(store, wasi_version)

    return Sandbox(store, import_object, module)
