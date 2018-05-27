Build instructions

1st) install any dependencies:
	a) compilers
	b) relevant libraries and headers

2nd) prepare space on designated path for use

Edit base.config and alter the value of NLYTIQ_TOP variable to reflect
where you would like the tools to reside.  Default if /opt/nlytiq, though 
you may put them anywhere ... though ... we do not recommend overwriting 
your platform tools (usually /usr).  

3rd) set the default compiler to use

By default, we assume gcc/g++/gfortran in default paths on the system.  These 
assumptions may be invalid.  If you wish to use gcc installed in a different 
path, edit compiler.config and find your OS (search for one of Linux, Darwin,
FreeBSD, SunOS representing all linux distros, macos, FreeBSD and possibly 
others).  Edit the GCC_PATH and GCC_VER appropriately.

Example: gcc-7 installed in Linux at /usr/local/compilers/gcc-7

	GCC_PATH = /usr/local/compilers/
	GCC_VER  = -7

The _VER is the suffix.  Leave blank if you don't need it.
the _PATH is the actual path, INCLUDING THE "/" AT THE END, to the gcc
binary.

Note: other compilers than GCC will work, with a few caveats.  

CLANG is available, and is built from source.  We plan to make it selectable
in case you have a previous clang installed you wish to use.

It should be possible to use Intel compilers, and Portland Group compilers,
though we've not done the work required to support this as of yet.

As of this moment, gcc-4.9, gcc-5.4, gcc-6.3 work under Linux, and FreebSD.  
clang works under MacOS (disguised as gcc). 

4th) run 

	nohup make > out 2> err &
	tail -f out err

Note:  if your directory requires elevated privileges to run, you may need to
run this under sudo.

If your build fails, you have a simple STDERR file (err) to search.  Best look
at it from the bottom up, to find the error that caused the build to fail.


