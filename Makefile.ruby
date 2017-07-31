include base.config

RUBY_INST_PATH	= ${NLYTIQ_INST_PATH}
RUBY_VERSION	= 2.4.0


# ${_EPF_} contains the front matter for configure after the include below
include configure.prefix.flag.config


all:    	install-ruby

clean:		clean-ruby  

configure-ruby:	
	tar -zxvf sources/ruby-${RUBY_VERSION}.tar.gz
	cd ruby-${RUBY_VERSION} ; ${_EPF_} ./configure --prefix=${RUBY_INST_PATH}  --enable-load-relative  --enable-shared
	touch configure-ruby

make-ruby: configure-ruby
	cd ruby-${RUBY_VERSION}; make -j${NCPU}
	touch make-ruby

install-ruby: make-ruby
	cd ruby-${RUBY_VERSION} ; make install
	touch install-ruby

clean-ruby:
	rm -rf ruby install-ruby make-ruby configure-ruby ruby-${RUBY_VERSION}
