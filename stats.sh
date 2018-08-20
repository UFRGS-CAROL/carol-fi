#!/bin/bash
printf "SDCs: "
grep -r -i SDC summary-carolfi.log |wc -l
printf "Crashes: "
grep -r -i CRASH summary-carolfi.log |wc -l
printf "Hangs: "
grep -r -i HANG summary-carolfi.log |wc -l
printf "Masked: "
grep -r -i Masked summary-carolfi.log |wc -l
printf "Failed: "
grep -r -i Failed summary-carolfi.log |wc -l


