#!/usr/bin/env python
import os
import re
from collections import Counter


fp = open("summary-carolfi.log", "r")
events = list()
for line in fp:
    m = re.match("(.*) - [Fault Injection Failed|Hang|SDC|NoOutputGenerated|Masked]",line)
    if m:
        line = line.strip()
        events.append(line)

print "FI attempts: ",len(events)
for k,v in Counter(events).most_common():
    print v,"\t",k
