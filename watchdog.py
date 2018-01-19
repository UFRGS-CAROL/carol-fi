#!/usr/bin/python

from __future__ import print_function
import os
import time
import sys

timestampFile = "summary-carolfi.log"
timestampMaxDiff=60*2 # in seconds

def run():
    os.system("killall -9 fault_injector.py")
    os.system("killall -9 gdb")
    os.system("./fault_injector.py -c codes/lavamd/lavamd.conf.KNL -i 9000 &")


print("running ...")
run()
time.sleep(timestampMaxDiff)
while True:
    timestamp = int(os.path.getmtime(timestampFile))
    now = int(time.time())
    timestampDiff = now - timestamp
    if timestampDiff > timestampMaxDiff:
        print ("timestamp > than expected")
        run()
    else:
        print ("timestamp OK")

    time.sleep(timestampMaxDiff)

