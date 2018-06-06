#!/usr/bin/env python

import sys
import os
import csv
import re
import collections
import parseUtils


def processErrors(errList):
        errLimitList = [0.1,0.2,0.3,0.4,0.5,1,2,3,4,5,8,10,12,15]
        csvHeader = list()
        csvHeader.append("numberIterationErrors")
        csvHeader.append("maxRelativeError")
        csvHeader.append("minRelativeError")
        csvHeader.append("averageRelativeError")
        for errLimit in errLimitList:
            csvHeader.append("numberErrorsLessThan"+str(errLimit))


        csvOutDict = dict()
        csvOutDict["numberIterationErrors"]=len(errList)
        for errLimit in errLimitList:
            (maxRelErr, minRelErr, avgRelErr, relErrLowerLimit, errListFiltered) = parseUtils.relativeErrorParser(errList, errLimit)
            csvOutDict["maxRelativeError"] = maxRelErr
            csvOutDict["minRelativeError"] = minRelErr
            csvOutDict["averageRelativeError"] = avgRelErr
            csvOutDict["numberErrorsLessThan"+str(errLimit)] = relErrLowerLimit



	# Write info to csv file
        csvFullPath = "out.csv"

        if not os.path.isfile(csvFullPath):
	    csvWFP = open(csvFullPath, "a")
	    writer = csv.writer(csvWFP, delimiter=';')
            writer.writerow(csvHeader)
        else:
	    csvWFP = open(csvFullPath, "a")
	    writer = csv.writer(csvWFP, delimiter=';')
        row = list()
        for item in csvHeader:
            if item in csvOutDict:
                row.append(csvOutDict[item])
            else:
                row.append(" ")
        writer.writerow(row)

	csvWFP.close()


###########################################
# MAIN
###########################################
csvDirOut = "csv_logs_parsed"
print "\n\tCSV files will be stored in "+csvDirOut+" folder\n"



#### Example errors from execution #1
errList1 = list()

positionsExample = [ ["x",5], ["y",10], ["z",0] ]
valuesExample = [ ["force", 10, 10], ["energy", 10, 11], ["velocity", 1, 1] ]
errItem = {"position" : positionsExample, "values" : valuesExample}
errList1.append(errItem)

positionsExample = [ ["x",5], ["y",0], ["z",40] ]
valuesExample = [ ["force", 10, 9.5], ["energy", 20, 21], ["velocity", 5, 5] ]
errItem = {"position" : positionsExample, "values" : valuesExample}
errList1.append(errItem)

#### Example errors from execution #2
errList2 = list()

positionsExample = [ ["x",3], ["y",12], ["z",0] ]
valuesExample = [ ["force", 10, 10], ["energy", 10, 10], ["velocity", 1, 2] ]
errItem = {"position" : positionsExample, "values" : valuesExample}
errList2.append(errItem)

positionsExample = [ ["x",50], ["y",50], ["z",50] ]
valuesExample = [ ["force", 2, 3], ["energy", 1, 1], ["velocity", 50, 50] ]
errItem = {"position" : positionsExample, "values" : valuesExample}
errList2.append(errItem)

positionsExample = [ ["x",5], ["y",0], ["z",40] ]
valuesExample = [ ["force", 10, 9.5], ["energy", 20, 20], ["velocity", 5, 5] ]
errItem = {"position" : positionsExample, "values" : valuesExample}
errList2.append(errItem)


### Process errors
processErrors(errList1)
processErrors(errList2)
