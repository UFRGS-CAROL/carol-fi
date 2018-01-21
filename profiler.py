import sys
sys.path.append("/home/carol/carol-fi") # I have to fix it

import gdb
import re
import common_functions as cf # All common functions will be at common_functions module

KERNEL_INFO_DIR = "/tmp/carol-fi-kernel-info.txt"

# This list will contains all kernel info
KERNEL_INFO_LIST = []

"""
This function will return all names of
active kernels at the first executed kernel.
This will only be executed when an event is defined
for it.
"""


def get_kernel_names_event(event):
    global KERNEL_INFO_LIST

    # Get info from gdb
    kernel_names = cf.execute_command("info cuda kernels")
    print kernel_names

    tittle = "Kernel Parent Dev Grid Status   SMs Mask   GridDim  BlockDim Invocation"

    # Information for all kernels
    for l in kernel_names:
        kernel_info = {}
        # Something went wrong
        if "No CUDA kernels" in l:
            return None

        # Tittle case
        elif tittle.replace(" ", "") not in l.replace(" ", ""):
            m = re.match(
                "\*[ ]*(\d+)[ ]*(\S+).*[\)]*.*(\d+)[ ]*(\d+)[ ]*(\S+)[ ]*([0-9a-fA-F][xX][0-9a-fA-F]+)[ ]*\((\d+),(\d+),(\d+)\)[ ]*\((\d+),(\d+),(\d+)\)[ ]*(\S+)",
            l)
            if m:
                #  '*      0      -   0    1 Active 0x0fffffff (20,10,1) (32,32,1)
            # matrixMulCUDA<32>(C=0x1020db2c000, A=0x1020da00000, B=0x1020da64000, wA=320, wB=640)'
                kernel_info["Kernel"] = m.group(1)
                kernel_info["Parent"] = m.group(2)
                kernel_info["Dev"] = m.group(3)
                kernel_info["Grid"] = m.group(4)
                kernel_info["Status"] = m.group(5)
                kernel_info["SMs_Mask"] = m.group(6)

                kernel_info["GridDim"] = [m.group(7), m.group(8), m.group(9)]
                kernel_info["BlockDim"] = [m.group(10), m.group(11), m.group(12)]
                kernel_info["Invocation"] = m.group(13)

            KERNEL_INFO_LIST.append(kernel_info)


    # Need only colect information at the first kernel entry
    cf.execute_command("set cuda break_on_launch none")

"""
Get kernel Threads and addresses necessary
to fault injection
"""
def get_kernel_address_event(event):
    global KERNEL_INFO_LIST, KERNEL_INFO_DIR
    ev = vars(event)
    print "Event info" , ev["breakpoints"][0].location

"""
Set temporary breakpoints.
After they are hit they are deleted
"""


def set_breakpoints():
    # We are going to set
    # temporary breakpoints
    # to retrieve info of each
    # kernel
    global KERNEL_INFO_LIST
    for kernel_info in KERNEL_INFO_LIST:
        print kernel_info
        kernel_info['Invocation'] = (kernel_info['Invocation'].split("("))[0]
        kernel_info['breakpoint'] = gdb.Breakpoint(kernel_info['Invocation'], type=gdb.BP_BREAKPOINT)



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


try:
    gdbInitStrings = "file /home/carol/carol-fi/codes/cuda/matrixMul/matrixMul; set args -wA=512 -hA=512 -hB=512 -wB=512"

    for initStr in gdbInitStrings.split(";"):
        print initStr
        gdb.execute(initStr)

except gdb.error as err:
    print "initializing setup: " + str(err)

########################################################################
# Profiler has two steps
# First: getting kernel information

gdb.events.stop.connect(get_kernel_names_event)

# Set to gdb stop at the first kernel
cf.execute_command("set cuda break_on_launch application")

# Run app for the first time
gdb.execute("r")
gdb.execute("c")
gdb.events.stop.disconnect(get_kernel_names_event)

# Second:
set_breakpoints()

gdb.events.stop.connect(get_kernel_address_event)
gdb.execute("r")





