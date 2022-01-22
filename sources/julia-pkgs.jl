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
	"LinuxPerf",
	"UnicodePlots",
	"FileIO",
	"Images",
	"ImageView",
	"GeometryTypes",
	"Colors",
	"JSON",
	"IJulia",
	"JuliaInterpreter",
	"Zygote",
	"ForwardDiff",
	"TimerOutputs",
	"UnicodePlots",
	"Primes",
	"XLSX",
	"Query",
	"Pluto",
	"Turing",
	"PyPlot",
#	"Javis",
	"OhMyREPL",
	"PackageCompiler",
	"LoopVectorization",
	"ArgParse",
	"Distributions",
	"CSV",
	"Statistics",
	"StatsBase",
	"Loess",
	"DSP",
	"SmoothingSplines",
	"HTTP",
	"ThreadsX",
	"BenchmarkHistograms",
	"ProfileView",
	"Revise"
       ]

for p ∈  pkgs
	@printf("Adding package %s\n",p)
	Pkg.add(p)
end

Pkg.add(PackageSpec(url="https://github.com/genieframework/Genie.jl"))
Pkg.add(PackageSpec(url="https://github.com/queryverse/Queryverse.jl"))
Pkg.add(PackageSpec(url="https://github.com/eliascarv/WebAPI.jl"))
Pkg.precompile()
