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
	"Gadfly",
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
	"DiffEqGPU",
	"TimerOutputs",
	"UnicodePlots",
	"Primes",
	"XLSX",
	"Query",
	"Pluto",
	"Turing",
	"PyPlot",
	"Javis",
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
	"ThreadsX",
	"HTTP"
       ]

for p ∈  pkgs
	@printf("Adding package %s\n",p)
	Pkg.add(p)
end

Pkg.add(PackageSpec(url="https://github.com/genieframework/Genie.jl"))
Pkg.add(PackageSpec(url="https://github.com/queryverse/Queryverse.jl"))
Pkg.precompile()
