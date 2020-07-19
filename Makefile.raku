include config/base.config

PERLVER		= 2020.06
PERL		= rakudo-${PERLVER}
PERL_INST_PATH	= ${NLYTIQ_INST_PATH}
OSREV		= $(shell uname -r)
PFLAGS          = --gen-moar
CONFFLAGS      =  --prefix ${NLYTIQ_INST_PATH}
DIR		= $(shell pwd)/${PERL}
ZEF		= zef
ZEFTAR		= ${ZEF}.tar.gz


ifeq ($(GCC),1)
	### use gcc
	CFLAGS          = -mtune=native
	###
endif

ifeq ($(CLANG),1)
	### use clang
	CFLAGS          = -O2
endif

# ${_EPF_} contains the front matter for configure after the include below
include config/configure.prefix.flag.config


#--------------------------------------------------------------------------#

all:    	install-perl6-mods

clean:		clean-perl6  

configure-perl6:	sources/${PERL}.tar.gz
	tar -zxvf sources/${PERL}.tar.gz
	cd ${PERL} ; ${_EPF_}  ${NLYTIQ_INST_PATH}/bin/perl Configure.pl ${PFLAGS} ${CONFFLAGS}
	touch configure-perl6

make-perl6: configure-perl6
	cd ${PERL} ; make -j${NCPU}
	touch make-perl6

install-perl6: make-perl6
	cd ${PERL} ; make install
	touch install-perl6

install-perl6-mods: install-perl6
	tar -zxvf sources/${ZEFTAR}
	cd zef ; ${_EPF_}  ${NLYTIQ_INST_PATH}/bin/perl6 -I. bin/zef install .
	touch install-perl6-mods

clean-perl6:
	rm -rf ${PERL} make-perl6 configure-perl6 install-perl6 zef install-perl6-mods 
