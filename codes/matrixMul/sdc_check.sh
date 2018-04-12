# Remove GDB specific outputs from gold and inj output
CLEAN_GOLD=/tmp/clean_carol_fi_gold.txt
CLEAN_INJ_OUTPUT=/tmp/clean_carol_fi_inj.txt
TMP=/tmp/carol_buff.txt

cat ${GOLD_OUTPUT_PATH} > ${CLEAN_GOLD}
cat ${INJ_OUTPUT_PATH} > ${CLEAN_INJ_OUTPUT}

for i in '/Breakpoint/,+2d' '/\[New/d' '/\[Thread/d' '/\[Switching/d' '/\[Inferior/d';
do
    for j in ${CLEAN_INJ_OUTPUT} ${CLEAN_GOLD};
    do
        sed -e $i $j > ${TMP}
        cat ${TMP} > $j
    done
done

# SDC checking diff
# Must compare all things here
# Copied from SASSIFI

diff -B ${CLEAN_GOLD} ${CLEAN_INJ_OUTPUT} > ${DIFF_LOG}

if grep -q "Result = FAIL" ${CLEAN_INJ_OUTPUT}; then
    echo "SDC" >> ${DIFF_LOG}
fi

rm -f ${CLEAN_GOLD} ${CLEAN_INJ_OUTPUT} ${TMP}