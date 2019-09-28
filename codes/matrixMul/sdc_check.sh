# SDC checking diff
# Must compare all things here
# Any special output comparrison must be done here
# To be consider as an SDC or CRASH the
# DIFF_LOG and DIFF_ERR_LOG files must not be empty


diff -B ${GOLD_OUTPUT_PATH} ${INJ_OUTPUT_PATH} > ${DIFF_LOG}
grep -q "Result = FAIL" ${INJ_OUTPUT_PATH} >> ${DIFF_LOG}

# diff stderr
diff -B ${INJ_ERR_PATH} ${GOLD_ERR_PATH} > ${DIFF_ERR_LOG}

rm -f ${CLEAN_GOLD} ${CLEAN_INJ_OUTPUT} ${TMP}
