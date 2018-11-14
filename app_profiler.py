#!/usr/bin/python
import argparse
import os
import re
import signal
import time
import common_functions as cf
import common_parameters as cp


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


def profiler_caller(gdb_exec, benchmark_binary, benchmark_args):
    acc_time = 0
    script = '{} -ex \'py arg0 = {}\' -n -batch -x {}'
    benchmark_args_striped = benchmark_args.replace('\\n', '').replace('\\', '')
    init_string = '"file {}; set args {}"'.format(benchmark_binary, benchmark_args_striped)
    profiler_cmd = script.format(gdb_exec, init_string, cp.PROFILER_SCRIPT)
    if cp.DEBUG:
        print("PROFILER CMD: {}".format(profiler_cmd))

    for i in range(0, cp.MAX_TIMES_TO_PROFILE):
        start = time.time()
        os.system(profiler_cmd)
        end = time.time()
        acc_time += end - start
        cf.kill_all("killall -9 {}; killall -9 {}".format(
            os.path.basename(gdb_exec), os.path.basename(benchmark_binary)))

    return acc_time / cp.MAX_TIMES_TO_PROFILE


"""
Function to generate the gold execution
"""


def generate_gold(gdb_exec, benchmark_binary, benchmark_args):
    script = '{} -ex "py arg0 = {}" -n -batch -x {} > {} 2> {}'
    init_string = "file {}; set args {}".format(benchmark_binary, benchmark_args)
    profiler_cmd = script.format(gdb_exec, init_string, cp.PROFILER_SCRIPT,  cp.GOLD_OUTPUT_PATH , cp.GOLD_ERR_PATH)
    if cp.DEBUG:
        print("PROFILER CMD: {}".format(profiler_cmd))

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

    # First set env vars
    cf.set_python_env()

    ########################################################################
    # Profiler step
    # Max time will be obtained by running
    # it will also get app output for golden copy
    # that is,
    print("###################################################\n1 - Profiling application")
    benchmark_binary = conf.get('DEFAULT', 'benchmarkBinary')
    benchmark_args = conf.get('DEFAULT', 'benchmarkArgs')
    gdb_exec = conf.get("DEFAULT", "gdbExecName")

    max_time_app = profiler_caller(gdb_exec=gdb_exec, benchmark_binary=benchmark_binary, benchmark_args=benchmark_args)

    # saving gold
    generate_gold(gdb_exec=gdb_exec, benchmark_binary=benchmark_binary, benchmark_args=benchmark_args)

    sm_processor = conf.get("DEFAULT", "smx")
    stderr = conf.get("DEFAULT", "makeStderr")
    kernel_regs = generate_dict(sm_version=sm_processor, input_file_name=stderr)
    if len(kernel_regs) < 1:
        print("Warning: no kernel register information was retrieved from {} file.\nPlease check nvcc output and "
              "GPU's architecture.".format(stderr))

    # Save the kernel configuration txt file
    cf.save_file(file_path=cp.KERNEL_INFO_DIR, data={'max_time': max_time_app, 'kernel_registers': kernel_regs})

    print("1 - Profile finished\n###################################################")


if __name__ == '__main__':
    main()
