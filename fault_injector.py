#!/usr/bin/python

from __future__ import print_function

import argparse
import os
import random
import re
import shutil
import time
import datetime
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will be at common_parameters module

from classes.RunGDB import RunGDB
from classes.SummaryFile import SummaryFile
from classes.Logging import Logging
from classes.SignalApp import SignalApp

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
                   breakpoint_location, flip_log_file, gdb_init_strings, kludge):
    # Block and thread
    env_string = ",".join(str(i) for i in valid_block) + "|" + ",".join(str(i) for i in valid_thread)
    env_string += "|" + valid_register + "|" + ",".join(str(i) for i in bits_to_flip)
    env_string += "|" + str(fault_model) + "|" + breakpoint_location
    env_string += "|" + flip_log_file + "|" + gdb_init_strings + "|" + str(kludge)

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

    # Logging file
    flip_log_file = "/tmp/carolfi-flipvalue-{}.log".format(unique_id)

    # Starting FI process
    if cp.DEBUG:
        print("STARTING GDB SCRIPT")

    logging = Logging(log_file=flip_log_file, unique_id=unique_id)
    logging.info("Starting GDB script")

    # Generate configuration file for specific test
    gen_env_string(gdb_init_strings=conf.get(section, "gdbInitStrings"),
                   valid_block=valid_block,
                   valid_thread=valid_thread,
                   valid_register=valid_register,
                   bits_to_flip=bits_to_flip,
                   fault_model=fault_model,
                   breakpoint_location=breakpoint_location,
                   flip_log_file=flip_log_file,
                   kludge=kludge)

    if cp.DEBUG:
        print("ENV GENERATE FINISHED")

    # Run pre execution function
    pre_execution(conf=conf, section=section)

    if cp.DEBUG:
        print("PRE EXECUTION")

    # First we have to start the SignalApp thread
    signal_app_thread = SignalApp(max_wait_time=max_time, signal_cmd=conf.get("DEFAULT", "signalCmd"),
                                  log_path=cp.SIGNAL_APP_LOG, unique_id=unique_id)

    # Create one thread to start gdb script
    # Start fault injection process
    fi_process = RunGDB(unique_id=unique_id, gdb_exec_name=conf.get("DEFAULT", "gdbExecName"),
                        flip_script=cp.FLIP_SCRIPT)

    # sdc, crash or hang
    is_sdc, is_hang, is_crash = False, False, False

    if cp.DEBUG:
        print("STARTING PROCESS")

    # Starting both threads
    fi_process.start()
    signal_app_thread.start()

    if cp.DEBUG:
        print("PROCESS SPAWNED")
    # Start counting time
    # timestamp_start = int(time.time())

    # Check if app stops execution (otherwise kill it after a time)
    # is_hang = check_finish(section=section, conf=conf, logging=logging, timestamp_start=timestamp_start,
    #                        end_time=max_time, p=fi_process)
    # if cp.DEBUG:
    #     print("FINISH CHECK OK")
    #
    # # Run pos execution function
    # pos_execution(conf=conf, section=section)
    # sdc_check_script = conf.get('DEFAULT', 'goldenCheckScript')
    #
    # # Check output files for SDCs
    # is_sdc, is_app_crash = check_sdcs_and_app_crash(logging=logging, sdc_check_script=sdc_check_script)
    # if cp.DEBUG:
    #     print("CHECK SDCs OK")

    # remove thrash
    signal_app_thread.join()
    fi_process.join()
    del fi_process, signal_app_thread

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
    # save_output(
    #     section=section, is_sdc=is_sdc, is_hang=(is_hang or is_app_crash), logging=logging, unique_id=unique_id,
    #     flip_log_file=flip_log_file, output_file=cp.INJ_OUTPUT_PATH)

    cf.kill_all(conf=conf)
    if cp.DEBUG:
        print("SAVE OUTPUT AND RETURN")

    return reg_old_value, reg_new_value, fault_successful, is_hang, is_crash, is_sdc


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

    return valid_thread, valid_block, valid_register, bits_to_flip


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


def fault_injection_by_breakpoint(conf, fault_models, iterations, kernel_info_list, summary_file, current_path):
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
                thread, block, register, bits_to_flip = gen_injection_location(
                    kernel_info_dict=kernel_info_dict, max_num_regs=int(conf.get("DEFAULT", "maxNumRegs")),
                    injection_site=conf.get("DEFAULT", "injectionSite"), fault_model=fault_model)

                # Selects the random line to inject
                kernel_begin = kernel_info_dict["kernel_line"]
                kernel_end = kernel_info_dict["kernel_end_line"]
                rand_line = random.randint(int(kernel_begin), int(kernel_end))
                break_line = str(kernel_info_dict["kernel_name"] + ":"
                                 + str(rand_line))

                # max time that app can run
                max_time = kernel_info_dict["max_time"]

                old_val, new_val, fault_injected, hang, crash, sdc = run_gdb_fault_injection(section="DEFAULT",
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
                                                                                             kludge=kludge)
                # Write a row to summary file
                row = [num_rounds, fault_model]
                row.extend(thread)
                row.extend(block)
                row.extend(
                    [old_val, new_val, 0, register, break_line, fault_injected,
                     hang,
                     sdc])
                print(row)
                summary_file.write_row(row=row)
                time.sleep(2)
                # except Exception as err:
                #     if cp.DEBUG:
                #         print("\nERROR ON BREAK POINT MODE: Fault was not injected, {}".format(str(err)))
                #     raise


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
    current_path = cf.set_python_env()

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
                                  current_path=current_path)
    print("###################################################")
    print("2 - Fault injection finished, results can be found in {}".format(conf.get("DEFAULT", "csvFile")))
    print("###################################################")
    ########################################################################


########################################################################
#                                   Main                               #
########################################################################

if __name__ == "__main__":
    main()
