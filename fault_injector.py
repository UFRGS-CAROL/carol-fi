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
# from threading import Thread
from multiprocessing import Process

from classes.RunGDB import RunGDB
from classes.SummaryFile import SummaryFile
from classes.Logging import Logging
from classes.SignalApp import SignalApp

created_threads = []

"""
CTRL + C event
"""


def signal_handler(sig, frame):
    global kill_strings, current_path
    print("\n\tKeyboardInterrupt detected, exiting gracefully!( at least trying :) )")
    kill_cmds = kill_strings.split(";")
    for cmd in kill_cmds:
        try:
            os.system(cmd)
        except Exception as err:
            print("Command err: {}".format(str(err)))

    # os.system("rm -f {}/bin/*".format(current_path))

    sys.exit(0)


"""
Check if app stops execution (otherwise kill it after a time)
"""


def check_finish(max_wait_time, logging, timestamp_start, process, thread, kill_string):
    is_hang = False

    # Wait maxWaitTimes the normal duration of the program before killing it
    # max_wait_time = int(conf.get(section, "maxWaitTimes")) * end_time
    sleep_time = max_wait_time / cp.NUM_DIVISION_TIMES
    if cp.DEBUG:
        print("MAX_WAIT_TIME {} CHECK FINISH SLEEP_TIME {}".format(max_wait_time, sleep_time))

    # Watchdog to avoid hangs
    p_is_alive = process.is_alive()
    now = int(time.time())
    diff_time = now - timestamp_start
    while diff_time < max_wait_time and p_is_alive:
        time.sleep(sleep_time)
        p_is_alive = process.is_alive()
        now = int(time.time())
        diff_time = now - timestamp_start

    # Process finished ok
    if not p_is_alive:
        logging.debug("PROCESS NOT RUNNING")
        if cp.DEBUG:
            print("PROCESS NOT RUNNING")

    # check execution finished before or after waitTime
    if diff_time < max_wait_time:
        logging.info("Execution on thread {} finished before waitTime. {} seconds.".format(thread, diff_time))
    else:
        logging.info("Execution on thread {} finished before waitTime. {} seconds.".format(thread, diff_time))
        is_hang = True

    logging.debug("now: {}".format(now))
    logging.debug("timestampStart: {}".format(timestamp_start))

    # Kill all the processes to make sure the machine is clean for another test
    cf.kill_all(kill_string=kill_string, logging=logging)

    # Also kill the subprocess
    process.kill_subprocess()

    return is_hang


"""
Copy the logs and output(if fault not masked) to a selected folder
"""


def save_output(is_sdc, is_hang, logging, unique_id, flip_log_file, inj_output_path,
                inj_err_path, diff_log_path, diff_err_path, signal_app_log_path):
    # FI successful
    fi_injected = False
    if os.path.isfile(flip_log_file):
        with open(flip_log_file, "r") as fp:
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
    elif not os.path.isfile(inj_output_path):
        cp_dir = os.path.join('logs', 'no_output_generated', dir_d_t)
        logging.summary("no_output_generated")
    else:
        cp_dir = os.path.join('logs', 'masked', dir_d_t)
        logging.summary("Masked")

    if not os.path.isdir(cp_dir):
        os.makedirs(cp_dir)

    # Moving all necessary files
    for file_to_move in [flip_log_file, inj_output_path,
                         inj_err_path, diff_log_path, diff_err_path, signal_app_log_path]:
        try:
            shutil.move(file_to_move, cp_dir)
        except Exception as err:
            if cp.DEBUG:
                print("ERROR ON MOVING {} -- {}".format(file_to_move, str(err)))


"""
Check output files for SDCs
"""


def check_sdcs_and_app_crash(logging, sdc_check_script, inj_output_path, inj_err_path, diff_log_path, diff_err_path):
    print(logging, sdc_check_script, inj_output_path, inj_err_path, diff_log_path, diff_err_path)
    is_sdc = False
    is_app_crash = False
    if not os.path.isfile(inj_output_path):
        logging.error("outputFile not found: " + inj_output_path)
        is_app_crash = True
    elif not os.path.isfile(cp.GOLD_OUTPUT_PATH):
        logging.error("gold_file not found: " + cp.GOLD_OUTPUT_PATH)
        raise ValueError("GOLD FILE NOT FOUND")
    elif not os.path.isfile(sdc_check_script):
        logging.error("sdc check script file not found: " + sdc_check_script)
        raise ValueError("SDC CHECK SCRIPT NOT FOUND")
    elif not os.path.isfile(inj_err_path):
        logging.error("possible crash, stderr not found: " + inj_output_path)
        is_app_crash = True
    elif not os.path.isfile(cp.GOLD_ERR_PATH):
        logging.error("gold_err_file not found: " + cp.GOLD_ERR_PATH)
        raise ValueError("GOLD ERR FILE NOT FOUND")
    if os.path.isfile(cp.GOLD_OUTPUT_PATH) and os.path.isfile(inj_output_path) and os.path.isfile(
            cp.GOLD_ERR_PATH) and os.path.isfile(inj_err_path):
        # Set environ variables for sdc_check_script
        os.environ['GOLD_OUTPUT_PATH'] = cp.GOLD_OUTPUT_PATH
        os.environ['INJ_OUTPUT_PATH'] = inj_output_path
        os.environ['GOLD_ERR_PATH'] = cp.GOLD_ERR_PATH
        os.environ['INJ_ERR_PATH'] = inj_err_path
        os.environ['DIFF_LOG'] = diff_log_path
        os.environ['DIFF_ERR_LOG'] = diff_err_path
        os.system("sh " + sdc_check_script)

        # Test if files are ok
        with open(diff_log_path, 'r') as fi:
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

        with open(diff_err_path, 'r') as fi_err:
            err_lines = fi_err.readlines()
            if len(err_lines) != 0:
                is_app_crash = True

    return is_sdc, is_app_crash


"""
Function to run one execution of the fault injector
return old register value, new register value
"""


def gdb_inject_fault(**kwargs):
    global kill_strings
    # These are the mandatory parameters
    bits_to_flip = kwargs.get('bits_to_flip')
    fault_model = kwargs.get('fault_model')
    unique_id = kwargs.get('unique_id')
    max_time = kwargs.get('max_time')
    current_path_local = kwargs.get('current_path')

    # injection site
    injection_site = kwargs.get('injection_site')
    benchmark_args = kwargs.get('benchmark_args')
    benchmark_binary = kwargs.get('benchmark_binary')
    host_thread = kwargs.get('host_thread')
    seq_signals = kwargs.get('seq_signals')
    init_sleep = kwargs.get('init_sleep')
    sdc_check_script = kwargs.get('gold_check_script')

    # signalCmd
    signal_cmd = kwargs.get("signal_cmd")
    gdb_exec_name = kwargs.get('gdb_path')

    # Define all path to current thread execution
    # Logging file
    flip_log_file = cp.LOG_DEFAULT_NAME.format(unique_id)
    inj_output_path = cp.INJ_OUTPUT_PATH.format(unique_id)
    inj_err_path = cp.INJ_ERR_PATH.format(unique_id)
    signal_app_log = cp.SIGNAL_APP_LOG.format(unique_id)
    diff_log_path = cp.DIFF_LOG.format(unique_id)
    diff_err_path = cp.DIFF_ERR_LOG.format(unique_id)

    # Starting FI process
    if cp.DEBUG:
        print("STARTING GDB SCRIPT")

    logging = Logging(log_file=flip_log_file, unique_id=unique_id)
    logging.info("Starting GDB script")

    # Generate configuration file for specific test
    gdb_env_string = "{}|{}|{}|file {}; set args {}|{}|{}".format(",".join(str(i) for i in bits_to_flip), fault_model,
                                                                  flip_log_file, benchmark_binary, benchmark_args,
                                                                  injection_site, host_thread)

    if cp.DEBUG:
        print("ENV GENERATE FINISHED")

    # First we have to start the SignalApp thread
    signal_app_thread = SignalApp(max_wait_time=max_time, signal_cmd=signal_cmd,
                                  log_path=signal_app_log, unique_id=unique_id,
                                  signals_to_send=seq_signals,
                                  init_sleep=init_sleep)

    # Create one thread to start gdb script
    # Start fault injection process
    fi_process = RunGDB(unique_id=unique_id, gdb_exec_name=gdb_exec_name, flip_script=cp.FLIP_SCRIPT,
                        carol_fi_base_path=current_path_local, gdb_env_string=gdb_env_string, gpu_to_execute=host_thread,
                        inj_output_path=inj_output_path, inj_err_path=inj_err_path)

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
    # max_wait_time, logging, timestamp_start, thread, kill_string
    is_hang = check_finish(max_wait_time=max_time, logging=logging, timestamp_start=timestamp_start,
                           process=fi_process, thread=host_thread,
                           kill_string=kill_strings)
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

    # # Check output files for SDCs
    is_sdc, is_crash = check_sdcs_and_app_crash(logging=logging, sdc_check_script=sdc_check_script,
                                                inj_output_path=inj_output_path, inj_err_path=inj_err_path,
                                                diff_log_path=diff_log_path, diff_err_path=diff_err_path)
    if cp.DEBUG:
        print("CHECK SDCs OK")

    # Search for set values for register
    # Must be done before save output
    # Was fault injected?
    kernel = register = block = thread = "___"
    try:
        old_value = re.findall("old_value:(\S+)", logging.search("old_value"))[0]
        new_value = re.findall("new_value:(\S+)", logging.search("new_value"))[0]

        block_focus = logging.search("CUDA_BLOCK_FOCUS")
        if block_focus:
            # Search for block
            m = re.search("CUDA_BLOCK_FOCUS:.*block[ ]+\((\d+),(\d+),(\d+)\).*", block_focus)
            if m:
                block = "{}_{}_{}".format(m.group(1), m.group(2), m.group(3))

        thread_focus = logging.search("CUDA_THREAD_FOCUS")
        if thread_focus:
            # Search for thread
            m = re.search("CUDA_THREAD_FOCUS:.*thread[ ]+\((\d+),(\d+),(\d+)\).*", thread_focus)
            if m:
                thread = "{}_{}_{}".format(m.group(1), m.group(2), m.group(3))

        register_selected = logging.search("SELECTED_REGISTER")
        if register_selected:
            m = re.search("SELECTED_REGISTER:(\S+).*", register_selected)
            if m:
                register = m.group(1)

        kernel_selected = logging.search("SELECTED_KERNEL")
        if kernel_selected:
            m = re.search("SELECTED_KERNEL:(\S+).*", kernel_selected)
            if m:
                kernel = m.group(1)

        fi_successful = True
    except Exception as e:
        new_value = old_value = None
        fi_successful = False
        if cp.DEBUG:
            print("FAULT WAS NOT INJECTED. ERROR {}".format(e))
            print()

    # Copy output files to a folder
    save_output(is_sdc=is_sdc, is_hang=is_hang, logging=logging, unique_id=unique_id,
                flip_log_file=flip_log_file, inj_output_path=inj_output_path, inj_err_path=inj_err_path,
                diff_log_path=diff_log_path, diff_err_path=diff_err_path, signal_app_log_path=signal_app_log)

    if cp.DEBUG:
        print("SAVE OUTPUT AND RETURN")

    return_list = [kernel, register, old_value, new_value, fi_successful,
                   is_hang, is_crash, is_sdc, signal_init_wait_time, block, thread]
    return return_list


# TODO: REMOVE THIS FUNCTION


def only_for_radiation_benchs():
    list_of_files = glob.glob('/home/carol/radiation-benchmarks/log/*.log')
    latest_file = max(list_of_files, key=os.path.getctime)
    return os.path.basename(latest_file)


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


def fault_injection_by_breakpoint(**kwargs):
    # Global rows list
    global summary_file_rows
    benchmark_binary = kwargs.get('benchmark_binary')
    kwargs['signal_cmd'] = "killall -2 {}".format(os.path.basename(benchmark_binary))
    fault_models = kwargs.get('fault_models')
    iterations = kwargs.get('iterations')
    host_thread = kwargs.get('host_thread')
    injection_site = kwargs.get('injection_site')

    # Execute the fault injector for each one of the sections(apps) of the configuration file
    for fault_model in fault_models:
        # Execute iterations number of fault injection for a specific app
        num_rounds = 1
        while num_rounds <= iterations:
            # Generate an unique id for this fault injection
            # Thread is for multi gpu
            kwargs['unique_id'] = "{}_{}_{}".format(num_rounds, fault_model, host_thread)
            kwargs['bits_to_flip'] = bit_flip_selection(fault_model=fault_model)
            kwargs['fault_model'] = fault_model

            fi_tic = int(time.time())
            ret = gdb_inject_fault(**kwargs)
            kernel, register, old_val, new_val, fault_injected, hang, crash, sdc, signal_init_time, block, thread = ret
            # Time toc
            fi_toc = int(time.time())

            # FI injection time
            injection_time = fi_toc - fi_tic

            if fault_injected:
                summary_file_rows.append(
                    [kwargs['unique_id'], kernel, register, num_rounds, fault_model, thread,
                     block, old_val, new_val, injection_site,
                     fault_injected, hang, crash, sdc, injection_time,
                     signal_init_time, kwargs['bits_to_flip'], only_for_radiation_benchs()])

            num_rounds += 1


"""
Main function
"""


def main():
    global kill_strings, summary_file_rows, current_path
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="config_file", help='Configuration file', required=True)
    parser.add_argument('-i', '--iter', dest="iterations",
                        help='How many times to repeat the programs in the configuration file', required=True, type=int)

    parser.add_argument('-n', '--n_gpus', dest="n_gpus", help="The number of available GPUs to perform FI."
                                                              " Default is 1.", required=False, default=1, type=int)

    args = parser.parse_args()
    if args.iterations < 1:
        parser.error('Iterations must be greater than zero')

    # Start with a different seed every time to vary the random numbers generated
    # the seed will be the current number of second since 01/01/70
    random.seed()

    # Read the configuration file with data for all the apps that will be executed
    conf = cf.load_config_file(args.config_file)
    # Connect signal SIGINT to stop application
    kill_strings = ""
    signal.signal(signal.SIGINT, signal_handler)

    # First set env vars
    current_path = cf.set_python_env()

    print("2 - Starting fault injection")
    print("###################################################")
    print("2 - {} faults will be injected".format(args.iterations))
    print("###################################################")
    ########################################################################
    summary_file_rows = []

    # Define the number of threads tha will execute
    num_gpus = args.n_gpus
    iterations = args.iterations
    if args.n_gpus > args.iterations:
        num_gpus = args.iterations

    os.system('mkdir -p {}/bin'.format(current_path))
    # Set binaries for the injection
    benchmark_binary_default = conf.get('DEFAULT', 'benchmarkBinary')
    gdb_path_default = conf.get('DEFAULT', 'gdbExecName')

    each_thread_iterations = iterations / num_gpus

    gpus_threads = []
    kernel_info_dict = cf.load_file(cp.KERNEL_INFO_DIR)

    for thread_id in range(0, num_gpus):
        gdb = "{}/bin/{}_{}".format(current_path, os.path.basename(gdb_path_default), thread_id)
        benchmark_binary = "{}/bin/{}_{}".format(current_path, os.path.basename(benchmark_binary_default), thread_id)

        os.system("ln -s {} {}".format(gdb_path_default, gdb))
        os.system("ln -s {} {}".format(benchmark_binary_default, benchmark_binary))
        # These are the mandatory parameters
        kwargs = {
            'injection_site': conf.get('DEFAULT', 'injectionSite'),
            'fault_models': [int(i) for i in str(conf.get('DEFAULT', 'faultModel')).split(',')],
            'max_time': float(kernel_info_dict['max_time']) * float(conf.get('DEFAULT', 'maxWaitTimes')),
            'iterations': each_thread_iterations,
            'benchmark_binary': benchmark_binary,
            'benchmark_args': conf.get('DEFAULT', 'benchmarkArgs'),
            'host_thread': thread_id,
            'gdb_path': gdb,
            'current_path': current_path,
            'seq_signals': int(conf.get('DEFAULT', 'seqSignals')),
            'init_sleep': float(conf.get('DEFAULT', 'initSleep')),
            'gold_check_script': "{}/{}".format(current_path, conf.get('DEFAULT', 'goldenCheckScript'))
        }
        kill_strings += "killall -9 {};killall -9 {};".format(os.path.basename(benchmark_binary), os.path.basename(gdb))

        fi_master_thread = Process(target=fault_injection_by_breakpoint, kwargs=kwargs)
        gpus_threads.append(fi_master_thread)

    print(kill_strings)
    for thread in gpus_threads:
        thread.start()

    for thread in gpus_threads:
        thread.join()

    # Logging all results (DANGEROUS)
    # Creating a summary csv file
    csv_file = conf.get("DEFAULT", "csvFile")

    # Csv log
    fieldnames = ['kernel', 'register', 'iteration', 'fault_model', 'thread', 'block', 'old_value',
                  'new_value', 'inj_mode', 'fault_successful', 'hang', 'crash', 'sdc', 'time',
                  'inj_time_location', 'bits_flipped', 'log_file']
    summary_file = SummaryFile(filename=csv_file, fieldnames=fieldnames, mode='w')

    # Writing everything to file
    summary_file.write_rows(summary_file_rows)

    os.system("rm -f {}/bin/*".format(current_path))
    print("###################################################")
    print("2 - Fault injection finished, results can be found in {}".format(csv_file))
    print("###################################################")
    ########################################################################


########################################################################
#                                   Main                               #
########################################################################

summary_file_rows = None
kill_strings = None
current_path = None
if __name__ == "__main__":
    main()
