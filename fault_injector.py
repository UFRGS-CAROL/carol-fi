#!/usr/bin/python

from __future__ import print_function

import argparse
import glob
import os
import random
import re
import shutil
import time
import datetime
import signal
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will be at common_parameters module
import sys
from classes.RunGDB import RunGDB
from classes.SummaryFile import SummaryFile
from classes.Logging import Logging
from classes.SignalApp import SignalApp

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


"""
Check if app stops execution (otherwise kill it after a time)
"""


def check_finish(section, conf, logging, timestamp_start, end_time, p):
    is_hang = False

    # Wait maxWaitTimes the normal duration of the program before killing it
    max_wait_time = int(conf.get(section, "maxWaitTimes")) * end_time

    p_is_alive = p.is_alive()
    if cp.DEBUG:
        print("MAX_WAIT_TIME {}".format(max_wait_time))

    # Watchdog to avoid hangs
    now = int(time.time())
    diff_time = now - timestamp_start
    while diff_time < max_wait_time and p_is_alive:
        time.sleep(max_wait_time / cp.NUM_DIVISION_TIMES)
        p_is_alive = p.is_alive()
        now = int(time.time())
        diff_time = now - timestamp_start

    # Process finished ok
    if not p_is_alive:
        logging.debug("PROCESS NOT RUNNING")
        if cp.DEBUG:
            print("PROCESS NOT RUNNING")

    # check execution finished before or after waitTime
    if diff_time < max_wait_time:
        logging.info("Execution finished before waitTime. {} seconds.".format(diff_time))
    else:
        logging.info("Execution did not finish before waitTime {} seconds.".format(diff_time))
        is_hang = True

    logging.debug("now: {}".format(now))
    logging.debug("timestampStart: {}".format(timestamp_start))

    # Kill all the processes to make sure the machine is clean for another test
    cf.kill_all(conf=conf, logging=logging)

    return is_hang


"""
Copy the logs and output(if fault not masked) to a selected folder
"""


def save_output(is_sdc, is_hang, logging, unique_id, flip_log_file, output_file):
    # FI successful
    fi_injected = False
    if os.path.isfile(flip_log_file):
        fp = open(flip_log_file, "r")
        content = fp.read()
        if re.search('Fault Injection Successful', content):
            fi_injected = True
        fp.close()

    dt = datetime.datetime.fromtimestamp(time.time())
    ymd = dt.strftime('%Y_%m_%d')
    y_m_d_h_m_s = dt.strftime('%Y_%m_%d_%H_%M_%S')
    y_m_d_h_m_s = unique_id + "-" + y_m_d_h_m_s
    dir_d_t = os.path.join(ymd, y_m_d_h_m_s)

    # Log and create the paths
    if not fi_injected:
        cp_dir = os.path.join('logs', 'failed-injection', dir_d_t)
        logging.summary("Fault Injection Failed")
    elif is_hang:
        cp_dir = os.path.join('logs', 'hangs', dir_d_t)
        logging.summary("Hang")
    elif is_sdc:
        cp_dir = os.path.join('logs', 'sdcs', dir_d_t)
        logging.summary("SDC")
    elif not os.path.isfile(output_file):
        cp_dir = os.path.join('logs', 'no_output_generated', dir_d_t)
        logging.summary("no_output_generated")
    else:
        cp_dir = os.path.join('logs', 'masked', dir_d_t)
        logging.summary("Masked")

    if not os.path.isdir(cp_dir):
        os.makedirs(cp_dir)

    # Moving all necessary files
    for file_to_move in [flip_log_file, cp.INJ_OUTPUT_PATH,
                         cp.INJ_ERR_PATH, cp.DIFF_LOG, cp.DIFF_ERR_LOG, cp.SIGNAL_APP_LOG]:
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


def gen_env_string(bits_to_flip, fault_model, flip_log_file, gdb_init_strings, injection_mode):
    # Block and thread
    env_string = ",".join(str(i) for i in bits_to_flip)
    env_string += "|" + str(fault_model) + "|" + flip_log_file + "|" + gdb_init_strings + "|" + str(injection_mode)

    if cp.DEBUG:
        print("ENV STRING:{}".format(env_string))
    os.environ['CAROL_FI_INFO'] = env_string


"""
Function to run one execution of the fault injector
return old register value, new register value
"""


def gdb_inject_fault(**kwargs):
    # These are the mandatory parameters
    bits_to_flip = kwargs.get('bits_to_flip')
    fault_model = kwargs.get('fault_model')
    section = kwargs.get('section')
    unique_id = kwargs.get('unique_id')
    conf = kwargs.get('conf')
    max_time = float(kwargs.get('max_time'))

    # Logging file
    flip_log_file = cp.LOG_DEFAULT_NAME.format(unique_id)

    # Starting FI process
    if cp.DEBUG:
        print("STARTING GDB SCRIPT")

    logging = Logging(log_file=flip_log_file, unique_id=unique_id)
    logging.info("Starting GDB script")

    # Generate configuration file for specific test
    gen_env_string(gdb_init_strings=conf.get(section, "gdbInitStrings"),
                   bits_to_flip=bits_to_flip,
                   fault_model=fault_model,
                   flip_log_file=flip_log_file,
                   injection_mode=conf.get("DEFAULT", "injectionSite"))

    if cp.DEBUG:
        print("ENV GENERATE FINISHED")

    # Run pre execution function
    pre_execution(conf=conf, section=section)

    if cp.DEBUG:
        print("PRE EXECUTION")

    # First we have to start the SignalApp thread
    signal_app_thread = SignalApp(max_wait_time=max_time, signal_cmd=conf.get("DEFAULT", "signalCmd"),
                                  log_path=cp.SIGNAL_APP_LOG, unique_id=unique_id,
                                  signals_to_send=conf.get("DEFAULT", "seqSignals"))

    # Create one thread to start gdb script
    # Start fault injection process
    fi_process = RunGDB(unique_id=unique_id, gdb_exec_name=conf.get("DEFAULT", "gdbExecName"),
                        flip_script=cp.FLIP_SCRIPT)

    if cp.DEBUG:
        print("STARTING PROCESS")

    # Starting both threads
    fi_process.start()
    signal_app_thread.start()

    if cp.DEBUG:
        print("PROCESSES SPAWNED")

    # Start counting time
    timestamp_start = int(time.time())

    # Check if app stops execution (otherwise kill it after a time)
    is_hang = check_finish(section=section, conf=conf, logging=logging, timestamp_start=timestamp_start,
                           end_time=max_time, p=fi_process)
    if cp.DEBUG:
        print("FINISH CHECK OK")

    # finishing and removing thrash
    fi_process.join()
    # fi_process.terminate()
    signal_app_thread.join()

    # Get the signal init wait time before destroy the thread
    signal_init_wait_time = signal_app_thread.get_int_wait_time()

    del fi_process, signal_app_thread

    if cp.DEBUG:
        print("PROCESS JOINED")

    # Run pos execution function
    pos_execution(conf=conf, section=section)
    sdc_check_script = conf.get('DEFAULT', 'goldenCheckScript')
    #
    # # Check output files for SDCs
    is_sdc, is_crash = check_sdcs_and_app_crash(logging=logging, sdc_check_script=sdc_check_script)
    if cp.DEBUG:
        print("CHECK SDCs OK")

    # Search for set values for register
    # Must be done before save output
    # Was fault injected?
    block = thread = "___"
    try:
        old_value = re.findall("old_value:(\S+)", logging.search("old_value"))[0]
        new_value = re.findall("new_value:(\S+)", logging.search("new_value"))[0]

        block_focus = logging.search("CUDA_BLOCK_FOCUS")
        if block_focus:
            # Search for block
            m = re.search("CUDA_BLOCK_FOCUS:.*block.*\((\d+),(\d+),(\d+)\).*", block_focus)
            if m:
                block = "{}_{}_{}".format(m.group(1), m.group(2), m.group(3))

        thread_focus = logging.search("CUDA_BLOCK_FOCUS")
        if thread_focus:
            # Search for thread
            m = re.search("CUDA_THREAD_FOCUS:.*thread.*\((\d+),(\d+),(\d+)\).*", thread_focus)
            if m:
                thread = "{}_{}_{}".format(m.group(1), m.group(2), m.group(3))

        fi_successful = True
    except Exception as e:
        new_value = old_value = None
        fi_successful = False
        if cp.DEBUG:
            print("FAULT WAS NOT INJECTED. ERROR {}".format(e))
            print()

    # Copy output files to a folder
    save_output(is_sdc=is_sdc, is_hang=is_hang, logging=logging, unique_id=unique_id,
                flip_log_file=flip_log_file, output_file=cp.INJ_OUTPUT_PATH)

    if cp.DEBUG:
        print("SAVE OUTPUT AND RETURN")

    register = "R0"
    return register, old_value, new_value, fi_successful, is_hang, is_crash, is_sdc, signal_init_wait_time, block, thread


# TODO: REMOVE THIS FUNCTION


def only_for_radiation_benchs():
    list_of_files = glob.glob('/home/ffsantos/radiation-benchmarks/log/*.log')
    latest_file = max(list_of_files, key=os.path.getctime)
    return os.path.basename(latest_file)


"""
Randomly selects a thread, address and a bit location
to inject a fault.
"""


def gen_injection_location(injection_site, fault_model):
    # Randomly choose a place to inject a fault
    bits_to_flip = bit_flip_selection(fault_model=fault_model)

    # Select INST_OUT, INST_ADD, and RF
    # instruction output
    if injection_site == 'INST_OUT':
        raise NotImplementedError
    # instruction address
    elif injection_site == 'INST_ADD':
        raise NotImplementedError
    # Register file
    # elif injection_site == 'RF':
    #     valid_register = 'R' + str(random.randint(0, max_num_regs))

    return bits_to_flip


"""
This function will select the bits that will be flipped
if it is least significant bits it will reduce the starting bit range
"""


def bit_flip_selection(fault_model):
    # Randomly select (a) bit(s) to flip
    # Max double bit flip
    max_size_register_fault_model = cp.SINGLE_MAX_SIZE_REGISTER
    # Max size of bits to flip is 2, max double bit flip
    bits_to_flip = [0]

    # Single bit flip
    if fault_model == 0:
        bits_to_flip[0] = random.randint(0, max_size_register_fault_model - 1)

    # Double bit flip
    elif fault_model == 1:
        bits_to_flip = [0] * 2
        bits_to_flip[0] = random.randint(0, max_size_register_fault_model - 1)
        # Make sure that the same bit is not going to be selected
        r = range(0, bits_to_flip[0]) + range(bits_to_flip[0] + 1, max_size_register_fault_model)
        bits_to_flip[1] = random.choice(r)

    # Random value
    elif fault_model == 2:
        bits_to_flip[0] = str(hex(random.randint(0, cp.MAX_INT_32)))

    # Zero value
    elif fault_model == 3:
        bits_to_flip[0] = 0

    # Least 16 bits
    elif fault_model == 4:
        # max_size_register_fault_model = 32
        # bits_to_flip[0] = random.randint(16, max_size_register_fault_model - 1)
        bits_to_flip[0] = random.randint(0, 16)

    # Least 8 bits
    elif fault_model == 5:
        max_size_register_fault_model = 8
        bits_to_flip[0] = random.randint(0, max_size_register_fault_model - 1)

    return bits_to_flip


"""
This injector has two injection options
this function performs fault injection
by creating a breakpoint and steeping into it
"""


def fault_injection_by_breakpoint(conf, fault_models, iterations, kernel_info_dict, summary_file, current_path,
                                  host_thread):
    # kludge
    if conf.has_option("DEFAULT", "kludge"):
        kludge = conf.get("DEFAULT", "kludge")
    else:
        kludge = None

    # Execute the fault injector for each one of the sections(apps) of the configuration file
    for fault_model in fault_models:
        # Execute one fault injection for a specific app
        # For each kernel
        # for kernel_info_dict in kernel_info_list:
        num_rounds = 1
        while num_rounds <= iterations:
            # Generate an unique id for this fault injection
            # Thread is for multi gpu
            unique_id = "{}_{}_{}".format(num_rounds, fault_model, host_thread)
            bits_to_flip = gen_injection_location(injection_site=conf.get("DEFAULT", "injectionSite"),
                                                  fault_model=fault_model)

            # max time that app can run
            max_time = kernel_info_dict["max_time"]

            # inject one fault with an specified fault model, in a specific
            # thread, in a bit flip pattern
            fi_tic = int(time.time())
            register, old_val, new_val, fault_injected, hang, crash, sdc, signal_init_time, block, thread = gdb_inject_fault(
                section="DEFAULT",
                conf=conf,
                unique_id=unique_id,
                bits_to_flip=bits_to_flip,
                fault_model=fault_model,
                max_time=max_time,
                current_path=current_path,
                kludge=kludge)

            # Time toc
            fi_toc = int(time.time())

            # FI injection time
            injection_time = fi_toc - fi_tic

            if fault_injected:
                # 'iteration', 'fault_model', 'thread_x', 'thread_y', 'thread_z',
                # 'block_x', 'block_y', 'block_z', 'old_value', 'new_value', 'inj_mode',
                # 'register', 'breakpoint_location', 'fault_successful',
                # 'crash', 'sdc', 'time', 'inj_time_location', 'bits_to_flip', 'log_file'
                # Write a row to summary file
                row = [num_rounds, fault_model, thread, block, old_val, new_val, 0, register,
                       fault_injected, hang, crash, sdc, injection_time,
                       signal_init_time, bits_to_flip, only_for_radiation_benchs()]
                print(row)
                summary_file.write_row(row=row)
                num_rounds += 1


"""
Main function
"""


def main():
    global kill_strings
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
    # Connect signal SIGINT to stop application
    kill_strings = conf.get("DEFAULT", "killStrs")
    signal.signal(signal.SIGINT, signal_handler)

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
                  'register', 'fault_successful', 'hang',
                  'crash', 'sdc', 'time', 'inj_time_location', 'bits_flipped', 'log_file']

    ########################################################################
    # Fault injection
    iterations = args.iterations
    csv_file = conf.get("DEFAULT", "csvFile")

    # Creating a summary csv file
    summary_file = SummaryFile(filename=csv_file, fieldnames=fieldnames, mode='w')

    fault_injection_by_breakpoint(conf=conf, fault_models=fault_models, iterations=int(iterations),
                                  kernel_info_dict=cf.load_file(cp.KERNEL_INFO_DIR), summary_file=summary_file,
                                  current_path=current_path, host_thread=0)
    print("###################################################")
    print("2 - Fault injection finished, results can be found in {}".format(conf.get("DEFAULT", "csvFile")))
    print("###################################################")
    ########################################################################


########################################################################
#                                   Main                               #
########################################################################

if __name__ == "__main__":
    main()
