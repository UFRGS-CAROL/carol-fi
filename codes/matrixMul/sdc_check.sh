
# SDC checking diff
# Must compare all things here
# Copied from SASSIFI
# APP, GOLD_OUTPUT_PATH and INJ_OUTPUT_PATH are set on python script
diff ${GOLD_OUTPUT_PATH} ${INJ_OUTPUT_PATH} > /tmp/diff_${APP}.log
