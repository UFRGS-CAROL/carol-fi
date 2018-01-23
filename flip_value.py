from __future__ import print_function
import gdb
import sys
import re

########################################################################
# Global vars
# Unfortunately gdb cannot see common_functions.py
HOME_DIR = "<home-location>"
sys.path.append(HOME_DIR)
import common_functions as cf  # All common functions will be at common_functions module

CONF_LOCATION = "<conf-location>"
VALID_BLOCK = None
VALID_THREAD = None
VALID_REGISTER = None
BITS_TO_FLIP =
FAULT_MODEL = "<fault-model>"

"""
function called when the execution is stopped
"""


def fault_injection(event):
    global VALID_BLOCK, VALID_THREAD, VALID_REGISTER
    global BITS_TO_FLIP, FAULT_MODEL
    
    threadFocus = gdb.execute("cuda kernel 0 block " + str(VALID_BLOCK[0]) + "," + str(VALID_BLOCK[1]) + "," + str(VALID_BLOCK[2]) +
                " thread " + str(VALID_THREAD[0]) + "," + str(VALID_THREAD[1]) + "," + str(VALID_THREAD[2]), to_string=True)
    
    generic_injector(VALID_REGISTER, BITS_TO_FLIP, FAULT_MODEL)

"""
Flip only a bit in a register content
"""


def flip_a_bit(bit_to_flip, reg_content):
    new_bit = '0' if reg_content[bit_to_flip] == 1 else '1'
    reg_content = reg_content[:bit_to_flip] + new_bit + reg_content[bit_to_flip - 1:]
    return reg_content

"""
Flip a bit or multiple based on a fault model
"""


def generic_injector(register, bits_to_flip, fault_model):
    # get register content
    reg_cmd = cf.execute_command("p/t $" + str(register))
    m = re.match("\$(\d+)[ ]*=[ ]*(\S+).*", reg_cmd)
    if m:
        reg_content = str(m.group(2))

        if fault_model == "single":
            # single bit flip
            reg_content = flip_a_bit(bits_to_flip[0], reg_content)

        elif fault_model == "multiple":
            # multiple bit flip
            for bit_to_flip in bits_to_flip:
                reg_content = flip_a_bit(bit_to_flip, reg_content)

        elif fault_model == "random":
            # random value is stored at bits_to_flip[0]
            reg_content = str(bits_to_flip[0])

        elif fault_model == "zero":
            reg_content = '0'

        # send the new value to gdb
        reg_cmd_flipped = cf.execute_command("set $" + str(register) + " = " + reg_content)

    else:
        raise NotImplementedError

    return reg_cmd_flipped


"""
Load temporary configuration file
"""


def load_conf_file()
    global CONF_LOCATION


########################################################################
# Initialize GDB to run the app
gdb.execute("set confirm off")
gdb.execute("set pagination off")



conf = cf.load_config_file()

try:
    gdbInitStrings = conf.get("DEFAULT", "gdbInitStrings")

    for initStr in gdbInitStrings.split(";"):
        gdb.execute(initStr)

except gdb.error as err:
    print ("initializing setup: " + str(err))





