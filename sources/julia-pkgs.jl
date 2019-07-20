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
	"CUDAdrv",
	"CuArrays",
	"CUDAnative",
	"DiffEqBase",
	"DiffEqPhysics",
	"DiffEqDevTools",
	"DiffEqPDEBase",
	"BoundaryValueDiffEq",
	"OrdinaryDiffEq",
	"Flux",
	"SpecialFunctions",
	"JuliaDB",
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
	"DiffEqFlux",
	"PhysicalConstants"
       ]

for p ∈  pkgs
	@printf("Adding package %s\n",p)
	Pkg.add(p)
end
