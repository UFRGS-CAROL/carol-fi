import gdb
from classes.BitFlip import BitFlip
from classes.Logging import Logging

"""
Handler attached to exit event
"""


def exit_handler(event):
    global global_logging
    global_logging.info(str("event type: exit"))
    try:
        global_logging.info("exit code: {}".format(str(event.exit_code)))
    except Exception as err:
        err_str = "ERROR: {}".format(str(err))
        global_logging.exception(err_str)


"""
Handler that will put a breakpoint on the kernel after
signal
"""


def set_event(event):
    try:
        # Accessing global vars
        global global_logging, was_hit, bit_lip

        # Just checking if it was hit
        if bit_lip.fault_injected is False:
            bit_lip.single_event()
            global_logging.info("BIT FLIP SET ON SIGNAL {}".format(event.stop_signal))

    except Exception as err:
        global_logging.exception("EVENT DIFFERENT FROM STOP SIGNAL: {}".format(str(err)))


"""
Main function
"""


def main():
    global global_logging, register, injection_mode, bits_to_flip, fault_model, was_hit, bit_lip, arg0

    was_hit = False

    # Initialize GDB to run the app
    gdb.execute("set confirm off")
    gdb.execute("set pagination off")
    gdb.execute("set target-async off")
    gdb.execute("set non-stop off")

    # Connecting to a exit handler event
    gdb.events.exited.connect(exit_handler)

    # Connecting to a stop signal event
    gdb.events.stop.connect(set_event)

    # Get variables values from environment
    # First parse line
    [bits_to_flip, fault_model, flip_log_file,
     gdb_init_strings, injection_mode] = arg0.split('|')

    # Logging
    global_logging = Logging(log_file=flip_log_file)
    global_logging.info("Starting flip_value script")
    try:
        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
            global_logging.info("initializing setup: " + str(init_str))

    except gdb.error as err:
        global_logging.exception("ERROR on initializing setup: {}".format(str(err)))

    # Set Breakpoint attributes to be use
    bits_to_flip = [i for i in bits_to_flip.split(",")]
    fault_model = int(fault_model)
    bit_lip = BitFlip(bits_to_flip=bits_to_flip, fault_model=fault_model,
                      logging=global_logging, injection_mode=injection_mode)

    # Start app execution
    gdb.execute("r")

    i = 0
    try:
        while 'The program' not in gdb.execute('c', to_string=True):
            i += 1
    except Exception as err:
        global_logging.info("CONTINUED {} times".format(i))
        err_str = str(err).rstrip()
        global_logging.exception("IGNORED CONTINUE ERROR: {}".format(err_str))

        # Make sure that it is going to finish
        if 'Failed' in err_str:
            gdb.execute('quit')
            global_logging.exception("QUIT REQUIRED")


# Call main execution
global_logging = None
register = None
bits_to_flip = None
fault_model = None
was_hit = False
injection_mode = None
bit_lip = None

main()
