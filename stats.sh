#!/bin/bash
echo "SDCs: "
grep -r -i SDC summary-carolfi.log |wc -l
echo "SDCs Detected: "
grep -r -i "SDC Detected" summary-carolfi.log |wc -l
echo "Hangs: "
grep -r -i HANG summary-carolfi.log |wc -l
echo "Masked: "
grep -r -i Masked summary-carolfi.log |wc -l
echo "Failed: "
grep -r -i Failed summary-carolfi.log |wc -l


