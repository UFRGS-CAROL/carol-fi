# Remove GDB specific outputs from gold and inj output
CLEAN_GOLD=/tmp/clean_carol_fi_gold.txt

# Remove breakpoint and folowing line
sed -e '/Breakpoint/,+2d' ${GOLD_OUTPUT_PATH} > ${CLEAN_GOLD}

sed '/\[New Thread/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}
sed '/\[Thread/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}
sed '/\[Switching/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}
sed '/\[Inferior/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}

# Remove inj output
CLEAN_INJ_OUTPUT=/tmp/clean_carol_fi_inj.txt
# Remove breakpoint and folowing line
sed -e '/Breakpoint/,+2d' ${INJ_OUTPUT_PATH} > ${CLEAN_INJ_OUTPUT}
sed '/\[New Thread/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}
sed '/\[Thread/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}
sed '/\[Switching/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}
sed '/\[Inferior/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}

# SDC checking diff
# Must compare all things here
# Copied from SASSIFI
# APP, GOLD_OUTPUT_PATH and INJ_OUTPUT_PATH are set on python script
diff ${CLEAN_GOLD} ${CLEAN_INJ_OUTPUT} > ${DIFF_LOG}

#rm -f /tmp/${CLEAN_GOLD} /tmp/${CLEAN_INJ_OUTPUT}