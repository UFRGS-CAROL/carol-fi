#!/usr/bin/python

from __future__ import print_function

import os
import subprocess
import time
import datetime
import random
from multiprocessing import Process
import re
import shutil
import argparse
import csv
import common_functions as cf
import common_parameters as cp

"""
Run gdb python script with specific parameters
It makes standart gdb script calls
"""


def run_gdb_python(gdb_name, script):
    cmd = 'env CUDA_DEVICE_WAITS_ON_EXCEPTION=1 ' + gdb_name
    cmd += ' -n --nh --nx -q -batch-silent --return-child-result -x ' + script
    return cmd


"""
Kill all remaining processes
"""


def kill_all(conf):
    for cmd in str(conf.get("DEFAULT", "killStrs")).split(";"):
        os.system(cmd)


"""
Class RunGdb: necessary to run gdb while
the main thread register the time
If RunGdb execution time > max timeout allowed
this thread will be killed
"""


class RunGDB(Process):
    def __init__(self, unique_id, gdb_exec_name, flip_script, current_dir):
        super(RunGDB, self).__init__()
        self.__gdb_exe_name = gdb_exec_name
        self.__flip_script = flip_script
        self.__unique_id = unique_id
        self.__current_dir = current_dir

    def run(self):
        os.system("stty tostop")

        if cp.DEBUG:
            print("GDB Thread run, section and id: ", self.__unique_id)

        start_cmd = run_gdb_python(gdb_name=self.__gdb_exe_name, script=self.__flip_script)
        try:
            os.system(start_cmd + " >" + cp.INJ_OUTPUT_PATH + " 2>" + cp.INJ_ERR_PATH)
        except Exception as err:
            with open(cp.INJ_ERR_PATH, 'w') as file_err:
                file_err.write(str(err))


"""
Class SummaryFile: this class will write the information
of each injection in a csv file to make easier data
parsing after fault injection
"""


class SummaryFile:
    # Filename
    __filename = ""
    # csv file
    __csv_file = None
    # Dict reader
    __dict_buff = None

    # Fieldnames
    __fieldnames = None

    # It will only open in a W mode for the first time
    def __init__(self, **kwargs):
        # Set arguments
        self.__filename = kwargs.get("filename")
        self.__fieldnames = kwargs.get("fieldnames")

        # Open and start csv file
        self.__open_csv(mode='w')
        self.__dict_buff.writeheader()
        self.__close_csv()

    """
    Open a file if it exists
    mode can be r or w
    default is r
    """

    def __open_csv(self, mode='a'):
        if os.path.isfile(self.__filename):
            self.__csv_file = open(self.__filename, mode)
        elif mode == 'w':
            self.__csv_file = open(self.__filename, mode)
        else:
            raise IOError(str(self.__filename) + " FILE NOT FOUND")

        # If file exists it is append or read
        if mode in ['w', 'a']:
            self.__dict_buff = csv.DictWriter(self.__csv_file, self.__fieldnames)
        elif mode == 'r':
            self.__dict_buff = csv.DictReader(self.__csv_file)

    """
    To not use __del__ method, close csv file
    """

    def __close_csv(self):
        if not self.__csv_file.closed:
            self.__csv_file.close()
        self.__dict_buff = None

    """
    Write a csv row, if __mode == w or a
    row must be a dict
    """

    def write_row(self, row):
        # If it is a list must convert first
        row_ready = {}
        if isinstance(row, list):
            for fields, data in zip(self.__fieldnames, row):
                row_ready[fields] = data
        else:
            row_ready = row

        # Open file first
        self.__open_csv()
        self.__dict_buff.writerow(row_ready)
        self.__close_csv()

    """
    Read rows
    return read rows from file in a list
    """

    def read_rows(self):
        self.__open_csv()
        rows = [row for row in self.__dict_buff]
        self.__close_csv()
        return rows


"""
Check if app stops execution (otherwise kill it after a time)
"""


def check_finish(section, conf, logging, timestamp_start, end_time, p):
    is_hang = False
    now = int(time.time())

    # Wait maxWaitTimes the normal duration of the program before killing it
    max_wait_time = int(conf.get(section, "maxWaitTimes")) * end_time
    kill_strings = conf.get(section, "killStrs")

    p_is_alive = p.is_alive()
    while (now - timestamp_start) < max_wait_time and p_is_alive:
        time.sleep(max_wait_time / 10.0)
        now = int(time.time())
        p_is_alive = p.is_alive()
        if not p_is_alive:
            logging.debug("Process not running")
            if cp.DEBUG:
                print("PROCESS NOT RUNNING")

    # check execution finished before or after waitTime
    if (now - timestamp_start) < max_wait_time:
        logging.info("Execution finished before waitTime")
    else:
        logging.info("Execution did not check_finish before waitTime")
        is_hang = True

    logging.debug("now: " + str(now))
    logging.debug("timestampStart: " + str(timestamp_start))

    # Kill all the processes to make sure the machine is clean for another test
    for k in kill_strings.split(";"):
        os.system(k)
        logging.debug("kill cmd: " + k)

    # Make sure process check_finish before trying to execute
    p.join()
    p.terminate()

    if cp.DEBUG:
        print("PROCESS JOINED")

    return is_hang


"""
Copy the logs and output(if fault not masked) to a selected folder
"""


def save_output(section, is_sdc, is_hang, logging, unique_id, flip_log_file, output_file):
    # FI successful
    fi_injected = False
    if os.path.isfile(flip_log_file):
        fp = open(flip_log_file, "r")
        content = fp.read()
        if re.search("Fault Injection Successful", content):
            fi_injected = True
        fp.close()

    dt = datetime.datetime.fromtimestamp(time.time())
    ymd = dt.strftime('%Y_%m_%d')
    ymdhms = dt.strftime('%Y_%m_%d_%H_%M_%S')
    ymdhms = unique_id + "-" + ymdhms
    dir_d_t = os.path.join(ymd, ymdhms)

    if not fi_injected:
        cp_dir = os.path.join('logs', section, 'failed-injection', dir_d_t)
        logging.summary(section + " - Fault Injection Failed")
    elif is_hang:
        cp_dir = os.path.join('logs', section, 'hangs', dir_d_t)
        logging.summary(section + " - Hang")
    elif is_sdc:
        cp_dir = os.path.join('logs', section, 'sdcs', dir_d_t)
        logging.summary(section + " - SDC")
    elif not os.path.isfile(output_file):
        cp_dir = os.path.join('logs', section, 'noOutputGenerated', dir_d_t)
        logging.summary(section + " - NoOutputGenerated")
    else:
        cp_dir = os.path.join('logs', section, 'masked', dir_d_t)
        logging.summary(section + " - Masked")

    if not os.path.isdir(cp_dir):
        os.makedirs(cp_dir)

    # Moving all necessary files
    for file_to_move in [flip_log_file, cp.INJ_OUTPUT_PATH, cp.INJ_ERR_PATH, cp.DIFF_LOG, cp.DIFF_ERR_LOG]:
        try:
            shutil.move(file_to_move, cp_dir)
        except Exception as err:
            if cp.DEBUG:
                print("ERROR ON MOVING {} -- {}".format(file_to_move, str(err)))


"""
Pre execution commands
"""


def pre_execution(conf, section):
    if conf.has_option(section, "preExecScript"):
        script = conf.get(section, "preExecScript")
        os.system(script)


"""
Pos execution commands
"""


def pos_execution(conf, section):
    if conf.has_option(section, "posExecScript"):
        script = conf.get(section, "posExecScript")
        os.system(script)


"""
Check output files for SDCs
"""


def check_sdcs_and_app_crash(logging, sdc_check_script):
    is_sdc = False
    is_app_crash = False
    if not os.path.isfile(cp.INJ_OUTPUT_PATH):
        logging.error("outputFile not found: " + cp.INJ_OUTPUT_PATH)
        is_app_crash = True
    elif not os.path.isfile(cp.GOLD_OUTPUT_PATH):
        logging.error("gold_file not found: " + cp.GOLD_OUTPUT_PATH)
        raise ValueError("GOLD FILE NOT FOUND")
    elif not os.path.isfile(sdc_check_script):
        logging.error("sdc check script file not found: " + sdc_check_script)
        raise ValueError("SDC CHECK SCRIPT NOT FOUND")
    elif not os.path.isfile(cp.INJ_ERR_PATH):
        logging.error("possible crash, stderr not found: " + cp.INJ_OUTPUT_PATH)
        is_app_crash = True
    elif not os.path.isfile(cp.GOLD_ERR_PATH):
        logging.error("gold_err_file not found: " + cp.GOLD_ERR_PATH)
        raise ValueError("GOLD ERR FILE NOT FOUND")
    if os.path.isfile(cp.GOLD_OUTPUT_PATH) and os.path.isfile(cp.INJ_OUTPUT_PATH) and os.path.isfile(
            cp.GOLD_ERR_PATH) and os.path.isfile(cp.INJ_ERR_PATH):
        # Set environ variables for sdc_check_script
        os.environ['GOLD_OUTPUT_PATH'] = cp.GOLD_OUTPUT_PATH
        os.environ['INJ_OUTPUT_PATH'] = cp.INJ_OUTPUT_PATH
        os.environ['GOLD_ERR_PATH'] = cp.GOLD_ERR_PATH
        os.environ['INJ_ERR_PATH'] = cp.INJ_ERR_PATH
        os.environ['DIFF_LOG'] = cp.DIFF_LOG
        os.environ['DIFF_ERR_LOG'] = cp.DIFF_ERR_LOG
        os.system("sh " + sdc_check_script)

        # Test if files are ok
        with open(cp.DIFF_LOG, 'r') as fi:
            out_lines = fi.readlines()
            if len(out_lines) != 0:
                # Check if NVIDIA signals on output
                for signal in cp.SIGNALS:
                    for line in out_lines:
                        if signal in line:
                            is_app_crash = True
                            break
                    if is_app_crash:
                        break
                if not is_app_crash:
                    is_sdc = True

        with open(cp.DIFF_ERR_LOG, 'r') as fi_err:
            err_lines = fi_err.readlines()
            if len(err_lines) != 0:
                is_app_crash = True

    return is_sdc, is_app_crash


"""
Generate environment string for cuda-gdb
valid_block, valid_thread, valid_register, bits_to_flip, fault_model, injection_site, breakpoint_location,
    flip_log_file, debug, gdb_init_strings
The default parameters are necessary for break and signal mode differentiations
"""


def gen_env_string(valid_block, valid_thread, valid_register, bits_to_flip, fault_model,
                   breakpoint_location, flip_log_file, debug, gdb_init_strings, kludge, breaks_to_ignore):
    # Block and thread
    env_string = ",".join(str(i) for i in valid_block) + "|" + ",".join(str(i) for i in valid_thread)
    env_string += "|" + valid_register + "|" + ",".join(str(i) for i in bits_to_flip)
    env_string += "|" + str(fault_model) + "|" + breakpoint_location
    env_string += "|" + flip_log_file + "|" + str(debug) + "|" + gdb_init_strings + "|" + str(kludge)
    env_string += "|" + str(breaks_to_ignore)

    if cp.DEBUG:
        print("ENV STRING:", env_string)
    os.environ['CAROL_FI_INFO'] = env_string


"""
Function to run one execution of the fault injector
return old register value, new register value
"""


def run_gdb_fault_injection(**kwargs):
    # These are the mandatory parameters
    bits_to_flip = kwargs.get('bits_to_flip')
    fault_model = kwargs.get('fault_model')
    section = kwargs.get('section')
    unique_id = kwargs.get('unique_id')
    valid_register = kwargs.get('valid_register')
    conf = kwargs.get('conf')
    max_time = float(kwargs.get('max_time'))
    kludge = kwargs.get('kludge')

    # Parameters for thread selection
    valid_block = kwargs.get('valid_block')
    valid_thread = kwargs.get('valid_thread')
    breakpoint_location = kwargs.get('break_line')

    # SDC check parameters
    current_path = kwargs.get('current_path')

    # Breaks to ignore
    injection_place = kwargs.get('breaks_to_ignore')

    # Logging file
    flip_log_file = "/tmp/carolfi-flipvalue-{}.log".format(unique_id)

    # Starting FI process
    if cp.DEBUG:
        print("STARTING GDB SCRIPT")

    logging = cf.Logging(log_file=flip_log_file, debug=conf.get("DEFAULT", "debug"), unique_id=unique_id)
    logging.info("Starting GDB script")

    # Generate configuration file for specific test
    gen_env_string(gdb_init_strings=conf.get(section, "gdbInitStrings"),
                   debug=conf.get(section, "debug"),
                   valid_block=valid_block,
                   valid_thread=valid_thread,
                   valid_register=valid_register,
                   bits_to_flip=bits_to_flip,
                   fault_model=fault_model,
                   breakpoint_location=breakpoint_location,
                   flip_log_file=flip_log_file,
                   kludge=kludge,
                   breaks_to_ignore=injection_place)

    if cp.DEBUG:
        print("ENV GENERATE FINISHED")

    # Run pre execution function
    pre_execution(conf=conf, section=section)

    if cp.DEBUG:
        print("PRE EXECUTION")
    # Create one thread to start gdb script
    # Start fault injection process
    fi_process = RunGDB(unique_id=unique_id, gdb_exec_name=conf.get("DEFAULT", "gdbExecName"),
                        flip_script=cp.FLIP_SCRIPT, current_dir=current_path)

    if cp.DEBUG:
        print("STARTING PROCESS")
    fi_process.start()

    if cp.DEBUG:
        print("PROCESS SPAWNED")
    # Start counting time
    timestamp_start = int(time.time())

    # Check if app stops execution (otherwise kill it after a time)
    is_hang = check_finish(section=section, conf=conf, logging=logging, timestamp_start=timestamp_start,
                           end_time=max_time, p=fi_process)
    if cp.DEBUG:
        print("FINISH CHECK OK")

    # Run pos execution function
    pos_execution(conf=conf, section=section)
    sdc_check_script = current_path + '/' + conf.get('DEFAULT', 'goldenCheckScript')

    # Check output files for SDCs
    is_sdc, is_app_crash = check_sdcs_and_app_crash(logging=logging, sdc_check_script=sdc_check_script)
    if cp.DEBUG:
        print("CHECK SDCs OK")

    # remove thrash
    del fi_process

    # Search for set values for register
    # Must be done before save output
    # Was fault injected?
    try:
        reg_old_value = logging.search("reg_old_value")
        reg_new_value = logging.search("reg_new_value")
        reg_old_value = re.findall("reg_old_value: (\S+)", reg_old_value)[0]
        reg_new_value = re.findall("reg_new_value: (\S+)", reg_new_value)[0]

        fault_successful = True
    except Exception as e:
        reg_new_value = reg_old_value = ''
        fault_successful = False
        if cp.DEBUG:
            print(str(e))

    # Copy output files to a folder
    save_output(
        section=section, is_sdc=is_sdc, is_hang=(is_hang or is_app_crash), logging=logging, unique_id=unique_id,
        flip_log_file=flip_log_file, output_file=cp.INJ_OUTPUT_PATH)

    kill_all(conf=conf)
    if cp.DEBUG:
        print("SAVE OUTPUT AND RETURN")

    return reg_old_value, reg_new_value, fault_successful, is_hang or is_app_crash, is_sdc


"""
Support function to parse a line of disassembled code
"""


def parse_line(instruction_line):
    registers = []
    instruction = ''
    address = ''
    byte_location = ''

    # Do not process MOV instructions
    if 'mov' in instruction_line or 'MOV' in instruction_line:
        return None, None, None, None, None

    comma_line_count = instruction_line.count(',')

    # INSTRUCTION R1, R2...
    # 0x0000000000b418e8 <+40>: MOV R4, R2
    expression = ".*([0-9a-fA-F][xX][0-9a-fA-F]+) (\S+):[ \t\r\f\v]*(\S+)[ ]*(\S+)" + str(
        ",[ ]*(\S+)" * comma_line_count)

    m = re.match(expression + ".*", instruction_line)
    if m:
        address = m.group(1)
        byte_location = m.group(2)
        instruction = m.group(3)

        # Check register also
        registers = [m.group(4 + i) for i in range(0, comma_line_count + 1)]
        is_valid_line = False
        for r in registers:
            if 'R' in r:
                is_valid_line = True
                break

        if not is_valid_line:
            return None, None, None, None, None
    return registers, address, byte_location, instruction, m


"""
Selects a valid thread for a specific
kernel
return the coordinates for the block
and the thread
"""


def get_valid_thread(threads):
    element = random.randrange(2, len(threads))
    # randomly chosen first block and thread
    #  (15,2,0) (31,12,0)    (15,2,0) (31,31,0)    20 0x0000000000b41a28 matrixMul.cu    47
    block_thread = re.match(".*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*", threads[element])

    block_x = block_thread.group(1)
    block_y = block_thread.group(2)
    block_z = block_thread.group(3)

    thread_x = block_thread.group(4)
    thread_y = block_thread.group(5)
    thread_z = block_thread.group(6)

    return [block_x, block_y, block_z], [thread_x, thread_y, thread_z]


"""
Randomly selects a thread, address and a bit location
to inject a fault.
"""


def gen_injection_location(kernel_info_dict, max_num_regs, injection_site, fault_model):
    # A valid block is a [block_x, block_y, block_z] coordinate
    # A valid thread is a [thread_x, thread_y, thread_z] coordinate
    valid_block, valid_thread = get_valid_thread(kernel_info_dict["threads"])

    # Randomly choose a place to inject a fault
    injection_place = random.randint(0, kernel_info_dict["breakpoint_hit_count"])

    bits_to_flip = bit_flip_selection(fault_model=fault_model)
    valid_register = None

    # Select INST_OUT, INST_ADD, and RF
    # instruction output
    if injection_site == 'INST_OUT':
        raise NotImplementedError
    # instruction address
    elif injection_site == 'INST_ADD':
        raise NotImplementedError
    # Register file
    elif injection_site == 'RF':
        valid_register = 'R' + str(random.randint(0, max_num_regs))

    return valid_thread, valid_block, valid_register, bits_to_flip, injection_place


"""
This function will select the bits that will be flipped
if it is least significant bits it will reduce the starting bit range
"""


def bit_flip_selection(fault_model):
    # Randomly select (a) bit(s) to flip
    # Max double bit flip
    max_size_register_fault_model = cp.SINGLE_MAX_SIZE_REGISTER

    # Least 16 bits
    if fault_model == 4:
        max_size_register_fault_model = 16

    # Least 8 bits
    elif fault_model == 5:
        max_size_register_fault_model = 8

    bits_to_flip = [0] * 2
    bits_to_flip[0] = random.randint(0, max_size_register_fault_model - 1)
    # Make sure that the same bit is not going to be selected
    r = range(0, bits_to_flip[0]) + range(bits_to_flip[0] + 1, max_size_register_fault_model)
    bits_to_flip[1] = random.choice(r)
    return bits_to_flip


"""
This injector has two injection options
this function performs fault injection
by creating a breakpoint and steeping into it
"""


def fault_injection_by_breakpoint(conf, fault_models, iterations, kernel_info_list, summary_file,
                                  max_time, current_path):
    # kludge
    if conf.has_option("DEFAULT", "kludge"):
        kludge = conf.get("DEFAULT", "kludge")
    else:
        kludge = None

    for num_rounds in range(iterations):
        # Execute the fault injector for each one of the sections(apps) of the configuration file
        for fault_model in fault_models:
            # Execute one fault injection for a specific app
            # For each kernel
            for kernel_info_dict in kernel_info_list:
                # Generate an unique id for this fault injection
                unique_id = str(num_rounds) + "_" + str(fault_model)
                try:
                    thread, block, register, bits_to_flip, injection_place = gen_injection_location(
                        kernel_info_dict=kernel_info_dict, max_num_regs=int(conf.get("DEFAULT", "maxNumRegs")),
                        injection_site=conf.get("DEFAULT", "injectionSite"), fault_model=fault_model)

                    # Selects the random line to inject
                    kernel_begin = kernel_info_dict["kernel_line"]
                    kernel_end = kernel_info_dict["kernel_end_line"]
                    rand_line = random.randint(int(kernel_begin), int(kernel_end))
                    break_line = str(kernel_info_dict["kernel_name"] + ":"
                                     + str(rand_line))

                    r_old_val, r_new_val, fault_injected, hang, sdc = run_gdb_fault_injection(section="DEFAULT",
                                                                                              conf=conf,
                                                                                              unique_id=unique_id,
                                                                                              valid_block=block,
                                                                                              valid_thread=thread,
                                                                                              valid_register=register,
                                                                                              bits_to_flip=bits_to_flip,
                                                                                              fault_model=fault_model,
                                                                                              break_line=break_line,
                                                                                              max_time=max_time,
                                                                                              current_path=current_path,
                                                                                              kludge=kludge,
                                                                                              breaks_to_ignore=
                                                                                              injection_place)
                    # Write a row to summary file
                    row = [num_rounds, fault_model]
                    row.extend(thread)
                    row.extend(block)
                    row.extend(
                        [r_old_val, r_new_val, 0, register, break_line, fault_injected,
                         hang,
                         sdc])
                    print(row)
                    summary_file.write_row(row=row)
                    time.sleep(2)
                except Exception as err:
                    if cp.DEBUG:
                        print("\nERROR ON BREAK POINT MODE: Fault was not injected, {}".format(str(err)))


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
        profiler_cmd = run_gdb_python(gdb_name=conf.get("DEFAULT", "gdbExecName"), script=cp.PROFILER_SCRIPT)
        start = time.time()
        os.system(profiler_cmd)
        end = time.time()
        acc_time += end - start
        kill_all(conf=conf)

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

    profiler_cmd = run_gdb_python(gdb_name=conf.get("DEFAULT", "gdbExecName"), script=cp.PROFILER_SCRIPT)
    # Execute and save gold file
    os.system(profiler_cmd + " > " + cp.GOLD_OUTPUT_PATH + " 2> " + cp.GOLD_ERR_PATH)


"""
Main function
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="config_file", help='Configuration file', required=True)
    parser.add_argument('-i', '--iter', dest="iterations",
                        help='How many times to repeat the programs in the configuration file', required=True)

    args = parser.parse_args()
    if args.iterations < 1:
        parser.error('Iterations must be greater than zero')

    # Start with a different seed every time to vary the random numbers generated
    # the seed will be the current number of second since 01/01/70
    random.seed()

    # Read the configuration file with data for all the apps that will be executed
    conf = cf.load_config_file(args.config_file)

    # First set env vars
    # GDB python cannot find common_functions.py, so I added this directory to PYTHONPATH
    current_path = os.path.dirname(os.path.realpath(__file__))
    os.environ['PYTHONPATH'] = "$PYTHONPATH:" + current_path

    ########################################################################
    # Profiler step
    # Max time will be obtained by running
    # it will also get app output for golden copy
    # that is,
    print("###################################################\n1 - Profiling application")
    max_time_app = profiler_caller(conf=conf)

    # saving gold
    generate_gold(conf=conf)

    print("1 - Profile finished\n###################################################")
    print("2 - Starting fault injection\n###################################################")
    print("2 - {} faults will be injected".format(args.iterations))
    print("###################################################")
    ########################################################################
    # Injector setup
    # Get fault models
    fault_models = [int(i) for i in str(conf.get('DEFAULT', 'faultModel')).split(',')]

    # Csv log
    fieldnames = ['iteration', 'fault_model', 'thread_x', 'thread_y', 'thread_z',
                  'block_x', 'block_y', 'block_z', 'old_value', 'new_value', 'inj_mode',
                  'register', 'breakpoint_location', 'fault_successful',
                  'crash', 'sdc']

    ########################################################################
    # Fault injection
    iterations = args.iterations
    csv_file = conf.get("DEFAULT", "csvFile")

    # Creating a summary csv file
    summary_file = SummaryFile(filename=csv_file, fieldnames=fieldnames, mode='w')

    # Load information file generated in profiler step
    kernel_info_list = cf.load_file(cp.KERNEL_INFO_DIR)
    fault_injection_by_breakpoint(conf=conf, fault_models=fault_models, iterations=int(iterations),
                                  kernel_info_list=kernel_info_list, summary_file=summary_file,
                                  max_time=max_time_app, current_path=current_path)
    print("###################################################")
    print("2 - Fault injection finished, results can be found in {}".format(conf.get("DEFAULT", "csvFile")))
    print("###################################################")
    # Clear /tmp files generated
    os.system("rm -f /tmp/carol-fi-kernel-info.txt")
    os.system("rm -f " + cp.GOLD_OUTPUT_PATH)
    os.system("rm -f " + cp.GOLD_ERR_PATH)
    ########################################################################


########################################################################
#                                   Main                               #
########################################################################

if __name__ == "__main__":
    main()
