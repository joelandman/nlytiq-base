#!/usr/bin/env julia
using StatsPlots
using DataFrames

# sigmoid function
s(a,x)=1/(1+exp(-a*x))

# offset sigmoid
os(o,a,x) = s(a,x-o)
x  =  range(-5,stop=5,101)
s1 =  os.(0,5,x)
s2 =  os.(-1,5,x)
s3 =  os.(1,5,x)
df = DataFrame(a=x, b=s1, c=s2, d=s3)

# plot
@df df plot(:a, [:b :c :d], title="Sigmoid function with hysteresis",leg=false)
savefig("sfh.png")
exit
