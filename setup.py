from setuptools import setup, find_namespace_packages

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setup(
    name='wasm_py_sandbox',
    author='Josh Rudnik',
    author_email='rudnik7000@gmail.com',
    description='Sandbox environment for executing Python code',
    keywords='python, sandbox, wasm, wasmer',
    license='MIT',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/tomchen/example_pypi_package',
    project_urls={
        'Documentation': 'https://github.com/JSH32/PySandbox',
        'Bug Reports': 'https://github.com/JSH32/PySandbox/issues',
        'Source Code': 'https://github.com/JSH32/PySandbox',
    },
    python_requires='>=3',
    package_dir={'': 'py_src'},
    version='0.1.0',
    packages=find_namespace_packages(where='py_src'),
    package_data={'': ['*.wasm']},
    install_requires=[
        'wasmer==1.1.0',
        'wasmer-compiler-cranelift==1.1.0',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)