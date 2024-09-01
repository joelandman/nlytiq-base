#Getting started

##Requirements

* compilers
   * C/C++
   * Fortran 

* libraries and development headers
   * bzip2   (Perl, R, Python)
   * openssl (Python, )
   * gdbm (Python)
   * sqlite3 (Python)
   * tk (Python)
   * png (Python)
   * Xwindows (R)
   * PCRE (Python, R)

Note: gcc 8 through 14 work well for this.  LLVM tends to be able to compile most of these packages
though there are occassional compatibility issues.  If you would like to adjust which compiler
is used, options for the compilation, paths to the compiler, make a (backup) copy of 

	config/compiler.config.$OS

where $OS is the lower case version of the output of `uname` for the system you are 
building this on.  Right now linux and darwin (mac OSX) are supported.  We have supported SmartOS
and FreeBSD in the past, but this support has been removed.



##Building

TL;DR version: 
    cd scripts
    sudo ./prep_$OS.sh

where $OS is debian1{1,2}, ubuntu2{2,4}.04, rocky8, or mac.
Then
    cd ..
    make

Note: this will take a long time, as several of the codes
are quite time consuming to build.  The process is (mostly)
automated, and undergoing rapid development.  The builds are
done in parallel whenever possible. 

Note: if you are building on Mac, homebrew is strongly recommended,
and is the basis of the prep_mac.sh script. 

To build everything after installing any dependencies

  make

To build a specific project

  make -f Makefile.$project

To clean up everything

  make clean

To clean up a specific project

  make -f Makefile.$project clean

