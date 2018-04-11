# Remove GDB specific outputs from gold and inj output
CLEAN_GOLD=/tmp/clean_carol_fi_gold.txt
TMP=/tmp/carol_buff.txt

for i in '/Breakpoint/,+2d' '/\[New Thread/d' '/\[Thread/d' '/\[Switching/d' '/\[Inferior/d';
do
    for j in ${INJ_OUTPUT_PATH} ${GOLD_OUTPUT_PATH};
    do
        sed -e $i $j > ${TMP}
        cat ${TMP} > $j
    done
done

# Remove breakpoint and folowing line
#sed -e '/Breakpoint/,+2d' ${GOLD_OUTPUT_PATH} > ${CLEAN_GOLD}
#
#cat ${CLEAN_GOLD} > ${TMP}
#sed '/\[New Thread/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}
#cat ${CLEAN_GOLD} > ${TMP}
#sed '/\[Thread/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}
#sed '/\[Switching/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}
#sed '/\[Inferior/d' ${CLEAN_GOLD} > ${CLEAN_GOLD}
#
## Remove inj output
#CLEAN_INJ_OUTPUT=/tmp/clean_carol_fi_inj.txt
## Remove breakpoint and folowing line
#sed -e '/Breakpoint/,+2d' ${INJ_OUTPUT_PATH} > ${CLEAN_INJ_OUTPUT}
#sed '/\[New Thread/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}
#sed '/\[Thread/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}
#sed '/\[Switching/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}
#sed '/\[Inferior/d' ${CLEAN_INJ_OUTPUT} > ${CLEAN_INJ_OUTPUT}

# SDC checking diff
# Must compare all things here
# Copied from SASSIFI
# APP, GOLD_OUTPUT_PATH and INJ_OUTPUT_PATH are set on python script
#diff ${CLEAN_GOLD} ${CLEAN_INJ_OUTPUT} > ${DIFF_LOG}

#rm -f /tmp/${CLEAN_GOLD} /tmp/${CLEAN_INJ_OUTPUT}