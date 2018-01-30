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

"""
function called when the execution is stopped
"""


def fault_injection(event):
    global valid_block, valid_thread, valid_register
    global bits_to_flip, fault_model, fi, logging

    # This if avoid the creation of another event connection
    # for some reason gdb cannot breakpoint addresses before
    # a normal breakpoint is hit
    if fi:

        logging.debug("Trying Fault Injection")

        try:
            change_focus_cmd = "cuda kernel 0 block {0},{1},{2} thread {3},{4},{5}".format(str(valid_block[0]),
                                                                                           str(valid_block[1]),
                                                                                           str(valid_block[2]),
                                                                                           str(valid_thread[0]),
                                                                                           str(valid_thread[1]),
                                                                                           str(valid_thread[2]))
            thread_focus = gdb.execute(change_focus_cmd, to_string=True)

            # Thread focus return information
            for i in thread_focus:
                logging.info(i)

            # Do the fault injection magic
            generic_injector(valid_register, bits_to_flip, fault_model)

        except Exception as err:
            logging.exception("fault_injection_python_exception: " + str(err))
    else:
        fi = True


"""
Flip only a bit in a register content
"""


def flip_a_bit(bit_to_flip, reg_content):
    # Make sure that binary value will have max size register
    reg_content = str('0' * (cf.MAX_SIZE_REGISTER - len(reg_content))) + reg_content
    new_bit = '0' if reg_content[bit_to_flip] == 1 else '1'
    reg_content = reg_content[:bit_to_flip] + new_bit + reg_content[bit_to_flip - 1:]
    return reg_content


"""
Flip a bit or multiple bits based on a fault model
"""


def generic_injector(valid_register, bits_to_flip, fault_model):
    # get register content
    reg_cmd = cf.execute_command(gdb, "p/t $" + str(valid_register))

    # Logging info result extracted from register
    logging.info("reg old value: " + str(reg_cmd[0]))
    m = re.match("\$(\d+)[ ]*=[ ]*(\S+).*", reg_cmd[0])

    if m:
        reg_content = str(m.group(2))
        print("REG OLD VALUE", reg_content)
        # Single bit flip
        if fault_model == 0:
            # single bit flip
            reg_content = flip_a_bit(bits_to_flip[0], reg_content)

        # Double bit flip
        elif fault_model == 1:
            # multiple bit flip
            for bit_to_flip in bits_to_flip:
                reg_content = flip_a_bit(bit_to_flip, reg_content)

        # Random value
        elif fault_model == 2:
            # random value is stored at bits_to_flip[0]
            reg_content = str(bits_to_flip[0])

        # Zero values
        elif fault_model == 3:
            reg_content = '0'

        # Least significant bits, not implemented
        elif fault_model == 4:
            raise NotImplementedError

        print("REG NEW VALUE", reg_content)
        reg_content = str(int(reg_content, 2))
        # send the new value to gdb
        reg_cmd_flipped = cf.execute_command(gdb, "set $" + str(valid_register) + " = " + reg_content)

    else:
        raise NotImplementedError

    logging.info("reg new value: " + str(reg_content))
    logging.info("flip command return: " + str(reg_cmd_flipped))

    return reg_cmd_flipped


def exit_handler(event):
    logging.info(str("event type: exit"))
    try:
        logging.info(str("exit code: %d" % event.exit_code))
    except:
        logging.exception(str("exit code: no exit code available"))


def abnormal_stop(event):
    logging.debug("Abnormal stop, signal:" + str(event.stop_signal))


def main():
    global valid_block, valid_thread, valid_register, bits_to_flip, fault_model, logging

    # Initialize GDB to run the app
    gdb.execute("set confirm off")
    gdb.execute("set pagination off")

    # Connecting to a exit handler event
    gdb.events.exited.connect(exit_handler)

    # Setting conf and loading global vars
    conf = cf.load_config_file(conf_location)

    # Get variables values from config file
    valid_block = conf.get("DEFAULT", "validBlock").split(";")
    valid_thread = conf.get("DEFAULT", "validThread").split(";")
    valid_register = conf.get("DEFAULT", "validRegister")
    bits_to_flip = [int(i) for i in conf.get("DEFAULT", "bitsToFlip").split(";")]
    fault_model = int(conf.get("DEFAULT", "faultModel"))
    injection_site = conf.get("DEFAULT", "injectionSite")
    breakpoint_location = conf.get("DEFAULT", "breakpointLocation")

    # Logging
    logging = cf.Logging(log_file=conf.get("DEFAULT", "flipLogFile"), debug=conf.get("DEFAULT", "debug"))
    logging.info("Starting flip_value script\n")
    try:
        gdb_init_strings = conf.get("DEFAULT", "gdbInitStrings")

        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
            logging.info("initializing setup: " + str(init_str))

    except gdb.error as err:
        print("initializing setup: " + str(err))

    # Place the first breakpoint, it is only to avoid
    # address memory error
    breakpoint_kernel_line = gdb.Breakpoint(spec=breakpoint_location, type=gdb.BP_BREAKPOINT)

    # Define which function to call when the execution stops, e.g. when a breakpoint is hit
    # or a interruption signal is received
    gdb.events.stop.connect(fault_injection)

    # Start app execution
    gdb.execute("r")
    breakpoint_kernel_line.delete()
    breakpoint_kernel_address = gdb.Breakpoint(spec="*" + injection_site, type=gdb.BP_BREAKPOINT)

    # Continue execution untill the next breakpoint
    gdb.execute("c")
    breakpoint_kernel_address.delete()


# Set global vars
valid_block = None
valid_thread = None
valid_register = None
bits_to_flip = None
fault_model = None
logging = None
fi = False

# Call main execution
main()
