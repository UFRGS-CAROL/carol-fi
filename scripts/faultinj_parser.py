#!/usr/bin/env python3
import os
import re
import csv
from collections import Counter

varSDCList = list()
varSDCDetectList = list()
varCrashList = list()
varHangList = list()
flipList = list()
faultModelCrash = list()
faultModelHang = list()
faultModelSDC = list()
faultModelSDCDetect = list()

flipCount = 0
sdcCount = 0
sdcDetectCount = 0
crashCount = 0
hangCount = 0

sdcFilename = "sdc.csv"
crashFilename = "crash.csv"
hangFilename = "hang.csv"
summFilename = "summary.csv"

def processDirectory(dirName, fileList):
    #print('Found directory: %s' % dirName)
    flipInfo = ""
    flip=False
    sdc=0
    sdcDetect=0
    crash=0
    hang=0
    var = ""
    varFile = ""
    varLine = ""
    faultTime = ""
    faultModel = ""
    signalTime = ""
    for fname in fileList:
#        if re.search("knl.log",fname):
#            (sdc, crash) = getSDCCrashInfo(dirName, fname)
        if re.search("carolfi-flipvalue",fname):
            (flip, flipInfo, var, varFile, varLine, faultTime, faultModel, signalTime) = getFlipInfo(dirName, fname)
            if re.search("sdcs",dirName):
                sdc = 1
                if re.search("sdcs-detected",dirName):
                    sdcDetect = 1
                else:
                    sdcDetect = 0
            else:
                sdc = 0
                sdcDetect = 0
            if re.search("hangs",dirName):
                hang = 1
            else:
                hang = 0
            if re.search("crashes",dirName) or re.search("noOutputGenerated",dirName):
                crash = 1
            else:
                crash = 0
    if flip:
        global flipCount
        global sdcCount
        global sdcDetectCount
        global crashCount
        global hangCount
        if var != "":
            flipCount += 1
            varInfo = var+";"+varFile+";"+str(varLine)
            flipList.append(varInfo)
            if sdc == 1:
                sdcCount += 1
                varSDCList.append(varInfo)
                faultModelSDC.append(faultModel)
                if sdcDetect == 1:
                    sdcDetectCount += 1
                    varSDCDetectList.append(varInfo)
                    faultModelSDCDetect.append(faultModel)
                csvWFP = open(current_folder_name+"_"+sdcFilename, "a")
                writer = csv.writer(csvWFP, delimiter=';')
                writer.writerow([var,varFile,str(varLine),str(faultTime),str(signalTime),str(faultModel),str(sdcDetect)])
                csvWFP.close()
            elif crash == 1:
                crashCount += 1
                varCrashList.append(varInfo)
                faultModelCrash.append(faultModel)
                csvWFP = open(current_folder_name+"_"+crashFilename, "a")
                writer = csv.writer(csvWFP, delimiter=';')
                writer.writerow([var,varFile,str(varLine),str(faultTime),str(signalTime),str(faultModel)])
                csvWFP.close()
            elif hang == 1:
                hangCount += 1
                varHangList.append(varInfo)
                faultModelHang.append(faultModel)
                csvWFP = open(current_folder_name+"_"+hangFilename, "a")
                writer = csv.writer(csvWFP, delimiter=';')
                writer.writerow([var,varFile,str(varLine),str(faultTime),str(signalTime),str(faultModel)])
                csvWFP.close()


def getSDCCrashInfo(dirName, fname):
    fp = open(dirName+"/"+fname, "r", errors="replace")
    content = fp.read()
    sdc = 0
    crash = 1
    if re.search("SDC", content):
        sdc = 1
    if re.search("END", content):
        crash = 0
    return (sdc, crash)

def getFlipInfo(dirName, fname):
    fp = open(dirName+"/"+fname, "r", errors="ignore")
    content = fp.read()
    flip = False
    if re.search("Fault Injection Successful",content):
        flip = True
    if flip:
        fp.seek(0)
        btC = False
        bt = ""
        symbolName = ""
        symbolFilename = ""
        symbolLine = 0
        faultTime = -1
        faultModel=""
        initSignal=-1
        endSignal=-1
        for line in fp:
            if re.search("Backtrace BEGIN:",line):
                bt = "Backtrace BEGIN:\n"
                btC = True
            if re.search("Backtrace END", line):
                btC = False
                bt += "Backtrace END\n"
            if btC:
                bt += line
            m = re.match(".*(Memory content before bitflip:.*)",line)
            if m:
                bt += m.group(1)
            m = re.match(".*(Memory content after  bitflip:.*)",line)
            if m:
                bt += m.group(1)
            m = re.match(".*(frame name:.*)",line)
            if m:
                bt += m.group(1)
            m = re.match(".*(symbol name: )(.*)",line)
            if m:
                bt += m.group(1)+m.group(2)
                symbolName = m.group(2)
            m = re.match(".*(symbol filename: )(.*)",line)
            if m:
                bt += m.group(1)+m.group(2)
                symbolFilename = m.group(2)
            m = re.match(".*(Fault Model: )(.*)",line)
            if m:
                bt += m.group(1)+m.group(2)
                faultModel = m.group(2)
            #initSignal:0
            m = re.match(".*(initSignal:)(.*)",line)
            if m:
                bt += m.group(1)+m.group(2)
                initSignal = m.group(2)
            #endSignal:2
            m = re.match(".*(endSignal:)(.*)",line)
            if m:
                bt += m.group(1)+m.group(2)
                endSignal = m.group(2)
            m = re.match(".*(symbol line: )(.*)",line)
            if m:
                bt += m.group(1)+m.group(2)
                symbolLine = m.group(2)
                #Fault Injection Successful after 0.692039966583s
            m = re.match(".*(Fault Injection Successful after )(\d+.\d+)s",line)
            if m:
                bt += m.group(1)+m.group(2)+"s"
                faultTime = m.group(2)

        return (flip, bt, symbolName, symbolFilename, symbolLine, faultTime, faultModel,initSignal+"-"+endSignal)
    else:
        return (flip, "", "", "", "", "", "", "")

cwd = os.getcwd()
current_folder_path, current_folder_name = os.path.split(os.getcwd())
print ("Processing directory "+cwd)
print ("Processing folder "+current_folder_name)

csvWFP = open(current_folder_name+"_"+sdcFilename, "w")
writer = csv.writer(csvWFP, delimiter=';')
writer.writerow(["Variable Name","Variable File","Variable Line","Fault Injection Time(s)","Injection Time Interval","Fault Model","Detected"])
csvWFP.close()
csvWFP = open(current_folder_name+"_"+crashFilename, "w")
writer = csv.writer(csvWFP, delimiter=';')
writer.writerow(["Variable Name","Variable File","Variable Line","Fault Injection Time(s)","Injection Time Interval","Fault Model"])
csvWFP.close()
csvWFP = open(current_folder_name+"_"+hangFilename, "w")
writer = csv.writer(csvWFP, delimiter=';')
writer.writerow(["Variable Name","Variable File","Variable Line","Fault Injection Time(s)","Injection Time Interval","Fault Model"])
csvWFP.close()

# Set the directory you want to start from
rootDir = '.'
for dirName, subdirList, fileList in os.walk(rootDir):
    processDirectory(dirName, fileList)
#print ("varCrashList: ", Counter(varCrashList).most_common(20))
#print ("varSDCList: ", Counter(varSDCList).most_common(20))

maskedCount = flipCount - sdcCount - crashCount - hangCount
sdcPVF = "N/A"
if sdcCount:
    sdcPVF = sdcCount/flipCount
crashPVF = "N/A"
if crashCount:
    crashPVF = crashCount/flipCount
hangPVF = "N/A"
if hangCount:
    hangPVF = hangCount/flipCount
maskedPVF = "N/A"
if maskedCount:
    maskedPVF = maskedCount/flipCount
fp = open(current_folder_name+"_"+summFilename, "w")
fp.write("Faults Injected:;"+str(flipCount))

fp.write("\n\nFault Effect;#Effect;PVF")
fp.write("\nMasked;"+str(maskedCount)+";"+str(maskedPVF))
fp.write("\nSDCs;"+str(sdcCount)+";"+str(sdcPVF))
fp.write("\nCrashes;"+str(crashCount)+";"+str(crashPVF))
fp.write("\nHangs;"+str(hangCount)+";"+str(hangPVF))
fp.write("\n\n")
fp.write("\nDetected SDCs:;"+str(sdcDetectCount))
fp.write("\nSDC Coverage (%):;"+str((sdcDetectCount*100)/sdcCount))
fp.write("\n\n")

flips = Counter(flipList)

if faultModelSDC:
    fp.write("FaultModels SDCs:")
    fp.write("\nFaultModel ;#SDCs;percentage")
    for k,v in Counter(faultModelSDC).most_common():
        try:
            per = float(v)/float(sdcCount) * 100
        except:
            per = "N/A"
        fp.write("\n"+str(k)+";"+str(v)+";"+str(per))

if faultModelSDCDetect:
    fp.write("\n\n")
    fp.write("FaultModels Detected SDCs:")
    fp.write("\nFaultModel ;#SDCs Detected; percentage")
    for k,v in Counter(faultModelSDCDetect).most_common():
        try:
            per = float(v)/float(sdcCount) * 100
        except:
            per = "N/A"
        fp.write("\n"+str(k)+";"+str(v)+";"+str(per))

if faultModelCrash:
    fp.write("\n\n")
    fp.write("FaultModels Crashes:")
    fp.write("\nFaultModel ;#Crashes;percentage")
    for k,v in Counter(faultModelCrash).most_common():
        try:
            per = float(v)/float(crashCount) * 100
        except:
            per = "N/A"
        fp.write("\n"+str(k)+";"+str(v)+";"+str(per))

if faultModelHang:
    fp.write("\n\n")
    fp.write("FaultModels Hangs:")
    fp.write("\nFaultModel ;#Hangs;percentage")
    for k,v in Counter(faultModelHang).most_common():
        try:
            per = float(v)/float(hangCount) * 100
        except:
            per = "N/A"
        fp.write("\n"+str(k)+";"+str(v)+";"+str(per))

if varSDCList:
    fp.write("\n\n")
    fp.write("Variables that caused SDCs:")
    fp.write("\nPVF ;#flips ;#SDCs ;Var name ;file ;line number")
    for k,v in Counter(varSDCList).most_common():
        try:
            pvf = float(v)/float(flips[k]) * 100
        except:
            pvf = "N/A"
        fp.write("\n"+str(pvf)+";"+str(flips[k])+";"+str(v)+";"+k)

if varSDCDetectList:
    fp.write("\n\n")
    fp.write("Variables that caused Detected SDCs:")
    fp.write("\nPVF ;#flips ;#SDCs ;Var name ;file ;line number")
    for k,v in Counter(varSDCDetectList).most_common():
        try:
            pvf = float(v)/float(flips[k]) * 100
        except:
            pvf = "N/A"
        fp.write("\n"+str(pvf)+";"+str(flips[k])+";"+str(v)+";"+k)

if varCrashList:
    fp.write("\n")
    fp.write("\nVariables that caused Crash:")
    fp.write("\nPVF ;#flips ;#SDCs ;Var name ;file ;line number")
    for k,v in Counter(varCrashList).most_common():
        try:
            pvf = float(v)/float(flips[k]) * 100
        except:
            pvf = "N/A"
        fp.write("\n"+str(pvf)+";"+str(flips[k])+";"+str(v)+";"+k)

if varHangList:
    fp.write("\n")
    fp.write("\nVariables that caused Hang:")
    fp.write("\nPVF ;#flips ;#SDCs ;Var name ;file ;line number")
    for k,v in Counter(varHangList).most_common():
        try:
            pvf = float(v)/float(flips[k]) * 100
        except:
            pvf = "N/A"
        fp.write("\n"+str(pvf)+";"+str(flips[k])+";"+str(v)+";"+k)

fp.close()
