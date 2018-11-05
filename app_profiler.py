#!/usr/bin/python
import argparse
import os
import re
import signal
import sys
import time
import common_functions as cf
import common_parameters as cp

"""
CTRL + C event
"""


def signal_handler(sig, frame):
    global kill_strings
    print("\n\tKeyboardInterrupt detected, exiting gracefully!( at least trying :) )")
    kill_cmds = kill_strings.split(";")
    for cmd in kill_cmds:
        try:
            os.system(cmd)
        except Exception as err:
            print("Command err: {}".format(str(err)))

    sys.exit(0)


def generate_dict(sm_version, input_file_name):
    with open(input_file_name, "r") as f:
        # dictionary to store the number of allocated registers per static
        kernel_reg = {}

        kernel_name = ""  # temporary variable to store the kernel_name
        check_for_register_count = False

        # process the input file created by capturing the stderr while compiling the
        # application using -Xptxas -v options
        for line in f:  # for each line in the file
            m = re.match(".*Compiling entry function.*'(\S+)'.*for.*'{}'.*".format(sm_version), line)
            if m:
                kernel_name = m.group(1)
                check_for_register_count = True

            m = re.match(".*Used[ ]+(\d+)[ ]+registers.*", line)
            if check_for_register_count and m:
                reg_num = m.group(1)  # extract register number
                if kernel_name not in kernel_reg:
                    # associate the extracted register number with the kernel name
                    kernel_reg[kernel_name] = int(reg_num.strip())
                else:
                    print("Warning: {} exists in the kernel_reg dictionary. "
                          "Skipping this register count.".format(kernel_name))
                check_for_register_count = False

    return kernel_reg


"""
Function that calls the profiler based on the injection mode
"""


def profiler_caller(conf):
    acc_time = 0
    os.environ['CAROL_FI_INFO'] = conf.get("DEFAULT", "gdbInitStrings")

    if cp.DEBUG:
        print(os.environ['CAROL_FI_INFO'])

    for i in range(0, cp.MAX_TIMES_TO_PROFILE):
        profiler_cmd = cf.run_gdb_python(gdb_name=conf.get("DEFAULT", "gdbExecName"), script=cp.PROFILER_SCRIPT)
        start = time.time()
        os.system(profiler_cmd)
        end = time.time()
        acc_time += end - start
        cf.kill_all(conf=conf)

    return acc_time / cp.MAX_TIMES_TO_PROFILE


"""
Function to generate the gold execution
"""


def generate_gold(conf):
    os.environ['CAROL_FI_INFO'] = conf.get("DEFAULT", "gdbInitStrings")

    if cp.DEBUG:
        print(os.environ['CAROL_FI_INFO'])

    profiler_script = cp.PROFILER_SCRIPT + " > " + cp.GOLD_OUTPUT_PATH + " 2> " + cp.GOLD_ERR_PATH
    profiler_cmd = cf.run_gdb_python(gdb_name=conf.get("DEFAULT", "gdbExecName"),
                                     script=profiler_script)

    # Execute and save gold file
    os.system(profiler_cmd)


def main():
    global kill_strings
    os.system("rm -f {}".format(cp.KERNEL_INFO_DIR))
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="config_file", help='Configuration file', required=True)

    args = parser.parse_args()

    # Read the configuration file with data for all the apps that will be executed
    conf = cf.load_config_file(args.config_file)

    # Attach the signal to event
    kill_strings = conf.get("DEFAULT", "killStrs")
    signal.signal(signal.SIGINT, signal_handler)

    # First set env vars
    cf.set_python_env()

    ########################################################################
    # Profiler step
    # Max time will be obtained by running
    # it will also get app output for golden copy
    # that is,
    print("###################################################\n1 - Profiling application")
    max_time_app = profiler_caller(conf=conf)

    # saving gold
    generate_gold(conf=conf)

    sm_processor = conf.get("DEFAULT", "smx")
    stderr = conf.get("DEFAULT", "makeStderr")
    kernel_regs = generate_dict(sm_version=sm_processor, input_file_name=stderr)
    if len(kernel_regs) < 1:
        print("Warning: no kernel register information was retrieved from {} file.\nPlease check nvcc output and "
              "GPU's architecture.")

    # Save the kernel configuration txt file
    cf.save_file(file_path=cp.KERNEL_INFO_DIR, data={'max_time': max_time_app, 'kernel_registers': kernel_regs})

    print("1 - Profile finished\n###################################################")


if __name__ == '__main__':
    main()
