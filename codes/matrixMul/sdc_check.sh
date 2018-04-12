# Remove GDB specific outputs from gold and inj output
CLEAN_GOLD=/tmp/clean_carol_fi_gold.txt
CLEAN_INJ_OUTPUT=/tmp/clean_carol_fi_inj.txt
TMP=/tmp/carol_buff.txt

cat ${GOLD_OUTPUT_PATH} > ${CLEAN_GOLD}
cat ${INJ_OUTPUT_PATH} > ${CLEAN_INJ_OUTPUT}

for i in '/Breakpoint/,+2d' '/\[New/d' '/\[Thread/d' '/\[Switching/d' '/\[Inferior/d' '/Performance=/d' '/Using host libthread_db/d';
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
grep -q "Result = FAIL" ${CLEAN_INJ_OUTPUT} >> ${DIFF_LOG}

# diff stderr
diff -B ${INJ_ERR_PATH} ${GOLD_ERR_PATH} > ${DIFF_ERR_LOG}

if ! grep -q 'exited normally\]' ${INJ_OUTPUT_PATH} ;
then
    echo "PROGRAM_DID_EXITED_NORMALLY" >> ${DIFF_ERR_LOG}
fi

rm -f ${CLEAN_GOLD} ${CLEAN_INJ_OUTPUT} ${TMP}