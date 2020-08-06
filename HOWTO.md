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

Note: gcc 8 and 9 work well for this.  LLVM tends to be able to compile most of these packages
though there are occassional compatibility issues.  If you would like to adjust which compiler
is used, options for the compilation, paths to the compiler, make a (backup) copy of 

	config/compiler.config.$OS

where $OS is the lower case version of the output of `uname` for the system you are 
building this on.  Right now linux and darwin (mac OSX) are supported.  We have supported SmartOS
and FreeBSD in the past, but this support has been removed.



##Building

Note: this will take a long time, as several of the codes
are quite time consuming to build.  The process is (mostly)
automated, and undergoing rapid development.  The builds are
done in parallel whenever possible.  On my 6 core system with ample
memory and fast disk, builds (when rust is enabled) have taken
more than 2 hours.

Note: if you are building on Mac, I'd recommend homebrew.  Then you'll
want to install gcc@8, and the following dependent packages:
	
	libssh2
	zlib
	tcl-tk
	ossp-uuid
	suite-sparse
	mbedtls
	curl
	libunwind-headers
	mpfr
	xz
	libedit
	with-readline
	cmake
	gnu-sed

The prep_mac.bash script will do this for you.  If you are running on linux, use the appropriate prep_distro.bash script by
	sudo ./prep_$DISTRO.bash
	
To build everything after installing any dependencies

  make

To build a specific project

  make -f Makefile.$project

To clean up everything

  make clean

To clean up a specific project

  make -f Makefile.$project clean

