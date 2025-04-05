#!/usr/bin/env julia

using Pkg
using Printf

pkgs = [
	"BenchmarkTools",
	"DataFrames", 
	"DataFramesMeta",
	"StatsPlots",
	"Plots",
	"UnicodePlots",
	"FileIO",
	"Colors",
	"JSON",
	"IJulia",
	"UnicodePlots",
	"PackageCompiler",
	"LoopVectorization",
	"ArgParse",
	"ArgMacros",
	"Distributions",
	"CSV",
	"Statistics",
	"StatsBase",
	"HTTP",
	"ThreadsX",
	"Revise"
       ]

for p ∈  pkgs
	@printf("Adding package %s\n",p)
	Pkg.add(p)
end

Pkg.add(PackageSpec(url="https://github.com/genieframework/Genie.jl"))
#Pkg.add(PackageSpec(url="https://github.com/eliascarv/WebAPI.jl"))
Pkg.add(PackageSpec(url="https://github.com/kmsquire/ArgParse2.jl"))

Pkg.precompile()
