import os
import gdb
from classes.BitFlip import BitFlip
from classes.FaultInjectionBreakpoint import FaultInjectionBreakpoint
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
        global global_logging, register, injection_mode, was_hit
        global bits_to_flip, fault_model, breakpoint_location, breakpoint_kernel_line

        # Just checking if
        global_logging.info("EVENT: {}".format(event.stop_signal))

        if was_hit is False:
            bit_lip = BitFlip(register=register, bits_to_flip=bits_to_flip, fault_model=fault_model,
                              logging=global_logging, injection_mode=injection_mode)
            bit_lip.single_event()

            global_logging.info("BREAKPOINT SET ON SIGNAL")
            was_hit = True
    except Exception as err:
        global_logging.exception("EVENT DIFFERENT FROM STOP SIGNAL: {}".format(str(err)))


"""
Main function
"""


def main():
    global global_logging, register, kludge_breakpoint, injection_mode
    global bits_to_flip, fault_model, breakpoint_location, kludge, breakpoint_kernel_line, was_hit

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
    [register, bits_to_flip, fault_model, breakpoint_location,
     flip_log_file, gdb_init_strings, kludge, injection_mode] = str(os.environ['CAROL_FI_INFO']).split('|')

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

    # if kludge != 'None':
    #     kludge_breakpoint = FaultInjectionBreakpoint(kludge=True, spec=kludge, type=gdb.BP_BREAKPOINT,
    #                                                  temporary=True)

    # Start app execution
    gdb.execute("r")

    i = 0
    try:
        while 'The program' not in gdb.execute('c', to_string=True):
            i += 1
    except Exception as err:
        global_logging.info("CONTINUED {} times".format(i))
        global_logging.exception("IGNORED CONTINUE ERROR: {}".format(str(err)))

    # Delete the breakpoint
    del breakpoint_kernel_line, kludge


# Call main execution
global_logging = None
register = None
bits_to_flip = None
fault_model = None
breakpoint_location = None
breakpoint_kernel_line = None
kludge = None
kludge_breakpoint = None
was_hit = False
injection_mode = None

main()
