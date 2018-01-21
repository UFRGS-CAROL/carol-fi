import gdb
import sys
sys.path.append("/home/carol/carol-fi") # I have to fix it
import common_functions as cf # All common functions will be at common_functions module

KERNEL_INFO_DIR = "/tmp/carol-fi-kernel-info.txt"

# This list will contains all kernel info
KERNEL_INFO_LIST = []

"""
Get kernel Threads and addresses information
necessary to fault injection
"""


def get_kernel_address_event(event):
    global KERNEL_INFO_LIST

    # Search all kernels info, and all breakpoints
    for kernel_info in KERNEL_INFO_LIST:
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
    global KERNEL_INFO_LIST
    breakpoints_list = kernel_conf_string.split(";")
    for kernel_line in breakpoints_list:
        print kernel_line
        kernel_info = {
            'breakpoint': gdb.Breakpoint(kernel_line, type=gdb.BP_BREAKPOINT),
            'kernel_name': kernel_line.split(":")[0],
            'kernel_line': kernel_line.split(":")[1]
            }

        KERNEL_INFO_LIST.append(kernel_info)


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
    print "initializing setup: " + str(err)

########################################################################
# Profiler has two steps
# First: getting kernel information
# Run app for the first time

kernel_conf_string = conf.get("DEFAULT", "kernelBreaks")
set_breakpoints(kernel_conf_string)

gdb.events.stop.connect(get_kernel_address_event)
gdb.execute("r")

# Save the informaticon file to the output
#cf.save_file(KERNEL_INFO_DIR, KERNEL_INFO_LIST)


########################################################################
print "If you are seeing it, profiler has been finished"





# gdb.events.stop.connect(get_kernel_names_event)
#
# # Set to gdb stop at the first kernel
# cf.execute_command("set cuda break_on_launch application")
# """
# This function will return all names of
# active kernels at the first executed kernel.
# This will only be executed when an event is defined
# for it.
# """
#
#
# def get_kernel_names_event(event):
#     global KERNEL_INFO_LIST
#
#     # Get info from gdb
#     kernel_names = cf.execute_command("info cuda kernels")
#     print kernel_names
#
#     tittle = "Kernel Parent Dev Grid Status   SMs Mask   GridDim  BlockDim Invocation"
#
#     # Information for all kernels
#     for l in kernel_names:
#         kernel_info = {}
#         # Something went wrong
#         if "No CUDA kernels" in l:
#             return None
#
#         # Tittle case
#         elif tittle.replace(" ", "") not in l.replace(" ", ""):
#             m = re.match(
#                 "\*[ ]*(\d+)[ ]*(\S+).*[\)]*.*(\d+)[ ]*(\d+)[ ]*(\S+)[ ]*([0-9a-fA-F][xX][0-9a-fA-F]+)[ ]*\((\d+),(\d+),(\d+)\)[ ]*\((\d+),(\d+),(\d+)\)[ ]*(\S+)",
#             l)
#             if m:
#                 #  '*      0      -   0    1 Active 0x0fffffff (20,10,1) (32,32,1)
#             # matrixMulCUDA<32>(C=0x1020db2c000, A=0x1020da00000, B=0x1020da64000, wA=320, wB=640)'
#                 kernel_info["Kernel"] = m.group(1)
#                 kernel_info["Parent"] = m.group(2)
#                 kernel_info["Dev"] = m.group(3)
#                 kernel_info["Grid"] = m.group(4)
#                 kernel_info["Status"] = m.group(5)
#                 kernel_info["SMs_Mask"] = m.group(6)
#
#                 kernel_info["GridDim"] = [m.group(7), m.group(8), m.group(9)]
#                 kernel_info["BlockDim"] = [m.group(10), m.group(11), m.group(12)]
#                 kernel_info["Invocation"] = m.group(13)
#
#             KERNEL_INFO_LIST.append(kernel_info)
#
#
#     # Need only colect information at the first kernel entry
#     cf.execute_command("set cuda break_on_launch none")