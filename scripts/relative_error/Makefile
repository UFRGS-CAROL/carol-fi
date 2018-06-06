# Need R and ggplot install. For ubuntu users: sudo apt install r-base-core r-cran-ggplot2
all: process.py parseUtils.py createErrLimitsTableforPlot.R lineGraph.R 
	./process.py
	./createErrLimitsTableforPlot.R out.csv benchmark_name errLimit.csv
	./lineGraph.R errLimit.csv errLimit.pdf

clear:
	rm -f out.csv errLimit.csv errLimit.pdf parseUtils.pyc
