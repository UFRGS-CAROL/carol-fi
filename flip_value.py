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
        err_str = "ERROR: {}".format(str(err))
        if cp.DEBUG:
            print(err_str)
        global_logging.exception(err_str)


"""
Handler that will put a breakpoint on the kernel after
signal
"""


def place_breakpoint():
    global breakpoint_kernel_line, kludge_breakpoint, injection_mode

    # Check if many breakpoints are going to be set
    # if not was_hit:
    # was_hit = True

    # try:
    # Place the first breakpoint, it is only to avoid
    # address memory error
    # breakpoint_kernel_line = FaultInjectionBreakpoint(block=block, thread=thread, register=register,
    #                                                   bits_to_flip=bits_to_flip, fault_model=fault_model,
    #                                                   logging=global_logging, spec=breakpoint_location,
    #                                                   type=gdb.BP_BREAKPOINT,
    #                                                   injection_mode=injection_mode)

    if kludge != 'None':
        kludge_breakpoint = FaultInjectionBreakpoint(kludge=True, spec=kludge, type=gdb.BP_BREAKPOINT,
                                                     temporary=True)
        # except Exception as err:
        #     if cp.DEBUG:
        #         print("ERROR ON PLACE_BREAKPOINT HANDLER {}".format(str(err)))


def set_event(event):
    global global_logging, block, thread, register, injection_mode
    global bits_to_flip, fault_model, breakpoint_location, breakpoint_kernel_line, was_hit

    try:
         print("FOI", event.stop_signal)

         if not was_hit:
             # breakpoint_kernel_line.set_is_ready_to_inject(True)
             breakpoint_kernel_line = FaultInjectionBreakpoint(block=block, thread=thread, register=register,
                                                               bits_to_flip=bits_to_flip, fault_model=fault_model,
                                                               logging=global_logging, spec=breakpoint_location,
                                                               type=gdb.BP_BREAKPOINT, temporary=True,
                                                               injection_mode=injection_mode)
             was_hit = True
    except:
        pass


"""
Main function
"""


def main():
    global global_logging, block, thread, register, kludge_breakpoint, injection_mode
    global bits_to_flip, fault_model, breakpoint_location, kludge, breakpoint_kernel_line, was_hit

    was_hit = False

    # Initialize GDB to run the app
    gdb.execute("set confirm off")
    gdb.execute("set pagination off")
    gdb.execute("set target-async off")
    gdb.execute("set non-stop off")

    # Connecting to a exit handler event
    # gdb.events.exited.connect(exit_handler)

    # Connecting to a stop signal event
    gdb.events.stop.connect(set_event)

    # Get variables values from environment
    # First parse line
    [block, thread, register, bits_to_flip, fault_model, breakpoint_location,
     flip_log_file, gdb_init_strings, kludge, injection_mode] = str(os.environ['CAROL_FI_INFO']).split('|')

    # Logging
    global_logging = Logging(log_file=flip_log_file)
    global_logging.info("Starting flip_value script")
    try:
        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
            global_logging.info("initializing setup: " + str(init_str))

    except gdb.error as err:
        print("ERROR on initializing setup: " + str(err))

    # Set Breakpoint attributes to be use
    print("Passou 1")
    block = block.split(",")
    thread = thread.split(",")
    bits_to_flip = [int(i) for i in bits_to_flip.split(",")]
    fault_model = int(fault_model)
    print("Passou 2")
    place_breakpoint()
    print("Passou 3")

    # breakpoint_kernel_line.ignore_count = 10000

    # Start app execution
    gdb.execute("r")
    print("Passou 4")

    while 'The program' not in gdb.execute('c', to_string=True):
        pass

    # Delete the breakpoint
    del breakpoint_kernel_line, kludge


# Call main execution
global_logging = None
block = None
thread = None
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
