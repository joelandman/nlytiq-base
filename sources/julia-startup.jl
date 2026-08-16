# Site startup file for the nlytiq tree, installed by Makefile.julia into
# <prefix>/etc/julia/startup.jl.  Julia reads it on every start of this
# installation, before the user's own ~/.julia/config/startup.jl.
#
# Makefile.julia installs the package set into a depot inside the tree rather
# than into each user's ~/.julia, so everyone using the tree gets the same
# packages.  Julia looks only in ~/.julia by default, so point it here as well.
#
# Two things are needed, and they are not the same thing:
#
#   DEPOT_PATH  where package *files* live
#   LOAD_PATH   which environment 'using Foo' resolves against
#
# Adding the depot alone is not enough: the packages would be on disk but no
# environment would list them, and 'using DataFrames' would still fail.
#
# The user's own depot stays first in DEPOT_PATH, so anything they install
# themselves, and any precompilation cache they generate, still lands in
# ~/.julia.  That keeps the shared tree usable when it is read-only, which it
# will be wherever it is installed somewhere like /opt/nlytiq.

let depot = "__NLYTIQ_JULIA_DEPOT__"
    if isdir(depot)
        depot in DEPOT_PATH || push!(DEPOT_PATH, depot)
        env = joinpath(depot, "environments", "v$(VERSION.major).$(VERSION.minor)")
        isdir(env) && (env in LOAD_PATH || push!(LOAD_PATH, env))
    end
end
