#!/usr/bin/env julia

using Pkg
using Printf

pkgs = [
	"Test",
	"BenchmarkTools",
	"DataFrames", 
	"StatsPlots",
	"DifferentialEquations",
	"Plots",
	"Gadfly",
	"CUDA",
	"DiffEqBase",
	"DiffEqPhysics",
	"DiffEqDevTools",
	"BoundaryValueDiffEq",
	"OrdinaryDiffEq",
	"Flux",
	"LinuxPerf",
	"SpecialFunctions",
	"ScikitLearn",
	"UnicodePlots",
	"FileIO",
	"Images",
	"ImageView",
	"Makie",
	"GeometryTypes",
	"Colors",
	"JSON",
	"FastGaussQuadrature",
	"FastTransforms",
	"IJulia",
	"JuliaInterpreter",
	"Zygote",
	"ForwardDiff",
	"DiffEqGPU",
	"PhysicalConstants",
	"VegaLite",
	"VegaDatasets",
	"CUTEst",
	"TimerOutputs",
	"Optim",
	"UnicodePlots",
	"Primes",
	"XLSX",
	"Query",
	"Pluto",
	"Turing",
	"PyPlot",
	"Javis",
	"OhMyREPL",
	"PackageCompiler"
       ]

for p ∈  pkgs
	@printf("Adding package %s\n",p)
	Pkg.add(p)
end

Pkg.add(PackageSpec(url="https://github.com/genieframework/Genie.jl"))
Pkg.add(PackageSpec(url="https://github.com/queryverse/Queryverse.jl"))
Pkg.precompile()
