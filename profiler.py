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
    kernel_info_list = []
    breakpoints_list = kernel_conf_string.split(";")
    for kernel_line in breakpoints_list:
        # Just to make sure things like this: kernel.cu:52;<nothing here>
        if len(kernel_line) > 0:
            kernel_places = kernel_line.split("-")
            k_l = kernel_places[0]
            kernel_info = {
                'breakpoint': ProfilerBreakpoint(spec=str(k_l), type=gdb.BP_BREAKPOINT, temporary=True),
                'kernel_name': kernel_places[0].split(":")[0],
                'kernel_line': kernel_places[0].split(":")[1],
                'kernel_end_line': kernel_places[1].split(":")[1]
            }
            kernel_info_list.append(kernel_info)
    return kernel_info_list


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

    try:
        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
    except gdb.error as err:
        print ("initializing setup: " + str(err))

    # Profiler has two steps
    # First: getting kernel information
    # Run app for the first time
    kludge_breakpoint = None
    kernel_info_list = None
    if time_profiler == 'False':
        kernel_info_list = set_breakpoints(kernel_conf_string)
        for kernel_info in kernel_info_list:
            kernel_info['breakpoint'].set_kernel_info_list(kernel_info_list=kernel_info_list)
        if kludge != 'None':
            kludge_breakpoint = ProfilerBreakpoint(spec=kludge, type=gdb.BP_BREAKPOINT,  kludge=True, temporary=True)

    gdb.execute("r")

    if kludge_breakpoint:
        # kludge_breakpoint.delete()
        del kludge_breakpoint

    # Second: save the retrieved information on a txt file
    # Save the information on file to the output
    if time_profiler == 'False':
        gdb.execute("c")
        try:
            while "The program is not being run" not in gdb.execute("c", to_string=True):
                pass
        except gdb.error as err:
            print str(err)

        # for kernel_info in kernel_info_list:
        #     kernel_info['breakpoint_hit_count'] = kernel_info['breakpoint'].hit_count
        #     kernel_info['breakpoint'].delete()
        #     del kernel_info['breakpoint']
        #     kernel_info['breakpoint'] = None

        cf.save_file(cp.KERNEL_INFO_DIR, kernel_info_list)
        del kernel_info_list

    else:
        gdb.execute("quit")

    if cp.DEBUG_PROFILER:
        print('FINISH PROFILER')


main()
