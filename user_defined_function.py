"""
[THIS FUNCTION CAN BE EDITED IF DESIRED]
User defined function
this function must return an empty or not.
The string will be appended in the last column of summary CSV file
the column will have  'user_defined' as header
if there isn't a return value the column will be None,
otherwise it will contain the returned values for each injection
"""
import re


def user_defined_function(injection_output_path):
    # This is a temporary example for carol-fi-codes suite
    # it will search for a LOGFILENAME int the benchmark output if it finds
    # then the desired pattern will be returned

    with open(injection_output_path, "r") as fp:
        for line in fp.readlines():
            m = re.match(r'LOGFILENAME:.*/(\S+).*', line)
            if m:
                return m.group(1)
