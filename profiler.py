import os
import gdb
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will bet at common_parameters module
from classes.ProfilerBreakpoint import ProfilerBreakpoint

"""
Set temporary breakpoints.
After they are hit they are deleted
"""


def set_breakpoints(kernel_conf_string):
    # We are going to set
    # temporary breakpoints
    # to retrieve info of each
    # kernel
    kernel_profiler_objects = []
    breakpoints_list = kernel_conf_string.split(";")

    for kernel_line in breakpoints_list:
        # Just to make sure things like this: kernel.cu:52;<nothing here>
        if len(kernel_line) > 0:
            kernel_places = kernel_line.split("-")
            k_l = kernel_places[0]
            kernel_profiler_objects.append(ProfilerBreakpoint(spec=str(k_l), type=gdb.BP_BREAKPOINT, temporary=True,
                                                              kernel_name=kernel_places[0].split(":")[0],
                                                              kernel_line=kernel_places[0].split(":")[1],
                                                              kernel_end_line=kernel_places[1].split(":")[1]))

    return kernel_profiler_objects


"""
Main function
"""


def main():
    # Initialize GDB to run the app
    gdb.execute("set confirm off")
    gdb.execute("set pagination off")
    gdb.execute("set target-async off")
    gdb.execute("set non-stop off")

    gdb_init_strings, kernel_conf_string, time_profiler, kludge = str(os.environ["CAROL_FI_INFO"]).split("|")
    time_profiler = False if time_profiler == 'False' else True

    try:
        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
    except gdb.error as err:
        print ("initializing setup: " + str(err))

    # Profiler has two steps
    # First: getting kernel information
    # Run app for the first time
    kernel_profiler_objects = []

    if not time_profiler:
        kernel_profiler_objects = set_breakpoints(kernel_conf_string)

        if kludge != 'None':
            kernel_profiler_objects.append(
                ProfilerBreakpoint(spec=kludge, type=gdb.BP_BREAKPOINT, kludge=True, temporary=True))

    gdb.execute("r")

    i = 0
    try:
        while 'The program' not in gdb.execute('c', to_string=True):
            i += 1
    except Exception as err:
        if cp.DEBUG_PROFILER:
            print("CONTINUED {} times. Format {}".format(i, err))

    for profile_objects in kernel_profiler_objects:
        del profile_objects

    if cp.DEBUG_PROFILER:
        print('FINISH PROFILER')

main()
