### nlytiq base tool build
###

include base.config

### list of all supported packages

### select which version based upon if we are using clang

ifeq ($(CLANG),1)
packages = cmake llvm atlas perl5 perl5mods perl6 python go julia node spark R ruby octave
endif

ifeq ($(GCC),1)
# do not need llvm if we are not using it to compile everything 
packages = cmake atlas perl5 perl5mods perl6 python go julia node spark R ruby octave
endif

#  remove rust for now.  May be added back later.

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
	for p in $(packages) ; do \
	  touch $$p.build ;        \
	done

%.complete: %.build	
	$(MAKE) -f Makefile.$*
	touch $*.complete

clean:	
	for p in $(packages) ; do \
		$(MAKE) -f Makefile.$$p clean ; \
		rm -f $$p.build $$p.packages $$p.complete ; \
	done

