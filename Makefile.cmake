include base.config

####   
CMAKEVER		= 3.7.0
CMAKESRC		= cmake-${CMAKEVER}
CMAKETAR		= ${CMAKESRC}.tar.gz
CMAKE_INST_PATH	= ${NLYTIQ_INST_PATH}
#--------------------------------------------------------------------------#

all:    	install-cmake

clean:		clean-cmake  


configure-cmake: 
	tar -zxf sources/${CMAKETAR}
	cd ${CMAKESRC} ; ./configure --prefix=${NLYTIQ_INST_PATH}  
	touch configure-cmake

make-cmake: configure-cmake
	cd ${CMAKESRC} ; make -j4
	touch make-cmake
 
install-cmake: make-cmake
	cd ${CMAKESRC} ; make -j4 install
	mv -f /usr/bin/cmake /usr/bin/cmake.original
	ln -s ${NLYTIQ_INST_PATH}/bin/cmake /usr/bin/cmake
	touch install-cmake

clean-cmake:
	rm -rf ${CMAKESRC} make-cmake install-cmake configure-cmake cmake
