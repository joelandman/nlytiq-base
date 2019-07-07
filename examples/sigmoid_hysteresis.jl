#!/usr/bin/env julia
using Plots

# sigmoid function
s(a,x)=1/(1+exp(-a*x))

# offset sigmoid function
os(o,a,x) = s(a,x-o)

x  =  range(-5.0,5.0,step=0.1)
s1 =  os.(0,5,x)
s2 =  os.(-1,5,x)
s3 =  os.(1,5,x)

plot!(x,[s1,s2,s3])
