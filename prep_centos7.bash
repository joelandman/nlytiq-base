#!/bin/bash -x

yum -y install bzip2-devel.x86_64 lzma-sdk-devel.x86_64 		\
	lzma-sdk457-devel.x86_64 zlib-devel.x86_64 ncurses-devel.x86_64 \
	sqlite-devel.x86_64 gdbm-devel.x86_64 openssl-devel.x86_64 		\
	uuid-devel.x86_64 libuuid-devel.x86_64 uthash-devel.noarch 		\
	rhash-devel.x86_64 mhash-devel.x86_64 libdhash-devel.x86_64 	\
	xxhash-devel.x86_64 readline-devel.x86_64 readline-static.x86_64\
	tkinter.x86_64 tcl-devel.x86_64 tcl-tclreadline-devel.x86_64 	\
	tcl-tclreadline-devel.x86_64 tclx-devel.x86_64 					\
	libffi-devel.x86_64 zstd alsa-lib-devel libuv-devel.x86_64 		\
	pcre2-devel fftw-devel.x86_64 asio-devel libzip-devel.x86_64 	\
	pbzip2.x86_64 lbzip2-utils.x86_64 bzip2-devel.x86_64 xz-devel 	\
	libcurl-devel.x86_64 gd-devel.x86_64 pango-devel.x86_64 		\
	compat-wxGTK3-gtk2-devel.x86_64 plplot-wxGTK-devel.x86_64 		\
	wxGTK3-devel.x86_64 wxGTK-devel.x86_64 cairo-devel.x86_64
