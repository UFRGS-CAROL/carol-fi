# SDC checking diff
# Must compare all things here
# Any particular output comparison must be made here
# To be considered as an SDC or CRASH the
# DIFF_LOG and DIFF_ERR_LOG files must not be empty

# INJ_OUTPUT_PATH, INJ_ERR_PATH, GOLD_OUTPUT_PATH, GOLD_ERR_PATH
# are environment variables defined by the fault_injector.py

set -e

diff -B ${INJ_OUTPUT_PATH} ${GOLD_OUTPUT_PATH} > ${DIFF_LOG}

# Special comparisson like the following one can be done in this script
grep -q "Result = FAIL" ${INJ_OUTPUT_PATH} >> ${DIFF_LOG}

# diff stderr
diff -B ${INJ_ERR_PATH} ${GOLD_ERR_PATH} > ${DIFF_ERR_LOG}

# Must exit 0
exit 0
