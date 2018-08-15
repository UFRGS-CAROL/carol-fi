import os
import gdb

import common_parameters as cp  # All common parameters will be at common_parameters module
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
        if cp.DEBUG:
            print("ERROR ON EXIT HANDLER {}".format(str(err)))
        global_logging.exception(str("exit code: no exit code available "))


"""
Main function
"""


def main():
    global global_logging
    # Initialize GDB to run the app
    gdb.execute("set confirm off")
    gdb.execute("set pagination off")
    gdb.execute("set target-async off")
    gdb.execute("set non-stop off")

    # Connecting to a exit handler event
    gdb.events.exited.connect(exit_handler)

    # Get variables values from environment
    # First parse line
    # CAROL_FI_INFO = blockX,blockY,blockZ;threadX,threadY,threadZ;validRegister;bits_0,bits_1;fault_model;
    # injection_site;breakpoint;flip_log_file;debug;gdb_init_strings
    [block, thread, register, bits_to_flip, fault_model, breakpoint_location,
     flip_log_file, debug, gdb_init_strings, kludge, ignore_breaks] = str(os.environ['CAROL_FI_INFO']).split('|')

    # Logging
    global_logging = Logging(log_file=flip_log_file, debug=debug)
    global_logging.info("Starting flip_value script")
    try:
        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
            global_logging.info("initializing setup: " + str(init_str))

    except gdb.error as err:
        print("ERROR on initializing setup: " + str(err))

    # Set Breakpoint attributes to be used
    block = block.split(",")
    thread = thread.split(",")
    bits_to_flip = [int(i) for i in bits_to_flip.split(",")]
    fault_model = int(fault_model)
    # debug = bool(debug)

    # Place the first breakpoint, it is only to avoid
    # address memory error
    breakpoint_kernel_line = FaultInjectionBreakpoint(block=block, thread=thread, register=register,
                                                      bits_to_flip=bits_to_flip, fault_model=fault_model,
                                                      logging=global_logging, spec=breakpoint_location,
                                                      type=gdb.BP_BREAKPOINT, breaks_to_ignore=ignore_breaks)
    # ,  temporary=True)

    kludge_breakpoint = None
    if kludge != 'None':
        kludge_breakpoint = FaultInjectionBreakpoint(kludge=True, spec=kludge, type=gdb.BP_BREAKPOINT, temporary=True)

    # Start app execution
    gdb.execute("r")

    # Man, this is a quick fix
    if kludge_breakpoint:
        # kludge_breakpoint.delete()
        del kludge_breakpoint
        gdb.execute('c')

    # Delete the breakpoint
    # breakpoint_kernel_line.delete()
    del breakpoint_kernel_line

    # Continue execution until the next breakpoint
    gdb.execute("c")


# Call main execution
global_logging = None
main()
