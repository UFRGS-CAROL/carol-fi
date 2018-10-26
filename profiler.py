import os
import gdb
import common_parameters as cp  # All common parameters will bet at common_parameters module

"""
Main function
"""


def main():
    # Initialize GDB to run the app
    gdb.execute("set confirm off")
    gdb.execute("set pagination off")
    gdb.execute("set target-async off")
    gdb.execute("set non-stop off")

    gdb_init_strings = str(os.environ["CAROL_FI_INFO"])

    try:
        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
    except gdb.error as err:
        print ("initializing setup: " + str(err))

    gdb.execute("r")

    i = 0
    try:
        while 'The program' not in gdb.execute('c', to_string=True):
            i += 1
    except Exception as err:
        if cp.DEBUG_PROFILER:
            print("CONTINUED {} times. Format {}".format(i, err))

    if cp.DEBUG_PROFILER:
        print('FINISH PROFILER')


main()
