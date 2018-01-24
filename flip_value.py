from __future__ import print_function
import gdb
import sys
import re

########################################################################
# Global vars
# Unfortunately gdb cannot see common_functions.py
home_dir = "<home-location>"
sys.path.append(home_dir)
import common_functions as cf  # All common functions will be at common_functions module


# global vars loaded from config file
conf_location = "<conf-location>"
valid_block = None
valid_thread = None
valid_register = None
bits_to_flip = None
fault_model = None
injection_site = None

# version
version = 1.0

"""
function called when the execution is stopped
"""


def fault_injection(event):
    global valid_block, valid_thread, valid_register
    global bits_to_flip, fault_model

    logging.debug("Trying Fault Injection")

    thread_focus = gdb.execute(
        "cuda kernel 0 block " + str(valid_block[0]) + "," + str(valid_block[1]) + "," + str(valid_block[2]) +
        " thread " + str(valid_thread[0]) + "," + str(valid_thread[1]) + "," + str(valid_thread[2]), to_string=True)

    # Thread focus return information
    for i in thread_focus:
        logging.info(i)

    generic_injector(valid_register, bits_to_flip, fault_model)


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

    # Logging info result extracted from register
    logging.info("reg old value: " + str(reg_cmd[0]))

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

    logging.info("reg old value: " + str(reg_content))
    logging.info("reg new value: " + str(reg_cmd_flipped))

    return reg_cmd_flipped


def exit_handler(event):
    logging.info(str("event type: exit"))
    try:
        logging.info(str("exit code: %d" % (event.exit_code)))
    except:
        logging.exception(str("exit code: no exit code available"))


def abnormal_stop(event):
    logging.debug("Abnormal stop, signal:" + str(event.stop_signal))


########################################################################
# Initialize GDB to run the app
gdb.execute("set confirm off")
gdb.execute("set pagination off")

# Connecting to a exit handler event
gdb.events.exited.connect(exit_handler)

# Setting conf and logging
conf = cf.load_config_file(conf_location)
logging = cf.Logging(conf)

logging.info("Starting flip_value script\nversion: " + str(version))

try:
    gdbInitStrings = conf.get("DEFAULT", "gdbInitStrings")

    for init_str in gdbInitStrings.split(";"):
        gdb.execute(init_str)
        logging.info("initializing setup: " + str(init_str))

except gdb.error as err:
    print("initializing setup: " + str(err))

# Define which function to call when the execution stops, e.g. when a breakpoint is hit
# or a interruption signal is received
gdb.events.stop.connect(fault_injection)

# Place the injection breakpoint
breakpoing_info = cf.execute_command("break " + str(injection_site))

logging.debug("breakpoint: " + str(breakpoing_info))

# Start app execution
gdb.execute("r")
