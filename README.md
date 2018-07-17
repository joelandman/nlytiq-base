# nlytiq-base

## What?
This is a simple analytical toolchain providing a number of up to date
programming, analytical, and graphics tools.  This toolchain is meant
to be used to provide a preconfigured computing environment for data
scientists, engineers, analysts, people working on computing tasks
that require up-to-date tools.


## Why?
Sadly, the reason for this is that most operating system distributions
(Linux, etc.) tend to wrapper and ship older, often obsolete and
end-of-life versions of tools.  As often as not, compiled not to maximize
utility, but to simplify their packaging, or provide *check-boxes* that
they have this tool.

Add to these often out of date, and badly obsolete tools, their
mis-build options, their massive dependency radii ... which, as
often as not, has you pulling in unrelated packages in order to satisfy
specific build dependencies.  Dependencies that often have nothing
to do with the package itself.

Early on, when I started building these updated packages, I discovered that
replacing the internal distribution packages with the updated versions
could both help and hurt, in that the distribution vendor often has
in-built dependencies on a specific version of the package.  You are
welcome to #facepalm right now.  Working around bugs in a package is
understandable, we do this all the time.  When you build upon these work
arounds, the bugs become part of the package specification.

Which means if you replace the old broken package with a new updated
package, bad things (TM) will happen.  As the bugs that have been fixed,
are now effectively missing required features.

So we built our own tree.  The tree is located in /opt/nlytiq by default.
But you can put it anywhere.  Just edit base.config, and follow the comments.

##Packages
The packages are broadly programming environments that are very strong
analytical systems on the own, and more general programming environments
that can be used to build and bridge other analytical systems.

High performance analytical programming environments

* [Julia](http://julialang.org)
* [R](https://cran.r-project.org/)
* [Octave](https://www.gnu.org/software/octave/)

High performance general programming environments
* [Python 3.x](http://www.python.org)
   * Python packages including numpy, scipy, matlibplot,
     Jupyter, pandas, Theano, ...
* [Perl 5.x](http://www.cpan.org)
   * Many Perl modules
* REMOVED [Ruby 2.x](https://www.ruby-lang.org/en/)
* REMOVED [NodeJS 6.x](https://nodejs.org/en/)
* REMOVED [Go 1.10.x](https://golang.org/) 
* [Perl 6.x](https://perl6.org/)
   * Perl6 modules including panda
* REMOVED [Rust 0.26.x](https://www.rust-lang.org/en-US/)

##Status
This is still in the early stages of development.  Most of the
tools are built from source, though we are currently using go-lang
binaries from the go site.  This will change soon, but the go build
is a self hosted/bootstrapped system, so there are additional
complications.

##Roadmap
Glad you asked.  The concept is to provide an eventually complete
system that one can use physically installed on a system, or
via a docker image, or some other mechanism, to provide up to date
and well maintained/curated tools that are generally useful.  Then
tie them together with a system like
[Beaker](http://beakernotebook.com/), as well as other tools I am
developing.  The idea is to provide an analytical cloud experience
that should be easy to self/remotely host, tie in data sets/sources
and interact with any scale analytics.  The tools should work as well
with data sets of 4 measurements, as they should with 4 x 10<sup>15</sup>
measurements.

##Who
Me:  Joe Landman (joe _dot_ landman at our friends at google's mail service)

##License
Each project has its own licensing, but all are open source.  Our code,
the makefiles, are Apache 2.0 licensed.

##How do I build it
See the HOWTO
