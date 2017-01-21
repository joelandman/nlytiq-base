include base.config

RUBY_INST_PATH	= ${NLYTIQ_INST_PATH}
RUBY_VERSION	= 2.4.0




all:    	install-ruby

clean:		clean-ruby  

configure-ruby:	
	tar -zxvf sources/ruby-${RUBY_VERSION}.tar.gz
	cd ruby-${RUBY_VERSION} ; CFLAGS=${CFLAGS} CC=${CC} CXX=${CXX} ./configure --prefix=${RUBY_INST_PATH}  --enable-load-relative  --enable-shared
	touch configure-ruby

make-ruby: configure-ruby
	cd ruby-${RUBY_VERSION}; CFLAGS=${CFLAGS} CC=${CC} CXX=${CXX} make -j${NCPU}
	touch make-ruby

install-ruby: make-ruby
	cd ruby-${RUBY_VERSION} ; CFLAGS=${CFLAGS} CC=${CC} CXX=${CXX} make install
	touch install-ruby

clean-ruby:
	rm -rf ruby install-ruby make-ruby configure-ruby ruby-${RUBY_VERSION}
