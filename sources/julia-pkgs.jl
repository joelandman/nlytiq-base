#!/usr/bin/env julia

using Pkg
using Printf

pkgs = [
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
	"BenchmarkTools",
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
	"JuliaInterpreter"
       ]

for p ∈  pkgs
	@printf("Adding package %s\n",p)
	Pkg.add(p)
end
