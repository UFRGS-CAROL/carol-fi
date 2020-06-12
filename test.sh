#!/bin/bash

set -e

#uncomment to a more verbose script
#set -x

FAULTS=10
CONFFILE=codes/matrixMul/matrixmul.conf


echo "Cleaning  the logs folder"
rm logs/* -rf

echo "Step 1 - Profiling the application for fault injection"
./app_profiler.py -c ${CONFFILE}


echo "Step 2 - Running ${FAULTS} on ${CONFFILE}"
./fault_injector.py -i ${FAULTS} -c ${CONFFILE}

echo "Fault injection finished"

exit 0
