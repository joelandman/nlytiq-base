include config/base.config
include config/fetch.config

#### R  
RVER		= 4.6.1
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

configure-R:	sources/${R}.tar.xz
	tar -Jxvf sources/${R}.tar.xz
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

### These two files belong to whoever runs the build, and this target appended
### to them unconditionally, so every rebuild left another copy of the same
### lines behind.  Both blocks are now guarded and write themselves once.
### The '###' is added in the recipe rather than here: in a variable
### assignment make would read it as the start of a comment and leave
### R_PROFILE_MARK empty, which would make the guard below match anything.
R_PROFILE_MARK	= nlytiq: CRAN mirror
R_LIBS_LINE	= R_LIBS=${NLYTIQ_INST_PATH}/Rpackages/

install-R-modules: install-R
	# create the .Rprofile file, once
	if ! grep -qF '### ${R_PROFILE_MARK}' ${HOME}/.Rprofile 2>/dev/null ; then	\
	  { echo '### ${R_PROFILE_MARK}' ;					\
	    echo 'r = getOption("repos")' ;					\
	    echo '# cloud.r-project.org is the CRAN CDN.  Not cran.us.r-project' ;\
	    echo '# .org: over http that redirects to lib.stat.cmu.edu and works,' ;\
	    echo '# but over https it redirects to cran.microsoft.com, which was' ;\
	    echo '# retired and now just times out.' ;				\
	    echo 'r["CRAN"] = "https://cloud.r-project.org"' ;			\
	    echo 'options(repos = r)' ;						\
	    echo 'rm(r)' ; } >> ${HOME}/.Rprofile ;				\
	fi
	#
	# create an .Renviron file to make packages installable by everyone
	mkdir -p ${NLYTIQ_INST_PATH}/Rpackages/
	chmod -R 1777 ${NLYTIQ_INST_PATH}/Rpackages/
	mkdir -p ${NLYTIQ_INST_PATH}/lib64/R/lib/
	if ! grep -qxF '${R_LIBS_LINE}' ${HOME}/.Renviron 2>/dev/null ; then	\
	  echo '${R_LIBS_LINE}' >> ${HOME}/.Renviron ;				\
	fi
	#
	# now install the modules we want.
	#
	# 'ggplot' was the package's name until it was renamed ggplot2 in 2007;
	# asking for the old name only produces "package 'ggplot' is not
	# available".  'onstatseries' was dropped for the same reason -- CRAN has
	# no package under that name, so it never installed anything.
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e 'install.packages("IRkernel")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e 'IRkernel::installspec()'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e 'install.packages("ggplot2")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("gplots")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("gtools")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("tframe")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("rjson")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("tidyverse")'
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e  'install.packages("shiny")'
	### install.packages() does not set a non-zero exit status when a package
	### fails, so this target used to report success while nothing installed.
	### fs needing libuv1-dev took out nine packages that way, tidyverse and
	### shiny among them, and the build said it was fine.
	${NLYTIQ_INST_PATH}/bin/R --no-save --quiet -e 'want <- c("IRkernel","ggplot2","gplots","gtools","tframe","rjson","tidyverse","shiny"); missing <- want[!sapply(want, requireNamespace, quietly=TRUE)]; if (length(missing)) { cat("error: these R packages did not install:", paste(missing, collapse=" "), "\n"); quit(status=1) }'
	touch install-R-modules

clean-R:
	rm -rf ${R} make-R configure-R install-R install-R-modules ${R}
