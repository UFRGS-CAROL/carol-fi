#!/usr/bin/env python

import sys
import os
import csv
import re
import collections
import parseUtils


# Processa os erros depois de feito o parser e salva um resumo num arquivo CSV
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
        csvFullPath = csvDirOut

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


# Faz o parser de um elemento corrompido e coloca num formato especifico para ser processado posteriormente: {"positions" : listPosition, "values" : listValues}
# Retorna None se nao eh possivel fazer o parser 
def parseErrMxM(errString):
        try:
                #ERR p: [0, 0], r: 3.0815771484375000e+02, e: 0.0000000000000000e+00
                m = re.match(".*ERR.*\[(\d+)..(\d+)\].*r\: ([0-9e\+\-\.]+).*e\: ([0-9e\+\-\.]+)", errString)
                if m:
                        posX = int(m.group(1))
                        posY = int(m.group(2))
                        read = float(m.group(3))
                        expected = float(m.group(4))
                        positions = [ ["x",posX], ["y",posY] ]
                        values = [ ["v", read, expected] ]
                        return {"position":positions, "values":values}
                else:
                        return None
        except ValueError:
                return None

###########################################
# MAIN
###########################################

# Define qual o arquivo que sera salvo os dados processados de cada erro
csvDirOut = "mxm_logs_parsed.csv"
print "\n\tCSV files will be stored in "+csvDirOut+" folder\n"

# Abre o arquivo que contem todas as execucoes erradas
fi = open("mxm-errors.log", "r")

# Para cada SDC (execucao com 1 ou mais elementos corrompidos) salva os elementos corrompidos numa lista (errList) e processa aquela execucao com SDC
errList = list()
for l in fi:
    # Para cada SDC novo, verifica se tem dados do SDC anterior e processa esses dados
    if re.search("SDC", l):
        if len(errList) > 0: # Se tem dados de um SDC anterior, processa eles
            print "Processing #"+str(len(errList))+" corrupted elements in this SDC\n"
            processErrors(errList)
        print "SDC found: "+l.strip() # Inicia uma lista vazia para novos elementos corrompidos do SDC que esta iniciando
        errList = list()

    if re.search("ERR", l): # Para cada elemento errado, coloca ele no formato correto e adiciona na lista de elementos corrompidos deste SDC em especifico
        err = parseErrMxM(l)
        if err is not None:
            errList.append(err)

if len(errList) > 0: # Processa os elementos corrompidos do ultimo SDC encontrado no loop anterior
    print "Processing #"+str(len(errList))+" corrupted elements in this SDC\n"
    processErrors(errList)

print "Done\n"
sys.exit(0)
