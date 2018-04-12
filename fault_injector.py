#!/usr/bin/python

from __future__ import print_function

import os
import time
import datetime
import random
import subprocess
import multiprocessing
import threading
import re
import shutil
import argparse
import csv

import common_functions as cf
import common_parameters as cp

"""
Run some command and return the output
"""


def run_command(command):
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    return out, err


"""
Class RunGdb: necessary to run gdb while
the main thread register the time
If RunGdb execution time > max timeout allowed
this thread will be killed
"""


class RunGDB(multiprocessing.Process):
    def __init__(self, unique_id, gdb_exec_name, flip_script, current_dir):
        # multiprocessing.Process.__init__(self)
        super(RunGDB, self).__init__()
        self.__gdb_exe_name = gdb_exec_name
        self.__flip_script = flip_script
        self.__unique_id = unique_id
        self.__current_dir = current_dir

    def run(self):
        if cp.DEBUG:
            print("GDB Thread run, section and id: ", self.__unique_id)
        # os.environ['CUDA_DEVICE_WAITS_ON_EXCEPTION'] = '1'
        # os.environ['GDB_EXE'] = self.__gdb_exe_name
        # os.environ['GDB_CAROLFI_FLAGS'] = '-n -batch -x'
        # os.environ['PYTHON_SCRIPT'] = self.__flip_script
        start_cmd = 'env CUDA_DEVICE_WAITS_ON_EXCEPTION=1 ' + self.__gdb_exe_name
        start_cmd += ' -n -batch -x ' + self.__flip_script
        stdout, stderr = run_command([start_cmd])
        with open(cp.INJ_OUTPUT_PATH, 'w') as fout:
            fout.write(stdout)
        with open(cp.INJ_ERR_PATH, 'w') as ferr:
            if stderr:
                ferr.write(stderr)
            else:
                ferr.write("")

"""
Signal the app to stop so GDB can execute the script to flip a value
"""


class SignalApp(threading.Thread):
    def __init__(self, signal_cmd, max_wait_time, init, end, seq_signals, logging, threads_num):
        threading.Thread.__init__(self)
        self.__signal_cmd = signal_cmd
        self.__max_wait_time = max_wait_time
        self.__init = init
        self.__end = end
        self.__seq_signals = seq_signals
        self.__logging = logging
        # It is for each thread wait similar time
        self.__max_sleep_time = end / threads_num

    def run(self):
        for i in range(0, self.__seq_signals):
            time.sleep(self.__max_sleep_time)
            proc = subprocess.Popen(self.__signal_cmd, stdout=subprocess.PIPE, shell=True)
            (out, err) = proc.communicate()
            if out is not None:
                self.__logging.info("shell stdout: " + str(out))
            if err is not None:
                self.__logging.error("shell stderr: " + str(err))

                # # Sleep to avoid lots of signals
                # time.sleep(0.01)


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


def finish(section, conf, logging, timestamp_start, end_time, p):
    is_hang = False
    now = int(time.time())

    # Wait maxWaitTimes the normal duration of the program before killing it
    max_wait_time = int(conf.get(section, "maxWaitTimes")) * end_time
    kill_strs = conf.get(section, "killStrs")  # + ";" + "kill -9 " + str(pid)

    p_is_alive = p.is_alive()
    while (now - timestamp_start) < max_wait_time and p_is_alive:
        time.sleep(max_wait_time / 10.0)
        now = int(time.time())
        p_is_alive = p.is_alive()
        if not p_is_alive:
            logging.debug("Process not running")
            # print("Pid existence", p_is_alive, "now - timestamp", now - timestamp_start)

    # check execution finished before or after waitTime
    if (now - timestamp_start) < max_wait_time:
        logging.info("Execution finished before waitTime")
    else:
        logging.info("Execution did not finish before waitTime")
        is_hang = True
        p.terminate()

    logging.debug("now: " + str(now))
    logging.debug("timestampStart: " + str(timestamp_start))

    # Kill all the processes to make sure the machine is clean for another test
    for k in kill_strs.split(";"):
        proc = subprocess.Popen(k, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()
        logging.debug("kill cmd: " + k)
        if out is not None:
            logging.debug("kill cmd, shell stdout: " + str(out))
        if err is not None:
            logging.error("kill cmd, shell stderr: " + str(err))

    return is_hang


"""
Copy the logs and output(if fault not masked) to a selected folder
"""


def save_output(section, is_sdc, is_hang, logging, unique_id, flip_log_file, output_file):
    # FI successful
    fi_succ = False
    if os.path.isfile(flip_log_file):
        fp = open(flip_log_file, "r")
        content = fp.read()
        if re.search("Fault Injection Successful", content):
            fi_succ = True
        fp.close()

    dt = datetime.datetime.fromtimestamp(time.time())
    ymd = dt.strftime('%Y_%m_%d')
    ymdhms = dt.strftime('%Y_%m_%d_%H_%M_%S')
    ymdhms = unique_id + "-" + ymdhms
    dir_d_t = os.path.join(ymd, ymdhms)
    masked = False
    if not fi_succ:
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
        masked = True

    if not os.path.isdir(cp_dir):
        os.makedirs(cp_dir)

    shutil.move(flip_log_file, cp_dir)
    # if os.path.isfile(output_file) and (not masked) and fi_succ:
    shutil.move(cp.INJ_OUTPUT_PATH, cp_dir)
    shutil.move(cp.INJ_ERR_PATH, cp_dir)
    shutil.move(cp.DIFF_LOG, cp_dir)


"""
Pre execution commands
"""


def pre_execution(conf, section):
    try:
        script = conf.get(section, "preExecScript")
        if script != "":
            os.system(script)
        return
    except:
        return


"""
Pos execution commands
"""


def pos_execution(conf, section):
    try:
        script = conf.get(section, "posExecScript")
        if script != "":
            os.system(script)
        return
    except:
        return


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
                for signal in cp.SIGNALS:
                    for line in out_lines:
                        if signal in line:
                            is_app_crash = True
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
                   injection_site, breakpoint_location, flip_log_file, debug, gdb_init_strings, inj_type):
    # Block and thread
    env_string = ",".join(str(i) for i in valid_block) + "|" + ",".join(str(i) for i in valid_thread)
    env_string += "|" + valid_register + "|" + ",".join(str(i) for i in bits_to_flip)
    env_string += "|" + str(fault_model) + "|" + injection_site + "|" + breakpoint_location
    env_string += "|" + flip_log_file + "|" + str(debug) + "|" + gdb_init_strings + "|" + inj_type

    os.environ['CAROL_FI_INFO'] = env_string


"""
Function to run one execution of the fault injector
return old register value, new register value
"""


def run_gdb_fault_injection(**kwargs):
    valid_block, valid_thread, injection_address, breakpoint_location = list(), list(), '', ''

    # Declare all FI threads
    # thread_signal_list = []

    # This are the mandatory parameters
    inj_mode = kwargs.get('inj_mode')
    bits_to_flip = kwargs.get('bits_to_flip')
    fault_model = kwargs.get('fault_model')
    section = kwargs.get('section')
    unique_id = kwargs.get('unique_id')
    valid_register = kwargs.get('valid_register')
    conf = kwargs.get('conf')
    # max_wait_times = int(conf.get("DEFAULT", "maxWaitTimes"))
    # init_signal = 0.0
    end_signal = float(kwargs.get('max_time'))

    # SDC check parameters
    current_path = kwargs.get('current_path')

    # Logging file
    flip_log_file = "/tmp/carolfi-flipvalue-" + unique_id + ".log"
    logging = cf.Logging(log_file=flip_log_file, debug=conf.get("DEFAULT", "debug"), unique_id=unique_id)
    logging.info("Starting GDB script")

    # Parameters only for break mode
    if inj_mode == 'break':
        valid_block = kwargs.get('valid_block')
        valid_thread = kwargs.get('valid_thread')
        injection_address = kwargs.get('injection_address')
        breakpoint_location = kwargs.get('breakpoint_location')

    # elif inj_mode == 'signal':
    #     signal_cmd = conf.get("DEFAULT", "signalCmd")
    #     seq_signals = int(conf.get("DEFAULT", "seqSignals"))
    #     max_thread_fi = int(conf.get("DEFAULT", "numThreadsFI"))
    #     max_wait_time = end_signal * max_wait_times
    #
    #     for i in range(0, max_thread_fi):
    #         thread_signal_list.append(SignalApp(signal_cmd=signal_cmd, max_wait_time=max_wait_time,
    #                                             init=init_signal, end=end_signal, seq_signals=seq_signals,
    #                                             logging=logging, threads_num=max_thread_fi))

    # Generate configuration file for specific test
    gen_env_string(gdb_init_strings=conf.get(section, "gdbInitStrings"),
                   debug=conf.get(section, "debug"),
                   valid_block=valid_block,
                   valid_thread=valid_thread,
                   valid_register=valid_register,
                   bits_to_flip=bits_to_flip,
                   fault_model=fault_model,
                   injection_site=injection_address,
                   breakpoint_location=breakpoint_location,
                   flip_log_file=flip_log_file, inj_type=inj_mode)

    # Run pre execution function
    pre_execution(conf=conf, section=section)

    # Create one thread to start gdb script
    # Start fault injection process
    fi_process = RunGDB(unique_id=unique_id, gdb_exec_name=conf.get("DEFAULT", "gdbExecName"),
                        flip_script=cp.FLIP_SCRIPT, current_dir=current_path)
    fi_process.daemon = True
    fi_process.start()

    # Start counting time
    timestamp_start = int(time.time())

    # Start signal fault injection threads, if this mode was selected
    # for t in thread_signal_list:
    #     t.start()

    # Check if app stops execution (otherwise kill it after a time)
    is_hang = finish(section=section, conf=conf, logging=logging, timestamp_start=timestamp_start,
                     end_time=end_signal, p=fi_process)

    # Make sure process finish before trying to execute again
    fi_process.join()

    # Run pos execution function
    pos_execution(conf=conf, section=section)
    sdc_check_script = current_path + '/' + conf.get('DEFAULT', 'goldenCheckScript')

    # Check output files for SDCs
    is_sdc, is_app_crash = check_sdcs_and_app_crash(logging=logging, sdc_check_script=sdc_check_script)

    # remove thrash
    del fi_process
    # Also signal ones
    # for t in thread_signal_list:
    #     t.join()
    # del thread_signal_list

    # Search for set values for register
    # Must be done before save output
    # Was fault injected?
    try:
        reg_old_value = logging.search("reg_old_value")
        reg_new_value = logging.search("reg_new_value")
        reg_old_value = re.findall("reg_old_value: (\S+)", reg_old_value)[0]
        reg_new_value = re.findall('reg_new_value: (\S+)', reg_new_value)[0]
        fault_successful = True
    except Exception as e:
        reg_new_value = reg_old_value = ''
        fault_successful = False

    # Copy output files to a folder
    save_output(
        section=section, is_sdc=is_sdc, is_hang=(is_hang or is_app_crash), logging=logging, unique_id=unique_id,
        flip_log_file=flip_log_file, output_file=cp.INJ_OUTPUT_PATH)

    return reg_old_value, reg_new_value, fault_successful, is_hang, is_sdc


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
Select a valid stop address
from the file created in the profiler
step
"""


def get_valid_address(addresses):
    m = registers = instruction = address = byte_location = instruction_line = None

    # search for a valid instruction
    while not m:
        element = random.randrange(2, len(addresses) - 1)
        instruction_line = addresses[element]

        registers, address, byte_location, instruction, m = parse_line(instruction_line)

        if cp.DEBUG:
            if not m:
                print("it is stopped here:", instruction_line)
            else:
                print("it choose something:", instruction_line)

    return registers, instruction, address, byte_location, instruction_line


"""
Selects a valid thread for a specific
kernel
return the coordinates for the block
and the thread
"""


def get_valid_thread(threads):
    element = random.randrange(2, len(threads) - 4)
    #  (15,2,0) (31,12,0)    (15,2,0) (31,31,0)    20 0x0000000000b41a28 matrixMul.cu    47
    splited = threads[element].replace("\n", "").split()

    # randomly chosen first block and thread
    block = re.match(".*\((\d+),(\d+),(\d+)\).*", splited[0])
    thread = re.match(".*\((\d+),(\d+),(\d+)\).*", splited[1])

    try:
        block_x = block.group(1)
        block_y = block.group(2)
        block_z = block.group(3)

        thread_x = thread.group(1)
        thread_y = thread.group(2)
        thread_z = thread.group(3)
    except:
        raise ValueError

    return [block_x, block_y, block_z], [thread_x, thread_y, thread_z]


"""
Randomly selects a thread, address and a bit location
to inject a fault.
"""


def gen_injection_location(kernel_info_dict, max_num_regs, injection_site):
    # A valid block is a [block_x, block_y, block_z] coordinate
    # A valid thread is a [thread_x, thread_y, thread_z] coordinate
    valid_block, valid_thread = get_valid_thread(kernel_info_dict["threads"])

    # A injection site is a list of [registers, instruction, address, byte_location]
    registers, _, address, _, instrution_line = get_valid_address(kernel_info_dict["addresses"])

    # Randomly select (a) bit(s) to flip
    # Max double bit flip
    bits_to_flip = [0] * 2
    bits_to_flip[0] = random.randint(0, cp.MAX_SIZE_REGISTER - 1)

    # Selects it it is in the instruction output
    # or register file
    valid_register = None
    if injection_site == 'INST_OUT':
        for i in reversed(registers):
            if 'R' in i:
                valid_register = i
                break
        valid_register = valid_register.replace("[", "").replace("]", "").replace("-", "")
        # Avoid cases like this: MOV R3, 0x2
        if valid_register is None:
            raise NotImplementedError("LINE COULD NOT BE PARSED")

    # Register file
    elif injection_site == 'RF':
        valid_register = 'R' + str(random.randint(0, max_num_regs))

    # Make sure that the same bit is not going to be selected
    r = range(0, bits_to_flip[0]) + range(bits_to_flip[0] + 1, cp.MAX_SIZE_REGISTER)
    bits_to_flip[1] = random.choice(r)

    return valid_thread, valid_block, valid_register, bits_to_flip, address, instrution_line


"""
This injector has two injection options
this function performs fault injection
by sending a OS signal to the application
"""

#
# def fault_injection_by_signal(conf, fault_models, inj_type, iterations, summary_file, max_time):
#     for num_rounds in range(iterations):
#         # Execute the fault injector for each one of the sections(apps) of the configuration file
#         for fault_model in fault_models:
#             unique_id = str(num_rounds) + "_" + str(inj_type) + "_" + str(fault_model)
#             r_old_val, r_new_val, fault_succ, hang, sdc = run_gdb_fault_injection(unique_id=unique_id,
#                                                                                   inj_mode='signal',
#                                                                                   fault_model=fault_model,
#                                                                                   section="DEFAULT",
#                                                                                   valid_register="R30", conf=conf,
#                                                                                   bits_to_flip=[31, 2],
#                                                                                   max_time=max_time)
#             # Write a row to summary file
#             row = [unique_id, num_rounds, fault_model]
#             row.extend([None, None, None])
#             row.extend([None, None, None])
#             row.extend(
#                 [r_old_val, r_new_val, 0, "", "", "", fault_succ])
#             summary_file.write_row(row=row)


"""
This injector has two injection options
this function performs fault injection
by creating a breakpoint and steeping into it
"""


def fault_injection_by_breakpointing(conf, fault_models, inj_type, iterations, kernel_info_list, summary_file,
                                     max_time, current_path):
    for num_rounds in range(iterations):
        # Execute the fault injector for each one of the sections(apps) of the configuration file
        for fault_model in fault_models:
            # Execute one fault injection for a specific app
            # For each kernel
            for kernel_info_dict in kernel_info_list:
                # Generate an unique id for this fault injection
                unique_id = str(num_rounds) + "_" + str(inj_type) + "_" + str(fault_model)
                # try:
                valid_thread, valid_block, valid_register, bits_to_flip, injection_address, instruction_line = gen_injection_location(
                    kernel_info_dict=kernel_info_dict, max_num_regs=int(conf.get("DEFAULT", "maxNumRegs")),
                    injection_site=conf.get("DEFAULT", "injectionSite"))
                breakpoint_location = str(kernel_info_dict["kernel_name"] + ":"
                                          + kernel_info_dict["kernel_line"])
                r_old_val, r_new_val, fault_succ, hang, sdc = run_gdb_fault_injection(section="DEFAULT", conf=conf,
                                                                                      unique_id=unique_id,
                                                                                      valid_block=valid_block,
                                                                                      valid_thread=valid_thread,
                                                                                      valid_register=valid_register,
                                                                                      bits_to_flip=bits_to_flip,
                                                                                      injection_address=injection_address,
                                                                                      fault_model=fault_model,
                                                                                      breakpoint_location=breakpoint_location,
                                                                                      max_time=max_time,
                                                                                      inj_mode=inj_type,
                                                                                      current_path=current_path)
                # Write a row to summary file
                row = [unique_id, num_rounds, fault_model]
                row.extend(valid_thread)
                row.extend(valid_block)
                row.extend(
                    [r_old_val, r_new_val, 0, injection_address, valid_register, breakpoint_location, fault_succ, hang,
                     sdc, instruction_line])
                print(row)
                summary_file.write_row(row=row)
                # except Exception as err:
                #     print("\nERROR ON BREAK POINT MODE: Fault was not injected\n", str(err))
                time.sleep(2)


"""
Function that calls the profiler based on the injection mode
"""


def profiler_caller(conf):
    acc_time = 0

    # First MAX_TIMES_TO_PROFILE is necessary to measure the application running time
    os.environ['CAROL_FI_INFO'] = conf.get(
        "DEFAULT", "gdbInitStrings") + "|" + conf.get("DEFAULT",
                                                      "kernelBreaks") + "|" + "True"

    for i in range(0, cp.MAX_TIMES_TO_PROFILE + 1):
        profiler_cmd = conf.get("DEFAULT", "gdbExecName") + " -n -q -batch -x profiler.py"
        start = time.time()
        run_command([profiler_cmd])
        end = time.time()
        acc_time += end - start

    # This run is to get carol-fi-kernel-info.txt
    os.environ['CAROL_FI_INFO'] = conf.get("DEFAULT", "gdbInitStrings") + "|" + conf.get(
        "DEFAULT", "kernelBreaks") + "|" + "False"
    profiler_cmd = conf.get("DEFAULT", "gdbExecName") + " -n -q -batch -x profiler.py"
    out, err = run_command([profiler_cmd])

    return acc_time / cp.MAX_TIMES_TO_PROFILE, out, err


"""
Main function
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="config_file", help='Configuration file', required=True)
    parser.add_argument('-i', '--iter', dest="iterations",
                        help='How many times to repeat the programs in the configuration file', required=True, type=int)

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
    inj_type = conf.get("DEFAULT", "injType")
    max_time_app, gold_out_app, gold_err_app = profiler_caller(conf)
    # save gold file
    with open(cp.GOLD_OUTPUT_PATH, "w") as gold_file:
        gold_file.write(gold_out_app)
    with open(cp.GOLD_ERR_PATH, "w") as gold_err_file:
        if gold_err_app:
            gold_err_file.write(gold_err_app)
        else:
            gold_err_file.write("")
    print("1 - Profile finished\n###################################################")
    print("2 - Starting fault injection\n###################################################")
    print("2 - {} faults will be injected".format(args.iterations))
    print("###################################################")
    ########################################################################
    # Injector setup
    # Get fault models
    fault_models = [int(i) for i in str(conf.get('DEFAULT', 'faultModel')).split(',')]

    # Csv log
    fieldnames = ['unique_id', 'iteration', 'fault_model', 'thread_x', 'thread_y', 'thread_z',
                  'block_x', 'block_y', 'block_z', 'old_value', 'new_value', 'inj_mode',
                  'injection_address', 'register', 'breakpoint_location', 'fault_successful',
                  'crash', 'sdc', 'instruction_line']

    ########################################################################
    # Fault injection
    iterations = args.iterations
    csv_file = conf.get("DEFAULT", "csvFile")

    # Creating a summary csv file
    summary_file = SummaryFile(filename=csv_file, fieldnames=fieldnames, mode='w')

    # break mode is default option
    if 'break' in inj_type:
        # Load information file generated in profiler step
        kernel_info_list = cf.load_file(cp.KERNEL_INFO_DIR)
        fault_injection_by_breakpointing(conf=conf, fault_models=fault_models, inj_type=inj_type, iterations=iterations,
                                         kernel_info_list=kernel_info_list, summary_file=summary_file,
                                         max_time=max_time_app, current_path=current_path)
    # elif 'signal' in inj_type:
    #     # The hard mode
    #     fault_injection_by_signal(conf=conf, fault_models=fault_models, inj_type=inj_type, iterations=iterations,
    #                               summary_file=summary_file, max_time=max_time_app)

    print("###################################################")
    print("2 - Fault injection finished, results can be found in {}".format(conf.get("DEFAULT", "csvFile")))
    print("###################################################")
    # Clear /tmp files generated
    os.system("rm -f /tmp/carol-fi-kernel-info.txt")
    os.system("rm -f " + cp.GOLD_OUTPUT_PATH)
    os.system("rm -f " + cp.INJ_OUTPUT_PATH)
    os.system("rm -f " + cp.GOLD_ERR_PATH)
    os.system("rm -f " + cp.INJ_ERR_PATH)
    os.system("rm -f " + cp.DIFF_ERR_LOG + " " + cp.DIFF_LOG)
    ########################################################################


########################################################################
#                                   Main                               #
########################################################################

if __name__ == "__main__":
    main()
