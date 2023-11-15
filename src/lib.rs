use std::{
    cell::{RefCell, UnsafeCell},
    mem::ManuallyDrop,
    ops::Deref,
    rc::Rc,
};

use rustpython_vm as vm;
use vm::{
    builtins::PyStrRef, extend_class, py_class, scope::Scope, Interpreter, PyObjectRef, PyRef,
    PyResult, VirtualMachine,
};

#[macro_use]
extern crate lazy_static;

/// Me when safety lmao ;)
struct UnsafeSendSync<T>(ManuallyDrop<T>);

unsafe impl<T> Send for UnsafeSendSync<T> {}
unsafe impl<T> Sync for UnsafeSendSync<T> {}

struct GlobalPythonVM(UnsafeCell<UnsafeSendSync<Interpreter>>);
unsafe impl Sync for GlobalPythonVM {}

struct GlobalPythonScope(UnsafeCell<UnsafeSendSync<Scope>>);
unsafe impl Sync for GlobalPythonScope {}

lazy_static! {
    /// Global python VM to exist per wasm instance.
    static ref PYTHON_VM: GlobalPythonVM = GlobalPythonVM(UnsafeCell::new(UnsafeSendSync(ManuallyDrop::new(vm::Interpreter::with_init(Default::default(), |vm| {
        vm.add_native_modules(rustpython_stdlib::get_module_inits());
    })))));

    static ref PYTHON_SCOPE: GlobalPythonScope = GlobalPythonScope(UnsafeCell::new(UnsafeSendSync(ManuallyDrop::new(unsafe { &*PYTHON_VM.0.get() }
        .0
        .enter(|vm| vm.new_scope_with_builtins())))));
}

pub struct Sandbox;

wai_bindgen_rust::export!("sandbox.wai");

impl sandbox::Sandbox for Sandbox {
    fn eval(expr: String) -> sandbox::Evalresult {
        let output = Rc::new(RefCell::new(String::new()));
        let error = Rc::new(RefCell::new(String::new()));

        let python = unsafe { &*PYTHON_VM.0.get() };
        let python_scope = unsafe { &*PYTHON_SCOPE.0.get() };

        let result: PyResult<sandbox::Value> = python.0.enter(|vm| {
            let code_obj = vm
                .compile(&expr, vm::compiler::Mode::Eval, "<embedded>".to_owned())
                .map_err(|err| vm.new_syntax_error(&err, Some(&expr)))?;

            let scope = python_scope.0.deref().clone();

            set_stdout(vm, output.clone(), error.clone());

            let result = vm.run_code_obj(code_obj, scope.clone())?;

            // Get type name as string.
            let type_name: String = result
                .obj_type()
                .get_attr("__name__", vm)
                .unwrap()
                .try_to_value(vm)?;

            // Get value as string.
            let value_repr = result.repr(vm).unwrap().to_string();

            Ok(sandbox::Value {
                value: value_repr,
                datatype: type_name,
            })
        });

        let val = match result {
            Ok(result) => Some(result),
            Err(e) => {
                // The entire run block runs all as one after enter is called.
                // Here we check for exception
                python.0.enter(|vm| {
                    let mut out = String::new();
                    vm.write_exception(&mut out, &e.clone()).unwrap();
                    error.borrow_mut().push_str(&out)
                });

                None
            }
        };

        sandbox::Evalresult {
            stdout: sandbox::Stdout {
                out: output.clone().borrow().to_string(),
                err: error.clone().borrow().to_string(),
            },
            value: val,
        }
    }

    fn exec(code: String) -> sandbox::Stdout {
        let output = Rc::new(RefCell::new(String::new()));
        let error = Rc::new(RefCell::new(String::new()));

        let python = unsafe { &*PYTHON_VM.0.get() };
        let python_scope = unsafe { &*PYTHON_SCOPE.0.get() };

        let result: PyResult<()> = python.0.enter(|vm| {
            let code_obj = vm
                .compile(&code, vm::compiler::Mode::Exec, "<embedded>".to_owned())
                .map_err(|err| vm.new_syntax_error(&err, Some(&code)))?;

            let scope = python_scope.0.deref().clone();

            set_stdout(vm, output.clone(), error.clone());

            // Result here doesn't matter, it's always NoneType since this is exec.
            vm.run_code_obj(code_obj, scope.clone())?;

            Ok(())
        });

        if let Err(e) = result {
            // The entire run block runs all as one after enter is called.
            // Here we check for exception
            python.0.enter(|vm| {
                let mut out = String::new();
                vm.write_exception(&mut out, &e.clone()).unwrap();
                error.borrow_mut().push_str(&out)
            });
        }

        sandbox::Stdout {
            out: output.clone().borrow().to_string(),
            err: error.clone().borrow().to_string(),
        }
    }
}

/// Sets the stdout and stderr objects.
fn set_stdout(vm: &vm::VirtualMachine, stdout: Rc<RefCell<String>>, stderr: Rc<RefCell<String>>) {
    // Rc::new(RefCell::new(String::new()));
    let output_clone = stdout.clone();

    vm.sys_module
        .set_attr(
            "stdout",
            make_stdout(vm, move |str, _| {
                output_clone.borrow_mut().push_str(str);
                Ok(())
            }),
            vm,
        )
        .unwrap();

    let error_clone = stderr.clone();

    vm.sys_module
        .set_attr(
            "stderr",
            make_stdout(vm, move |str, _| {
                error_clone.borrow_mut().push_str(str);
                Ok(())
            }),
            vm,
        )
        .unwrap();
}

/// Creates a new `VMStdout` object
///
/// # Arguments
/// - `vm`: The virtual machine
/// - `write_f`: The function to call when `VMStdout.write` is called
fn make_stdout(
    vm: &vm::VirtualMachine,
    write_f: impl Fn(&str, &VirtualMachine) -> PyResult<()> + 'static,
) -> vm::PyObjectRef {
    let cls = PyRef::leak(py_class!(
        vm.ctx,
        "VMStdout",
        vm.ctx.types.object_type.to_owned(),
        {}
    ));

    let write_method = vm.new_method(
        "write",
        cls,
        move |_self: PyObjectRef, data: PyStrRef, vm: &VirtualMachine| -> PyResult<()> {
            write_f(data.as_str(), vm)
        },
    );

    let flush_method = vm.new_method("flush", cls, |_self: PyObjectRef| {});
    extend_class!(vm.ctx, cls, {
        "write" => write_method,
        "flush" => flush_method,
    });

    vm.ctx.new_base_object(cls.to_owned(), None)
}
