#!/usr/bin/env bash

# Remove GDB specific outputs from gold and inj output
CLEAN_GOLD=/tmp/clean_carol_fi_gold.txt

sed '/\[New Thread/d' ${GOLD_OUTPUT_PATH} > ${CLEAN_GOLD}
sed '/\[Thread/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}
sed '/\[Switching/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}
sed '/Breakpoint/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}

# Remove inj output
CLEAN_INJ_OUTPUT=/tmp/clean_carol_fi_inj.txt
sed '/\[New Thread/d' ${INJ_OUTPUT_PATH} > ${CLEAN_INJ_OUTPUT}
sed '/\[Thread/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}
sed '/\[Switching/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}
sed '/Breakpoint/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}


# SDC checking diff
# Must compare all things here
# Copied from SASSIFI
# APP, GOLD_OUTPUT_PATH and INJ_OUTPUT_PATH are set on python script
diff ${CLEAN_GOLD} ${CLEAN_INJ_OUTPUT} > /tmp/diff_${APP}.log
rm -f /tmp/${CLEAN_GOLD} /tmp/${CLEAN_INJ_OUTPUT}