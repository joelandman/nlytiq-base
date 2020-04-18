#!/usr/bin/env julia
using Plots

# sigmoid function
s(a,x)   = 1/(1+exp(-a*x))

# first derivative of sigmoid function
d1s(a,x) = a*exp(-a*x)/((1+exp(-a*x))^2)

# second derivative of sigmoid function
d2s(a,x) = a * (2*d1s(a,x)*exp(-a*x)/(1+exp(-a*x))  - d1s(a,x))

x  =  range(-5.0,5.0,step=0.01)
s1   =  s.(5,x)
d1s1 =  d1s.(5,x)
#d2s1 =  d2s.(5,x)

plot(x,[s1,d1s1],yscale = :log10)
# ,d2s1]
#label = ["sigmoid", "dsigmoid/dx", "d^2sigmoid/dx^2"])
