include config/base.config

#### R  
RVER		= 3.6.3
R		= R-${RVER}
R_INST_PATH	= ${NLYTIQ_INST_PATH}

# clang and f95 disagree on int size.  f95 wants it 64 bit (as it should be)
# clang wants it 32 bit.  Looking for a way to convince clang that it should
# be 64 bit.
FORCEGCC	= 1

### force baseline gcc if GCC_VER is not blank
include config/forcegcc.config

CFLAGS          += -I${NLYTIQ_INST_PATH}/include
LDFLAGS         += -L${NLYTIQ_INST_PATH}/lib -lcurl


FFLAGS		= ${CFLAGS}
FCFLAGS		= ${CFLAGS} 
CXXFLAGS	= ${CFLAGS}

# ${_EPF_} contains the front matter for configure after the include below
include config/configure.prefix.flag.config

### R specific compilation flags
MAIN_LDFLAGS    = -L${NLYTIQ_INST_PATH}/lib
LIBS		= -lcurl
_EPF_ += MAIN_LDFLAGS="${MAIN_LDFLAGS}"

RFLAGS		= --with-blas --with-lapack --with-readline  --with-system-zlib --with-system-bzlib --with-system-pcre --with-system-xz --with-recommended-packages --with-x --with-sysroot=${NLYTIQ_INST_PATH}/lib --enable-R-shlib --enable-R-static-lib
#--------------------------------------------------------------------------#

all:    	install-R-modules

clean:		clean-R  

configure-R:	
	tar -zxvf sources/${R}.tar.gz
	cd ${R} ; export PATH=${NLYTIQ_INST_PATH}/bin:${PATH} ; ${_EPF_} ./configure --prefix=${NLYTIQ_INST_PATH} ${RFLAGS}
	cd ${R} ; /bin/bash tools/rsync-recommended 			  
	touch configure-R

make-R: configure-R
	cd ${R} ;  ${_EPF_} make -j${NCPU}
	touch make-R

install-R: make-R
	# below to fix a build issue
	mkdir -p ${NLYTIQ_INST_PATH}/lib/R/lib/
	cd ${R} ;   ${_EPF_} make install
	touch install-R

install-R-modules: install-R
	# create the .Rprofile file
	#echo 'cat(".Rprofile: Setting US repository")' > ${HOME}/.Rprofile
	echo 'r = getOption("repos") # use the US repo for CRAN' >> ${HOME}/.Rprofile
	echo 'r["CRAN"] = "http://cran.us.r-project.org"' >> ${HOME}/.Rprofile
	echo 'options(repos = r)' >> ${HOME}/.Rprofile
	echo 'rm(r)' >> ${HOME}/.Rprofile
	#
	# create an .Renviron file to make packages installable by everyone
	mkdir -p ${NLYTIQ_INST_PATH}/Rpackages/ 
	chmod -R 1777 ${NLYTIQ_INST_PATH}/Rpackages/
	mkdir -p ${NLYTIQ_INST_PATH}/lib64/R/lib/
	echo "R_LIBS=${NLYTIQ_INST_PATH}/Rpackages/" >> ${HOME}/.Renviron
	#
	# now install the modules we want
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e 'install.packages("ggplot")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e 'install.packages("tseries")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("gplots")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("gtools")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("parallelize.dynamic")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("partools")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("tframe")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("forecast")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("ltsa")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("bspec")' 
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("bit64")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("rjson")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("IRkernel")'
	touch install-R-modules

clean-R:
	rm -rf ${R} make-R configure-R install-R install-R-modules ${R}
