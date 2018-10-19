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
from curses import wrapper

if sys.version_info >= (3,0):
    import configparser # python 3
else:
    import ConfigParser # python 2

try:
    from subprocess import DEVNULL # py3k
except ImportError:
    import os
    DEVNULL = open(os.devnull, 'wb')

### Script version
VERSION = "1.1"

### Global variables
uniqueID = str(uuid.uuid4())
gdbFIlogFile = "/tmp/carolfi-"+uniqueID+".log"
summFIlogFile = "summary-carolfi.log"
if sys.version_info >= (3,0):
    conf = configparser.ConfigParser()
else:
    conf = ConfigParser.ConfigParser()


# Counters to keep track of fault effects so we can show them to the user
faults = {"masked": 0, "sdc": 0, "crash": 0, "hang": 0, "noOutput": 0, "failed": 0}

status = ""

# The number of threads that will stop the target program at a random time (each stop is a fault injection tentative)
# Fault injections tentatives are not always successful, that is why we need to do it more than once. 
# However, only one fault can be injected
numThreadsFI=3

# How many times each thread (numTHreadsFI) will try to stop (interrupt) the target program
seqSignals=5

class logging:
    @staticmethod
    def info(msg):
        fp = open(gdbFIlogFile, "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[INFO -- "+d+"]\n"+msg+"\n")
        fp.close()

    @staticmethod
    def error(msg):
        fp = open(gdbFIlogFile, "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[ERROR -- "+d+"]\n"+msg+"\n")
        fp.close()

    @staticmethod
    def debug(msg):
        if conf.getboolean("DEFAULT","debug"):
            fp = open(gdbFIlogFile, "a")
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
        # Sleep for a random time
        waitTime = random.uniform(init,end)
        time.sleep(waitTime)
        # Send a series of signal to make sure gdb will flip a value in one of the interupt signals
        logging.info("sending "+str(seqSignals)+" signals using command: '"+signalCmd+"' after "+str(waitTime)+"s")
        for i in range(0,seqSignals):
            subprocess.call(signalCmd, shell=True, stdout=DEVNULL, stderr=subprocess.STDOUT)
            time.sleep(0.01)

# Start the gdb script
class runGDB (threading.Thread):
    def __init__(self, section):
        threading.Thread.__init__(self)
        self.section = section
    def run(self):
        startCmd = conf.get(self.section,"gdbExecName")+" --nh --nx -q -batch-silent --return-child-result -x "+"/tmp/flip-"+uniqueID+".py > /dev/null 2> /dev/null &"
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
        subprocess.call(k, shell=True, stdout=DEVNULL, stderr=subprocess.STDOUT)


    return isHang

def checkIsOutput(section):
    outputFile = conf.get(section,"outputFile")
    return os.path.isfile(outputFile)

# Copy the logs and output(if sdc occured) to a selected folder
def saveOutput(section, isHang):
    outputFile = conf.get(section,"outputFile")
    flipLogFile = "/tmp/carolfi-flipvalue-"+uniqueID+".log"


    fiSucc = False
    isCrash = False
    isSDC = False
    if os.path.isfile(flipLogFile):
        fp = open(flipLogFile, "r")
        content = fp.read()
        if re.search("Fault Injection Successful",content):
            fiSucc = True
        if not re.search("exit code: 0",content):
            isCrash = True
        fp.close()

    isOutput = checkIsOutput(section)

    dt = datetime.datetime.fromtimestamp(time.time())
    ymd = dt.strftime('%Y_%m_%d')
    timestamp = dt.strftime('%Y_%m_%d_%H_%M_%S_%f')
    uniqueFolder = uniqueID+"-"+timestamp
    dirDT = os.path.join(ymd,uniqueFolder)
    if not fiSucc:
        cpDir = os.path.join('logs',section,'failed-injection',dirDT)
        logging.summary(section+" - Fault Injection Failed")
        faults["failed"] += 1
    elif isHang:
        cpDir = os.path.join('logs',section,'hangs',dirDT)
        logging.summary(section+" - Hang")
        faults["hang"] += 1
    elif isCrash:
        cpDir = os.path.join('logs',section,'crashes',dirDT)
        logging.summary(section+" - Crash")
        faults["crash"] += 1
    elif not isOutput:
        cpDir = os.path.join('logs',section,'noOutputGenerated',dirDT)
        logging.summary(section+" - NoOutputGenerated")
        faults["noOutput"] += 1
    else:
        # Check output files for SDCs
        isSDC = checkSDCs(section)
        if isSDC:
            cpDir = os.path.join('logs',section,'sdcs',dirDT)
            logging.summary(section+" - SDC")
            faults["sdc"] += 1
        else:
            cpDir = os.path.join('logs',section,'masked',dirDT)
            logging.summary(section+" - Masked")
            faults["masked"] += 1

    if not os.path.isdir(cpDir):
        os.makedirs(cpDir)

    shutil.move(flipLogFile, cpDir)
    shutil.move(gdbFIlogFile, cpDir)
    if isSDC:
        shutil.move(outputFile, cpDir)


def preExecution(section):
    try:
        script = conf.get(section,"preExecScript")
        if script != "":
            subprocess.call(script, shell=True, stdout=DEVNULL, stderr=subprocess.STDOUT)
        return
    except:
        return

def posExecution(section):
    try:
        script = conf.get(section,"posExecScript")
        if script != "":
            subprocess.call(script, shell=True, stdout=DEVNULL, stderr=subprocess.STDOUT)
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
    isHang = False

    logging.info("Starting GDB script")
    init = conf.getfloat(section,"initSignal")
    end = conf.getfloat(section,"endSignal")
    logging.info("initSignal:"+str(init))
    logging.info("endSignal:"+str(end))
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

    # Copy output files to a folder
    saveOutput(section, isHang)

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
    if str(md5) != "9b9557b511ff36d53666c3cd062c6f52":
        print("Error: Checksum of flip_value.py does not match, please use the correct file",file=sys.stderr)
        print("It seems you are using a different version of the flip_value.py script")
        sys.exit(0)

def updateStatus(args, numRounds, avgRoundTime, sec, faults):
    global status
    status = "\tIteration "+str(numRounds)+"/"+str(args.iterations)+"\n\n"
    status += "\tIteration average time: "+str(avgRoundTime)+"s\n\n"
    status += "\tExecuting section: "+str(sec)+"\n\n"
    status += "\tFault Effects: \n"
    for k, v in faults.items():
        status += "\t\t"+str(k)+": "+str(v)+"\n"


def printStatusCurses(stdscr):
    try:
        stdscr.clear()
        stdscr.addstr(0, 0, status)
        #stdscr.addstr(0, 0, "\tIteration "+str(numRounds)+"/"+str(args.iterations)+"\n\n")
        #stdscr.addstr("\tIteration average time: "+str(avgRoundTime)+"s\n\n")
        #stdscr.addstr("\tExecuting section: "+str(sec)+"\n\n")
        #stdscr.addstr("\tFault Effects: \n")
        #for k, v in faults.items():
        #    stdscr.addstr("\t\t"+str(k)+": "+str(v)+"\n")
        stdscr.refresh()
    except:
        stdscr.clear()
        stdscr.addstr(0, 0, "Screen too small, resize!")
        stdscr.refresh()

def main(stdscr):
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="configFile", help='Configuration file', required=True)
    parser.add_argument('-i', '--iter', dest="iterations", help='How many times to repeat the programs in the configuration file', required=True, type=int)
    
    args = parser.parse_args()
    if args.iterations < 1:
        parser.error('Iterations must be greater than zero')
    
    checkmd5()
    
    # Start with a different seed every time to vary the random numbers generated
    random.seed() # the seed will be the current number of second since 01/01/70
    
    # Read the configuration file with data for all the apps that will be executed
    conf.read(args.configFile)
    
    
    try:

        avgRoundTime = 0
        sumRoundTime = 0
        numRounds = 0
        while numRounds < args.iterations:
            start = int(time.time())
            # Execute the fault injector for each one of the sections(apps) of the configuration file
            for sec in conf.sections():
                # Print status information
                updateStatus(args, numRounds, avgRoundTime, sec, faults)
                printStatusCurses(stdscr)
                # Execute one fault injection for a specific app
                runGDBFaultInjection(sec)
            sumRoundTime += (int(time.time()) - start) # in seconds
            numRounds += 1
            avgRoundTime = sumRoundTime / numRounds
        updateStatus(args, numRounds, avgRoundTime, sec, faults)
        subprocess.call("rm -f /tmp/*"+uniqueID+"*", shell=True, stdout=DEVNULL, stderr=subprocess.STDOUT)

    except KeyboardInterrupt:  # Ctrl+c
        print(status)
        print ("\n\tKeyboardInterrupt detected, exiting gracefully!( at least trying :) )")
        # Get all kill commands from all sections from the config file to make sure there is no spawn process running
        for sec in conf.sections():
            killStrs = conf.get(sec,"killStrs")
            for k in killStrs.split(";"):
                subprocess.call(k, shell=True, stdout=DEVNULL, stderr=subprocess.STDOUT)
        # Clean tmp files
        subprocess.call("rm -f /tmp/*"+uniqueID+"*", shell=True, stdout=DEVNULL, stderr=subprocess.STDOUT)
        sys.exit(1)


if __name__ == "__main__":
    #main()
    wrapper(main) # ncurses
    print (status)

