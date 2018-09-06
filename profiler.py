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

    for i, kernel_line in enumerate(breakpoints_list):
        # Just to make sure things like this: kernel.cu:52;<nothing here>
        if len(kernel_line) > 0:
            kernel_places = kernel_line.split("-")
            k_l = kernel_places[0]
            kernel_info = {
                'breakpoint': ProfilerBreakpoint(spec=str(k_l), type=gdb.BP_BREAKPOINT, temporary=True,
                                                 kernel_info_list=kernel_info_list, list_index=i),
                'kernel_name': kernel_places[0].split(":")[0],
                'kernel_line': kernel_places[0].split(":")[1],
                'kernel_end_line': kernel_places[1].split(":")[1]
            }
            kernel_info_list.append(kernel_info)

    for i in kernel_info_list:
        print(i['addresses'])
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
    time_profiler = False if time_profiler == 'False' else True

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

    if not time_profiler:
        kernel_info_list = set_breakpoints(kernel_conf_string)
        # for kernel_info in kernel_info_list:
        #     kernel_info['breakpoint'].set_kernel_info_list(kernel_info_list=kernel_info_list)
        if kludge != 'None':
            kludge_breakpoint = ProfilerBreakpoint(spec=kludge, type=gdb.BP_BREAKPOINT, kludge=True, temporary=True)

    gdb.execute("r")

    if kludge_breakpoint:
        del kludge_breakpoint
        gdb.execute("c")

    # Second: save the retrieved information on a txt file
    # Save the information on file to the output
    if not time_profiler:
        gdb.execute("c")

        for kernel_info in kernel_info_list:
            print("PRINTING KERNEL ADDRESSES\n\n")
            for i in kernel_info['addresses']:
                print(i[0])
            del kernel_info['breakpoint']
            kernel_info['breakpoint'] = None

        cf.save_file(cp.KERNEL_INFO_DIR, kernel_info_list)
        del kernel_info_list

    if cp.DEBUG_PROFILER:
        print('FINISH PROFILER')


main()
