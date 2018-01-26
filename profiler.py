import gdb
import sys
sys.path.append("/home/carol/carol-fi") # I have to fix it
import common_functions as cf # All common functions will be at common_functions module

kernel_info_dir = "/tmp/carol-fi-kernel-info.txt"

# This list will contains all kernel info
kernel_info_list = []

"""
Get kernel Threads and addresses information
necessary to fault injection
"""


def get_kernel_address_event(event):
    global kernel_info_list

    # Search all kernels info, and all breakpoints
    for kernel_info in kernel_info_list:
        for breakpoint in event.breakpoints:

            # Get the addresses and thread for this kernel
            if breakpoint == kernel_info["breakpoint"]:

                # Thread info
                kernel_info["threads"] = cf.execute_command("info cuda threads")
                kernel_info["addresses"] = cf.execute_command("disassemble")

                gdb.flush()
                breakpoint.delete()

                kernel_info['breakpoint'] = None
                # Need to continue after get the kernel information
                gdb.execute("c")


"""
Set temporary breakpoints.
After they are hit they are deleted
"""


def set_breakpoints(kernel_conf_string):
    # We are going to set
    # temporary breakpoints
    # to retrieve info of each
    # kernel
    global kernel_info_list
    breakpoints_list = kernel_conf_string.split(";")
    for kernel_line in breakpoints_list:
        # Just to make sure things like this: kernel.cu:52;<nothing here>
        if len(kernel_line) > 0:
            kernel_info = {
                'breakpoint': gdb.Breakpoint(kernel_line, type=gdb.BP_BREAKPOINT),
                'kernel_name': kernel_line.split(":")[0],
                'kernel_line': kernel_line.split(":")[1]
                }

            kernel_info_list.append(kernel_info)


"""
This function will stop at each kernel
and extract the number of threads and theirs
cordinates.
"""


def get_kernel_threads():
    threads = cf.execute_command("info cuda threads")
    addresses = cf.execute_command("disassemble")



########################################################################
# Initialize GDB to run the app
gdb.execute("set confirm off")
gdb.execute("set pagination off")

conf = cf.load_config_file()

try:
    gdb_init_strings = conf.get("DEFAULT", "gdbInitStrings")

    for init_str in gdb_init_strings.split(";"):
        gdb.execute(init_str)

except gdb.error as err:
    print ("initializing setup: " + str(err))

########################################################################
# Profiler has two steps
# First: getting kernel information
# Run app for the first time

kernel_conf_string = conf.get("DEFAULT", "kernelBreaks")
set_breakpoints(kernel_conf_string)

gdb.events.stop.connect(get_kernel_address_event)
gdb.execute("r")

# Second: save the retrivied information on a txt file
# Save the informaticon file to the output
cf.save_file(kernel_info_dir, kernel_info_list)

########################################################################
print ("If you are seeing it, profiler has been finished")