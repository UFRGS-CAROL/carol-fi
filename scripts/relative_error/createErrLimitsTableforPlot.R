#!/usr/bin/env Rscript
args = commandArgs(trailingOnly=TRUE)

if (length(args)<3) {
  stop("At least two arguments must be supplied: csv_in, benchmark name, csv_out", call.=FALSE)
}

dat = read.csv(args[1],sep=";")
#head(dat, 5)

execSDC = dim(dat)[1]
execSDC0.1 = 0
execSDC0.2 = 0
execSDC0.3 = 0
execSDC0.4 = 0
execSDC0.5 = 0
execSDC1 = 0
execSDC2 = 0
execSDC3 = 0
execSDC4 = 0
execSDC5 = 0
execSDC8 = 0
execSDC10 = 0
execSDC12 = 0
execSDC15 = 0
for (i in 1:dim(dat)[1]){
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan0.1[i]){
		execSDC0.1 = execSDC0.1 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan0.2[i]){
		execSDC0.2 = execSDC0.2 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan0.3[i]){
		execSDC0.3 = execSDC0.3 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan0.4[i]){
		execSDC0.4 = execSDC0.4 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan0.5[i]){
		execSDC0.5 = execSDC0.5 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan1[i]){
		execSDC1 = execSDC1 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan2[i]){
		execSDC2 = execSDC2 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan3[i]){
		execSDC3 = execSDC3 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan4[i]){
		execSDC4 = execSDC4 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan5[i]){
		execSDC5 = execSDC5 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan8[i]){
		execSDC8 = execSDC8 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan10[i]){
		execSDC10 = execSDC10 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan12[i]){
		execSDC12 = execSDC12 + 1
	}
	if(dat$numberIterationErrors[i] > dat$numberErrorsLessThan15[i]){
		execSDC15 = execSDC15 + 1
	}
}


per0.1 = (execSDC0.1 * 100 / execSDC)
per0.2 = (execSDC0.2 * 100 / execSDC)
per0.3 = (execSDC0.3 * 100 / execSDC)
per0.4 = (execSDC0.4 * 100 / execSDC)
per0.5 = (execSDC0.5 * 100 / execSDC)
per1 = (execSDC1 * 100 / execSDC)
per2 = (execSDC2 * 100 / execSDC)
per3 = (execSDC3 * 100 / execSDC)
per4 = (execSDC4 * 100 / execSDC)
per5 = (execSDC5 * 100 / execSDC)
per8 = (execSDC8 * 100 / execSDC)
per10 = (execSDC10 * 100 / execSDC)
per12 = (execSDC12 * 100 / execSDC)
per15 = (execSDC15 * 100 / execSDC)

print(paste("errLimit ; percentage; benchmark"))
errLimit =c("0.1", "0.2", "0.3", "0.4", "0.5", "1", "2", "3", "4", "5", "8", "10", "12", "15")
percentage = c(per0.1, per0.2, per0.3, per0.4, per0.5, per1, per2, per3, per4, per5, per8, per10, per12, per15)
benchmark = c(args[2], args[2], args[2], args[2], args[2], args[2], args[2], args[2], args[2], args[2], args[2], args[2], args[2], args[2])
myDat = data.frame(errLimit, percentage, benchmark)

write.csv(myDat, file = args[3])
#print(paste("0.1;",per0.1,";",args[2]))
#print(paste("0.2;",per0.2,";",args[2]))
#print(paste("0.3;",per0.3,";",args[2]))
#print(paste("0.4;",per0.4,";",args[2]))
#print(paste("0.5;",per0.5,";",args[2]))
#print(paste("1;",per1,";",args[2]))
#print(paste("2;",per2,";",args[2]))
#print(paste("3;",per3,";",args[2]))
#print(paste("4;",per4,";",args[2]))
#print(paste("5;",per5,";",args[2]))
