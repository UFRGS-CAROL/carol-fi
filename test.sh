#!/bin/bash

set -e

#uncomment to a more verbose script
#set -x

FAULTS=10
CONFFILE=carol-fi-codes/gemm_tensorcores/single_mxm_no_tensor.conf

echo "Step 1 - Profiling the application for fault injection"
./app_profiler.py -c ${CONFFILE}


echo "Step 2 - Running ${FAULTS} on ${CONFFILE}"
./fault_injector.py -i ${FAULTS} -c ${CONFFILE}

echo "Fault injection finished"

exit 0
