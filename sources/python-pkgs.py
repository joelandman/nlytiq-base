#!/usr/bin/env -S python3

import sys, subprocess as sp

pkgs = [
        "numpy",
        "pyzmq",
        "pandas",
        "sympy",
        "fortran-language-server",
        "scipy",
        "requests",
        "polars",
        "nuitka",
        "tqdm"
        ]

for pkg in pkgs:
    cmd = f"pip3 install {pkg}"
    sp.run(cmd)
