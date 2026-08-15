Build instructions

1st) install any dependencies:
	a) compilers
	b) relevant libraries and headers
	c) curl or wget, and sha256sum (or shasum on macos)

Note: the build downloads source tarballs from upstream on first use, so
the build host needs network access.  See "Source tarballs" at the end of
this file if you need to pre-fetch them or build offline.

2nd) prepare space on designated path for use

Edit base.config and alter the value of NLYTIQ_TOP variable to reflect
where you would like the tools to reside.  Default if /opt/nlytiq, though 
you may put them anywhere ... though ... we do not recommend overwriting 
your platform tools (usually /usr).  

3rd) set the default compiler to use

By default, we assume gcc/g++/gfortran in default paths on the system.  These 
assumptions may be invalid.  If you wish to use gcc installed in a different 
path, edit compiler.config and find your OS (search for one of Linux, Darwin,
representing all linux distros and macos.  Edit the GCC_PATH and GCC_VER 
appropriately.

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


Source tarballs

Source tarballs are not stored in this repository.  sources/manifest.txt
records the upstream URL and SHA-256 of each one, and each Makefile.<pkg>
lists its tarball as a prerequisite, so a missing tarball is downloaded and
verified as an ordinary part of the build.

To pre-fetch everything up front -- useful before building on a slow link, or
to populate sources/ on a machine that will later build offline:

	scripts/fetch-source.sh --all

or fetch a single one:

	scripts/fetch-source.sh Python-3.14.3.tar.xz

A tarball already present in sources/ is verified and left alone, so the above
is cheap to re-run.  A checksum that does not match is always a hard error:
the build stops rather than using the file.


Bumping a package version

See UPDATING.md for the full treatment.  In short:

	scripts/update-package.py --package gnuplot --list-versions
	scripts/update-package.py --package gnuplot

The first lists what upstream offers, with release dates and ages in days and
a marker on the version this tree currently pins.  The second downloads the
newest one, with a progress bar, and updates all three things that have to
agree: the version variable in Makefile.<pkg>, the package's line in
sources/manifest.txt (filename, checksum and URL), and the tarball in sources/.
The checksum is computed from the bytes that actually arrived, and nothing is
written until the download has finished, so an interrupted run leaves the tree
as it was.

Pass --version VERSION to pick a specific one rather than the latest, or
--dry-run to see what would change without downloading or writing anything.
--list-packages shows the packages it knows about and their pinned versions.

Where each package's versions come from, and the templates used to build its
download URL, are described in packages.yaml at the top of the tree.  The tool
needs nothing but python3.  Set GITHUB_TOKEN if you hit GitHub's rate limit on
anonymous requests.

The version bump is deliberately separate from the build: review it with
'git diff', then rebuild that package with

	make -f Makefile.<pkg> clean && make -f Makefile.<pkg>

Packages installed some other way -- rust (rustup), spark, jupyter_kernels and
perl5mods -- have no tarball and are not managed by this tool.  To bump one of
the packages by hand instead, edit the version variable at the top of the
relevant Makefile.<pkg> and replace that package's line in sources/manifest.txt
with the new filename, checksum, and URL.  Take the checksum from upstream
where they publish one; otherwise download the tarball and run sha256sum on it.

Two files under sources/ are exceptions and remain checked in:
spark-0.46.tar.gz and maxima-kernel.tar.gz.  Both are local clone snapshots
rather than upstream release artifacts, so no URL reproduces them.


