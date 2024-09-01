#!/bin/bash

for pkg in libssh2 zlib tcl-tk gcc@8 ossp-uuid  suite-sparse mbedtls curl libunwind-headers mpfr xz  libedit with-readline cmake gnu-sed
do
  echo installing $pkg
  brew install $pkg
done
