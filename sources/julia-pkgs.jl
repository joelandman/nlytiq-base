#!/usr/bin/env julia

using Pkg
using Printf

pkgs = [
	"Test",
	"BenchmarkTools",
	"DataFrames", 
	"DataFramesMeta",
	"StatsPlots",
	"Plots",
	"CUDA",
  "AMDGPU",
	"UnicodePlots",
	"FileIO",
	"Colors",
	"JSON",
	"IJulia",
	"JuliaInterpreter",
	"UnicodePlots",
	"Query",
	"Pluto",
	"PackageCompiler",
	"LoopVectorization",
	"ArgParse",
	"ArgMacros",
	"Distributions",
	"CSV",
	"JSON",
	"Statistics",
	"StatsBase",
	"Loess",
	"DSP",
	"SmoothingSplines",
	"HTTP",
	"ThreadsX",
	"ProfileView",
	"Revise",
	"StaticCompiler",
	"StaticTools"
       ]

for p ∈  pkgs
	@printf("Adding package %s\n",p)
	Pkg.add(p)
end

Pkg.add(PackageSpec(url="https://github.com/genieframework/Genie.jl"))
#Pkg.add(PackageSpec(url="https://github.com/eliascarv/WebAPI.jl"))
Pkg.add(PackageSpec(url="https://github.com/kmsquire/ArgParse2.jl"))

Pkg.precompile()
