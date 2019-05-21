#Getting started

##Requirements

* compilers
   * C/C++
   * Fortran (gfortran)

* libraries and development headers
   * bzip2   (Perl, R, Python)
   * openssl (Python, )
   * gdbm (Python)
   * sqlite3 (Python)
   * tk (Python)
   * png (Python)
   * Xwindows (R)
   * PCRE (Python, R)

A dependency checker is planned.

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

The prep_mac.bash script will do this for you.

To build everything after installing any dependencies

  make

To build a specific project

  make -f Makefile.$project

To clean up everything

  make clean

To clean up a specific project

  make -f Makefile.$project clean

Rust is currently disabled due to some oddities I am working on tracking
down.  
