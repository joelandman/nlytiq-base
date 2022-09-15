include config/base.config

####   
GNUPLOTVER	= 5.4.4
GNUPLOT		= gnuplot-${GNUPLOTVER}
GNUPLOTTAR	= ${GNUPLOT}.tar.gz
PFLAGS          = 
CONFFLAGS	= --prefix=${NLYTIQ_INST_PATH} --disable-silent-rules \
		  --enable-stats \
		  --enable-backwards-compatibility \
		  --with-x --with-readline=gnu \
		  --with-gd=/usr/lib/x86_64-linux-gnu/	\
		  --with-pdf=/usr/lib/x86_64-linux-gnu/ \
		  --with-qt --with-row-help
DIR		= $(shell pwd)/${GNUPLOT}


# ${_EPF_} contains the front matter for configure after the include below
include config/configure.prefix.flag.config


#--------------------------------------------------------------------------#

all:    	install-gnuplot

clean:		clean-gnuplot  

configure-gnuplot:	sources/${GNUPLOT}.tar.gz 
	tar -zxvf sources/${GNUPLOTTAR}
	cd ${DIR} ; ${_EPF_} ./configure ${CONFFLAGS}
	touch configure-gnuplot

make-gnuplot: configure-gnuplot
	cd ${DIR} ; export  LD_LIBRARY_PATH=${DIR} ;  make -j${NCPU} 
	touch make-gnuplot

install-gnuplot: make-gnuplot
	cd ${DIR} ; export  LD_LIBRARY_PATH=${DIR} ; make install
	touch install-gnuplot

clean-gnuplot:
	rm -rf ${DIR} make-gnuplot configure-gnuplot install-gnuplot ${DIR}
