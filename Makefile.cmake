include base.config

####   
CMAKEVER		= 3.8.2
CMAKESRC		= cmake-${CMAKEVER}
CMAKETAR		= ${CMAKESRC}.tar.gz
CMAKE_INST_PATH	= ${NLYTIQ_INST_PATH}
#--------------------------------------------------------------------------#


### force baseline gcc if GCC_VER is not blank
include forcegcc.config

# ${_EPF_} contains the front matter for configure after the include below
include configure.prefix.flag.config


all:    	install-cmake

clean:		clean-cmake  


configure-cmake: 
	tar -zxf sources/${CMAKETAR}
	#cd ${CMAKESRC} ; CC=${CC} CXX=${CXX} CFLAGS=${CFLAGS} CXXFLAGS=${CXXFLAGS} ./configure --prefix=${NLYTIQ_INST_PATH}  
	cd ${CMAKESRC} ; ${_EPF} ./configure --prefix=${NLYTIQ_INST_PATH} 
	touch configure-cmake

make-cmake: configure-cmake
	cd ${CMAKESRC} ; make -j${NCPU}
	touch make-cmake
 
install-cmake: make-cmake
	cd ${CMAKESRC} ; make -j${NCPU} install
ifeq ($(OS),Linux)
	test -f /usr/bin/cmake  && \
       		mv -f /usr/bin/cmake /usr/bin/cmake.original && \
		ln -s ${NLYTIQ_INST_PATH}/bin/cmake /usr/bin/cmake
endif
	touch install-cmake

clean-cmake:
	rm -rf ${CMAKESRC} make-cmake install-cmake configure-cmake cmake
