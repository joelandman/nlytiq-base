include config/base.config

#### go
GOVER			= 1.16.3

ifeq (${OS},Linux)
GOTAR			= go${GOVER}.linux-amd64.tar.gz
endif

#--------------------------------------------------------------------------#

all:    	install-gobin

clean:		clean-go

install-gobin: sources/${GOTAR}
	tar -C ${NLYTIQ_INST_PATH} -zxf sources/${GOTAR}
	touch install-gobin

clean-go:
	rm -rf install-gobin
