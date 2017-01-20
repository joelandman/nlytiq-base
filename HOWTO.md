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

To build everything

  sudo make

To build a specific project

  sudo make -f Makefile.$project

To clean up everything

  sudo make clean

To clean up a specific project

  sudo make -f Makefile.$project clean

Rust is currently disabled due to some oddities I am working on tracking
down.  
