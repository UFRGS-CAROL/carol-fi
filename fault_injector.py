#!/usr/bin/python
from __future__ import print_function
import os
import sys
import time
import datetime
import random
import subprocess
import threading
import re
import filecmp
import shutil
import argparse
import hashlib
import uuid
#import logging

if sys.version_info >= (3,0):
    import configparser # python 3
else:
    import ConfigParser # python 2

### Script version
VERSION = "1.0"

### Global variables
uniqueID = str(uuid.uuid4())
gdbFIlogFile = "/tmp/carolfi-"+uniqueID+".log"
summFIlogFile = "summary-carolfi.log"
if sys.version_info >= (3,0):
    conf = configparser.ConfigParser()
else:
    conf = ConfigParser.ConfigParser()



class logging:
    @staticmethod
    def info(msg):
        fp = open(gdbFIlogFile, "a")
        #fp = open(conf.get("DEFAULT","gdbFIlogFile"), "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[INFO -- "+d+"]\n"+msg+"\n")
        fp.close()

    @staticmethod
    def error(msg):
        fp = open(gdbFIlogFile, "a")
        #fp = open(conf.get("DEFAULT","gdbFIlogFile"), "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[ERROR -- "+d+"]\n"+msg+"\n")
        fp.close()

    @staticmethod
    def debug(msg):
        if conf.getboolean("DEFAULT","debug"):
            fp = open(gdbFIlogFile, "a")
            #fp = open(conf.get(section,"gdbFIlogFile"), "a")
            d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            fp.write("[DEBUG -- "+d+"]\n"+msg+"\n")
            fp.close()

    @staticmethod
    def summary(msg):
        fp = open(summFIlogFile, "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[SUMMARY -- "+d+"]\nFI-uniqueID="+uniqueID+"\n"+msg+"\n")
        fp.close()

# Signal the app to stop so GDB can execute the script to flip a value
class signalApp (threading.Thread):
    def __init__(self, section):
        threading.Thread.__init__(self)
        self.section = section
    def run(self):
        global timestampStart
        timestampStart = int(time.time())
        signalCmd = conf.get(self.section, "signalCmd")
        maxWaitTime = conf.getfloat(self.section,"maxWaitTime")
        init = conf.getfloat(self.section,"initSignal")
        end = conf.getfloat(self.section,"endSignal")
        seqSignals = conf.getint(self.section,"seqSignals")
        # Sleep for a random time
        waitTime = random.uniform(init,end)
        time.sleep(waitTime)
        # Send a series of signal to make sure gdb will flip a value in one of the interupt signals
        logging.info("sending "+str(seqSignals)+" signals using command: '"+signalCmd+"' after "+str(waitTime)+"s")
        for i in range(0,seqSignals):
            proc = subprocess.Popen(signalCmd, stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
            if out is not None:
                logging.info("shell stdout: "+str(out))
            if err is not None:
                logging.error("shell stderr: "+str(err))
            time.sleep(0.01)

# Start the gdb script
class runGDB (threading.Thread):
    def __init__(self, section):
        threading.Thread.__init__(self)
        self.section = section
    def run(self):
        startCmd = conf.get(self.section,"gdbExecName")+" -n -q -batch -x "+"/tmp/flip-"+uniqueID+".py"
        os.system(startCmd)


# Check if app stops execution (otherwise kill it after a time) 
def finish(section):
    isHang = False
    now = int(time.time())
    # Wait 2 times the normal duration of the program before killing it
    maxWaitTime = conf.getfloat(section,"maxWaitTime")
    gdbExecName = conf.get(section,"gdbExecName")
    checkRunning = "ps -e | grep -i "+gdbExecName
    killStrs = conf.get(section,"killStrs")
    while ((now - timestampStart) < (maxWaitTime*2)):
        time.sleep(maxWaitTime/10)
        # Check if the gdb is still running, if not, stop waiting
        proc = subprocess.Popen(checkRunning, stdout=subprocess.PIPE, shell=True)
        (out,err)=proc.communicate()
        if(not re.search(gdbExecName,str(out))):
            logging.debug("Process "+str(gdbExecName)+" not running, out:"+str(out))
            logging.debug("check command: "+checkRunning)
            break
        now = int(time.time())
    if ((now - timestampStart) < maxWaitTime*2):
        logging.info("Execution finished before waitTime")
    else:
        logging.info("Execution did not finish before waitTime")
        isHang = True
    logging.debug("now: "+str(now))
    logging.debug("timestampStart: "+str(timestampStart))

    # Kill all the processes to make sure the machine is clean for another test
    for k in killStrs.split(";"):
        proc = subprocess.Popen(k, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        logging.debug("kill cmd: "+k)
        if out is not None:
            logging.debug("kill cmd, shell stdout: "+str(out))
        if err is not None:
            logging.error("kill cmd, shell stderr: "+str(err))

    return isHang

# Copy the logs and output(if fault not masked) to a selected folder
def saveOutput(section, isSDC, isHang):
    outputFile = conf.get(section,"outputFile")
    flipLogFile = "/tmp/carolfi-flipvalue-"+uniqueID+".log"


    fiSucc = False
    if os.path.isfile(flipLogFile):
        fp = open(flipLogFile, "r")
        content = fp.read()
        if re.search("Fault Injection Successful",content):
            fiSucc = True
        fp.close()

    
    dt = datetime.datetime.fromtimestamp(time.time())
    ymd = dt.strftime('%Y_%m_%d')
    ymdhms = dt.strftime('%Y_%m_%d_%H_%M_%S')
    ymdhms = uniqueID+"-"+ymdhms
    dirDT = os.path.join(ymd,ymdhms)
    masked = False
    if not fiSucc:
        cpDir = os.path.join('logs',section,'failed-injection',dirDT)
        logging.summary(section+" - Fault Injection Failed")
    elif isHang:
        cpDir = os.path.join('logs',section,'hangs',dirDT)
        logging.summary(section+" - Hang")
    elif isSDC:
        cpDir = os.path.join('logs',section,'sdcs',dirDT)
        logging.summary(section+" - SDC")
    elif not os.path.isfile(outputFile):
        cpDir = os.path.join('logs',section,'noOutputGenerated',dirDT)
        logging.summary(section+" - NoOutputGenerated")
    else:
        cpDir = os.path.join('logs',section,'masked',dirDT)
        logging.summary(section+" - Masked")
        masked = True

    if not os.path.isdir(cpDir):
        os.makedirs(cpDir)

    shutil.move(flipLogFile, cpDir)
    shutil.move(gdbFIlogFile, cpDir)
    if os.path.isfile(outputFile) and (not masked) and fiSucc and isSDC and (not isHang):
        shutil.move(outputFile, cpDir)


def preExecution(section):
    try:
        script = conf.get(section,"preExecScript")
        if script != "":
            os.system(script)
        return
    except:
        return

def posExecution(section):
    try:
        script = conf.get(section,"posExecScript")
        if script != "":
            os.system(script)
        return
    except:
        return

# Check output files for SDCs
def checkSDCs(section):
    goldFile = conf.get(section,"goldFile")
    outputFile = conf.get(section,"outputFile")
    if not os.path.isfile(outputFile):
        logging.error("outputFile not found: "+str(outputFile))
    if os.path.isfile(goldFile) and os.path.isfile(outputFile):
        return (not filecmp.cmp(goldFile,outputFile, shallow=False) )
    else:
        return False

# Main function to run one execution of the fault injector
def runGDBFaultInjection(section):
    isSDC = False
    isHang = False

    logging.info("Starting GDB script")
    init = conf.getfloat(section,"initSignal")
    end = conf.getfloat(section,"endSignal")
    seqSignals = conf.getint(section,"seqSignals")
    logging.info("initSignal:"+str(init))
    logging.info("endSignal:"+str(end))
    logging.info("seqSignal:"+str(seqSignals))
    timestampStart = int(time.time())

    # Generate configuration file for specific test
    genConfFile(section)

    # Generate python script for GDB
    genFlipScript(section)

    # Run pre execution function
    preExecution(section)

    # Create one thread to start gdb script
    th = runGDB(section)
    # Create numThreadsFI threads to signal app at a random time
    numThreadsFI = conf.getint(section,"numThreadsFI")
    sigThs = list()
    for i in range(0,numThreadsFI):
        sigThs.append(signalApp(section))
    # Start threads
    th.start()
    for sig in sigThs:
        sig.start()

    # Check if app stops execution (otherwise kill it after a time)
    isHang = finish(section)

    # Run pos execution function
    posExecution(section)

    # Check output files for SDCs
    isSDC = checkSDCs(section)

    # Copy output files to a folder
    saveOutput(section, isSDC, isHang)

    # Make sure threads finish before trying to execute again
    th.join()
    for sig in sigThs:
        sig.join()
    del sigThs[:]

# Generate config file for the gdb flip_value script
def genConfFile(section):
    if sys.version_info >= (3,0):
        fconf = configparser.SafeConfigParser()
    else:
        fconf = ConfigParser.SafeConfigParser()
    #fconf.set("DEFAULT", "flipLogFile", conf.get(section,"flipLogFile"))
    fconf.set("DEFAULT", "flipLogFile", "/tmp/carolfi-flipvalue-"+uniqueID+".log")
    fconf.set("DEFAULT", "debug", conf.get(section,"debug"))
    fconf.set("DEFAULT", "gdbInitStrings", conf.get(section,"gdbInitStrings"))
    fconf.set("DEFAULT", "initSignal", conf.get(section,"initSignal"))
    fconf.set("DEFAULT", "endSignal", conf.get(section,"endSignal"))
    fconf.set("DEFAULT", "seqSignals", conf.get(section,"seqSignals"))
    fconf.set("DEFAULT", "faultModel", conf.get(section,"faultModel"))

    fp = open("/tmp/flip-"+uniqueID+".conf","w")
    fconf.write(fp)
    fp.close()

# Generate the gdb flip_value script
def genFlipScript(section):
    fp = open("flip_value.py","r")
    pscript = fp.read()
    fp.close()
    fp = open("/tmp/flip-"+uniqueID+".py", "w")
    fp.write(pscript.replace("<conf-location>","/tmp/flip-"+uniqueID+".conf"))
    fp.close()
    os.chmod("/tmp/flip-"+uniqueID+".py", 0775)

######################## Main ########################
def checkmd5():
    md5 = hashlib.md5(open("flip_value.py", 'rb').read()).hexdigest()
    if str(md5) != "260a2ce0736f2132a82053246e3272e7":
        print("Error: Checksum of flip_value.py does not match, please use the correct file",file=sys.stderr)
        print("It seems you are using a different version of the flip_value.py script")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="configFile", help='Configuration file', required=True)
    parser.add_argument('-i', '--iter', dest="iterations", help='How many times to repeat the programs in the configuration file', required=True, type=int)
    #parser.add_argument('-m', '--model', dest="model", help='Fault injection model; all will randomly choose one fault model', required=False, choices=('single', 'double', 'random', 'zeros', 'lsb', 'all'), default='all')
    
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error('Iterations must be greater than zero')
    #print ("args:",args)
    checkmd5()
    #sys.exit(0)
    
    # Start with a different seed every time to vary the random numbers generated
    random.seed() # the seed will be the current number of second since 01/01/70
    
    # Read the configuration file with data for all the apps that will be executed
    conf.read(args.configFile)
    
    
    numRounds = 0
    while numRounds < args.iterations:
        # Execute the fault injector for each one of the sections(apps) of the configuration file
        for sec in conf.sections():
            # Execute one fault injection for a specific app
            runGDBFaultInjection(sec)
        numRounds += 1
    os.system("rm -f /tmp/*"+uniqueID+"*")

if __name__ == "__main__":
    main()
