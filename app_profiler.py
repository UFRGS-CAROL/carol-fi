#!/usr/bin/python
import argparse
import os
import time
import common_functions as cf
import common_parameters as cp

"""
Function that calls the profiler based on the injection mode
"""


def profiler_caller(conf):
    acc_time = 0

    # kludge
    if conf.has_option("DEFAULT", "kludge"):
        kludge = conf.get("DEFAULT", "kludge")
    else:
        kludge = None

    # First MAX_TIMES_TO_PROFILE is necessary to measure the application running time
    os.environ['CAROL_FI_INFO'] = conf.get(
        "DEFAULT", "gdbInitStrings") + "|" + conf.get("DEFAULT",
                                                      "kernelBreaks") + "|" + "True" + "|" + str(kludge)

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
    # kludge
    if conf.has_option("DEFAULT", "kludge"):
        kludge = conf.get("DEFAULT", "kludge")
    else:
        kludge = None

    # This run is to get carol-fi-kernel-info.txt
    os.environ['CAROL_FI_INFO'] = conf.get("DEFAULT", "gdbInitStrings") + "|" + conf.get(
        "DEFAULT", "kernelBreaks") + "|" + "False" + "|" + str(kludge)

    if cp.DEBUG:
        print(os.environ['CAROL_FI_INFO'])

    profiler_cmd = cf.run_gdb_python(gdb_name=conf.get("DEFAULT", "gdbExecName"), script=cp.PROFILER_SCRIPT)

    # Execute and save gold file
    start = time.time()
    os.system(profiler_cmd)
    end = time.time()

    return end - start


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="config_file", help='Configuration file', required=True)

    args = parser.parse_args()

    # Read the configuration file with data for all the apps that will be executed
    conf = cf.load_config_file(args.config_file)

    # First set env vars
    # GDB python cannot find common_functions.py, so I added this directory to PYTHONPATH
    current_path = os.path.dirname(os.path.realpath(__file__))
    os.environ["PYTHONPATH"] = "$PYTHONPATH:" + current_path

    ########################################################################
    # Profiler step
    # Max time will be obtained by running
    # it will also get app output for golden copy
    # that is,
    print("###################################################\n1 - Profiling application")
    # max_time_app = profiler_caller(conf=conf)

    # saving gold
    max_time_app = generate_gold(conf=conf)

    # Load and re-save the kernel configuration txt file
    kernel_list = cf.load_file(file_path=cp.KERNEL_INFO_DIR)
    for kernel_dict in kernel_list:
        kernel_dict['max_time'] = max_time_app
    cf.save_file(file_path=cp.KERNEL_INFO_DIR, data=kernel_list)

    print("1 - Profile finished, \n###################################################")


if __name__ == '__main__':
    main()
