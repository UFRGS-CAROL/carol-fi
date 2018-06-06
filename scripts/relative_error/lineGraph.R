#!/usr/bin/env Rscript

library(ggplot2)
args = commandArgs(trailingOnly=TRUE)

if (length(args)<2) {
  stop("At least two argument must be supplied, input file and outputfile", call.=FALSE)
}

dat = read.csv(args[1],sep=",")

pdf(file = args[2])
ggplot(dat, aes(x=errLimit, y=percentage, colour=benchmark), method = "lm", formula = y ~ poly(x, 10)) +
ylim(0,100)+
geom_line(size=1.1) +
labs(x = "Tolerated Relative Error [%]", y = "PVF/AVF rate [%]", color="Benchmark") +
theme(legend.position="bottom",axis.text.x=element_text(size=14) , axis.text.y=element_text(size=14) , text = element_text(size = 14)) 

dev.off()
