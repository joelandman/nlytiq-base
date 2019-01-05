### nlytiq base tool build
###

## build environment configuration
include config/base.config

## package options
include config/options.config


### list of all supported packages

compiler = cmake llvm 
prereqs  = curl pcre perl5 perl5mods 
locallibs= openblas atlas
base     = perl6 gnuplot python 
environs = octave julia R 
misc	 = jupyter_kernels spark 

# package construction
packages = 

#Linux
ifeq (${OS},Linux)

ifeq (${CLANG},1)
packages+=${compiler}
endif

packages+=${prereqs}

ifeq (${LOCALLIBS},1)
packages+=${locallibs}
endif

packages+=${base}

ifeq (${ENVIRONS},1)
packages+=${environs}
endif

ifeq (${MISC},1)
packages+=${misc}
endif

endif

# MacOSX
ifeq (${OS},Darwin)

ifeq (${CLANG},1)
packages+=${compiler}
endif

packages+=${prereqs}

ifeq (${LOCALLIBS},1)
packages+=${locallibs}
endif

packages+=${base}

ifeq (${ENVIRONS},1)
packages+=${environs}
endif

ifeq (${MISC},1)
packages+=${misc}
endif

endif


# FreeBSD
ifeq (${OS},FreeBSD)

ifeq (${CLANG},1)
packages+=${compiler}
endif

packages+=${prereqs}

ifeq (${LOCALLIBS},1)
packages+=${locallibs}
endif

packages+=${base}

ifeq (${ENVIRONS},1)
packages+=${environs}
endif

ifeq (${MISC},1)
packages+=${misc}
endif

endif


### each package has its own Makefile.  This Makefile drives complilation
### with a default target of all.  Each Makefile also has a clean target
### You can make them as simple/complex as you wish, as long as the above
### boundaries (all, clean) are respected, and are working ... such that
###
###    make -f Makefile.$package
### 
### will generate a newly installed package, and
### 
###    make -f Makefile.$package clean
###
### will clean up the build


### The below are the mechanisms used to create build targets, completed 
### build targets, and clean up.
###
build    = $(addsuffix .build,$(packages))
complete = $(addsuffix .complete,$(packages))

all:    	$(build) $(complete)

### generate the .build files
$(build):
	for p in $(packages) ; do  \
	  touch $$p.build ;        \
	done
ifeq ($(OS), Darwin)
# bad bad Apple.  Bad Apple.
	touch R.build R.complete octave.build octave.complete
# sigh ...
endif


%.complete: %.build
	mkdir -p ${NLYTIQ_INST_PATH}	
	$(MAKECMD) -f Makefile.$*
	touch $*.complete

clean:	
	for p in $(packages) ; do \
		$(MAKECMD) -f Makefile.$$p clean ; \
		rm -f $$p.build $$p.packages $$p.complete ; \
	done

