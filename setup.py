from setuptools import setup, find_namespace_packages

setup(
    name='py_sandbox',
    author='Josh Rudnik',
    author_email='rudnik7000@gmail.com',
    description='Sandbox environment for executing Python code',
    python_requires='>=3',
    package_dir={'': 'py_src'},
    version='0.1.0',
    packages=find_namespace_packages(where='py_src'),
    install_requires=[
        'wasmer==1.1.0',
        'wasmer-compiler-cranelift==1.1.0',
    ],
)