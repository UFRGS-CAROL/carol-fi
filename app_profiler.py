#!/usr/bin/python
import argparse
import os
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
    if len(sys.argv) != 4:
        print "Usage: python extract_reg_numbers.py <application name> <sm version> <stderr file name>"
        print "Example: python extract_reg_numbers.py simple_add sm_35 stderr"
        print "It is prefered that you run this script from the application directory and store the pickle file there."
        sys.exit(-1)

    f = open(input_file_name, "r")

    # dictionary to store the number of allocated registers per static
    kernel_reg = {}

    kname = ""  # temporary variable to store the kname
    check_for_regcount = False

    # process the input file created by capturing the stderr while compiling the
    # application using -Xptxas -v options
    for line in f:  # for each line in the file
        if "Compiling entry function" in line:  # if line has this string
            kname = line.split("'")[1].strip()  # extract kernel name
            check_for_regcount = True if sm_version in line else False
        if check_for_regcount and ": Used" in line and "registers, " in line:
            reg_num = line.split(':')[1].split()[1]  # extract register number
            if kname not in kernel_reg:
                kernel_reg[kname] = int(reg_num.strip())  # associate the extracted register number with the kernel name
            else:
                print "Warning: " + kname + " exists in the kernel_reg dictionary. Skipping this regcount."

    # print the recorded kernel_reg dictionary
    # pickle_filename = app + "_kernel_regcount.p"
    # cPickle.dump(kernel_reg, open(pickle_filename, "wb"))
    # print "Created the pickle file: " + os.getcwd() + "/" + pickle_filename
    # print "Load it from the specific_params.py file"
    return kernel_reg
    # print_dictionary(kernel_reg)


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
        print(profiler_cmd)
        start = time.time()
        # os.system(profiler_cmd)
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
    # os.system(profiler_cmd)


def main():
    os.system("rm -f {}".format(cp.KERNEL_INFO_DIR))
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="config_file", help='Configuration file', required=True)

    args = parser.parse_args()

    # Read the configuration file with data for all the apps that will be executed
    conf = cf.load_config_file(args.config_file)

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

    # Load and re-save the kernel configuration txt file
    # kernel_list = cf.load_file(file_path=cp.KERNEL_INFO_DIR)
    cf.save_file(file_path=cp.KERNEL_INFO_DIR, data=[{'max_time': max_time_app, 'kernel_registers': kernel_regs}])

    print("1 - Profile finished\n###################################################")


if __name__ == '__main__':
    main()
