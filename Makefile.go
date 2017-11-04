include base.config

####   
GOVER		= 1.9.2
GOBASE		= go${GOVER}
ifeq ($(OS),Linux)
GOARCH		= linux-amd64
endif
ifeq ($(OS),FreeBSD)
GOARCH		= freebsd-amd64
endif
GOBIN		= ${GOBASE}.${GOARCH}
GOSRC		= ${GOBASE}.src
GOBINTAR	= ${GOBIN}.tar.gz
GOSRCTAR	= ${GOSRC}.tar.gz
#--------------------------------------------------------------------------#




all:    	install-gobin

clean:		clean-go  

install-gobin: sources/${GOBINTAR}
	tar -zxf sources/${GOBINTAR} -C ${NLYTIQ_INST_PATH}
	echo "export GOROOT=${NLYTIQ_INST_PATH}/go" >> ${NLYTIQ_INST_PATH}/env.sh
	echo "export PATH=$$PATH:${NLYTIQ_INST_PATH}/bin:\$$GOROOT/bin" >> ${NLYTIQ_INST_PATH}/env.sh
	chmod +x ${NLYTIQ_INST_PATH}/env.sh
	touch install-gobin


clean-go:
	rm -rf install-gobin
