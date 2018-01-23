from __future__ import print_function
import gdb
import sys

sys.path.append() # I have to fix it
import common_functions as cf # All common functions will be at common_functions module

HOME_DIR = "<home-location>"
CONF_LOCATION = "<conf-location>"

VALID_BLOCK = None
VALID_THREAD = None
VALID_REGISTER = None

"""
function called when the execution is stopped
"""


def fault_injection(event):
    global VALID_BLOCK, VALID_THREAD, VALID_REGISTER
    
    threadFocus = gdb.execute("cuda kernel 0 block " + str(VALID_BLOCK[0]) + "," + str(VALID_BLOCK[1]) + "," + str(VALID_BLOCK[2]) +
                " thread " + str(VALID_THREAD[0]) + "," + str(VALID_THREAD[1]) + "," + str(VALID_THREAD[2]), to_string=True)
    
    generic_injector(VALID_REGISTER, "bit_flip")


def generic_injector(register, faultModel):
    if faultModel == "bit_flip":
        pass
    elif faultModel == "multiple_bitflip":
        pass
    elif faultModel == "random_value":
        pass
    elif faultModel == "zero_value":
        pass









########################################################################
# Initialize GDB to run the app
gdb.execute("set confirm off")
gdb.execute("set pagination off")



conf = cf.load_config_file()

try:
    gdbInitStrings = conf.get("DEFAULT", "gdbInitStrings")

    for initStr in gdbInitStrings.split(";"):
        print initStr
        gdb.execute(initStr)

except gdb.error as err:
    print "initializing setup: " + str(err)





