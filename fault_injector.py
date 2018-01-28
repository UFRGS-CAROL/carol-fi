#!/usr/bin/python
from __future__ import print_function
import os
import sys
import time
import datetime
import random
import subprocess
import threading
import re
import filecmp
import shutil
import argparse
import uuid
import common_functions as cf

if sys.version_info >= (3, 0):
    import configparser  # python 3
else:
    import ConfigParser  # python 2

# Debug env var
DEBUG = True

# Max size of register
max_size_register = 32

# Injection mode
# 0 -> Instruction output
injection_mode = 0


class RunGDB(threading.Thread):
    section = None
    conf = None
    unique_id = None

    def __init__(self, section, conf, unique_id):
        threading.Thread.__init__(self)
        self.section = section
        self.unique_id = unique_id
        self.conf = conf

    def run(self):
        if DEBUG:
            print("GDB Thread run, section and id: ", self.section, self.unique_id)
        start_cmd = self.conf.get(self.section,
                                  "gdbExecName") + " -n -q -batch -x " + "/tmp/flip-" + self.unique_id + ".py"
        os.system(start_cmd)


"""
Check if app stops execution (otherwise kill it after a time)
"""


def finish(section, conf, logging, timestamp_start):
    is_hang = False
    now = int(time.time())

    # Wait 2 times the normal duration of the program before killing it
    max_wait_time = conf.getfloat(section, "maxWaitTime")
    gdb_exec_name = conf.get(section, "gdbExecName")
    check_running = "ps -e | grep -i " + gdb_exec_name
    kill_strs = conf.get(section, "killStrs")

    while (now - timestamp_start) < (max_wait_time * 2):
        time.sleep(max_wait_time / 10)

        # Check if the gdb is still running, if not, stop waiting
        proc = subprocess.Popen(check_running, stdout=subprocess.PIPE, shell=True)
        (out, err) = proc.communicate()

        if not re.search(gdb_exec_name, str(out)):
            logging.debug("Process " + str(gdb_exec_name) + " not running, out:" + str(out))
            logging.debug("check command: " + check_running)
            break
        now = int(time.time())

    # check execution finished before or after waitTime
    if (now - timestamp_start) < max_wait_time * 2:
        logging.info("Execution finished before waitTime")
    else:
        logging.info("Execution did not finish before waitTime")
        is_hang = True

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


def save_output(section, is_sdc, is_hang, conf, logging, unique_id, flip_log_file, gdb_fi_log_file):
    output_file = conf.get(section, "outputFile")

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
    shutil.move(gdb_fi_log_file, cp_dir)
    if os.path.isfile(output_file) and (not masked) and fi_succ:
        shutil.move(output_file, cp_dir)


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


def check_sdcs(gold_file, output_file, logging):
    if not os.path.isfile(output_file):
        logging.error("outputFile not found: " + str(output_file))
    if os.path.isfile(gold_file) and os.path.isfile(output_file):
        return not filecmp.cmp(gold_file, output_file, shallow=False)
    else:
        return False


"""
Generate config file for the gdb flip_value script
"""


def gen_conf_file(gdb_init_strings, debug, unique_id, valid_block, valid_thread, valid_register, bits_to_flip,
                  fault_model,
                  injection_site, breakpoint_location):
    if sys.version_info >= (3, 0):
        fconf = configparser.SafeConfigParser()
    else:
        fconf = ConfigParser.SafeConfigParser()

    # valid_block = conf.get("DEFAULT", "validBlock").split(";")
    # valid_thread = conf.get("DEFAULT", "validThread").split(";")
    # valid_register = conf.get("DEFAULT", "validRegister")
    # bits_to_flip = [int(i) for i in conf.get("DEFAULT", "bitsToFlip").split(";")]
    # fault_model = conf.get("DEFAULT", "faultModel")
    # injection_site = conf.get("DEFAULT", "injectionSite")
    # breakpoint_location = conf.get("DEFAULT", "breakpointLocation")

    fconf.set("DEFAULT", "flipLogFile", "/tmp/carolfi-flipvalue-" + unique_id + ".log")
    fconf.set("DEFAULT", "debug", debug)
    fconf.set("DEFAULT", "gdbInitStrings", gdb_init_strings)
    fconf.set("DEFAULT", "faultModel", str(fault_model))
    fconf.set("DEFAULT", "injectionSite", injection_site)
    fconf.set("DEFAULT", "validThread", ";".join(valid_thread))
    fconf.set("DEFAULT", "validBlock", ";".join(valid_block))
    fconf.set("DEFAULT", "validRegister", ";".join(valid_register))
    fconf.set("DEFAULT", "bitsToFlip", ";".join(str(i) for i in bits_to_flip))
    fconf.set("DEFAULT", "breakpointLocation", breakpoint_location)

    fp = open("/tmp/flip-" + unique_id + ".conf", "w")
    fconf.write(fp)
    fp.close()


"""
Generate the gdb flip_value script
"""


def gen_flip_script(unique_id):
    fp = open("flip_value.py", "r")
    pscript = fp.read()
    fp.close()
    fp = open("/tmp/flip-" + unique_id + ".py", "w")

    pscript = pscript.replace("<conf-location>", "/tmp/flip-" + unique_id + ".conf")
    pscript = pscript.replace("<home-location>", "/home/carol/carol-fi")
    fp.write(pscript)
    fp.close()
    os.chmod("/tmp/flip-" + unique_id + ".py", 0o775)


"""
Generate the gdb profiler script
"""


def gen_profiler_script(unique_id, conf_filename):
    fp = open("profiler.py", "r")
    pscript = fp.read()
    fp.close()
    profiler_filename = "/tmp/profiler-" + unique_id + ".py"
    fp = open(profiler_filename, "w")

    fp.write(pscript.replace("<conf-location>", conf_filename))
    fp.close()
    os.chmod(profiler_filename, 0o775)
    return profiler_filename


"""
Function to run one execution of the fault injector
"""


def run_gdb_fault_injection(section, conf, unique_id, valid_block, valid_thread, valid_register, bits_to_flip,
                            injection_address,
                            fault_model, breakpoint_location):
    flip_log_file = "/tmp/carolfi-flipvalue-" + unique_id + ".log"
    gdb_fi_log_file = "/tmp/carolfi-" + unique_id + ".log"

    logging = cf.Logging(log_file=flip_log_file, debug=conf.get("DEFAULT", "debug"))

    logging.info("Starting GDB script")

    # Information about this fault

    # Generate configuration file for specific test
    gen_conf_file(gdb_init_strings=conf.get(section, "gdbInitStrings"),
                  debug=conf.get(section, "debug"),
                  unique_id=unique_id,
                  valid_block=valid_block,
                  valid_thread=valid_thread,
                  valid_register=valid_register,
                  bits_to_flip=bits_to_flip,
                  fault_model=fault_model,
                  injection_site=injection_address,
                  breakpoint_location=breakpoint_location)

    # Generate python script for GDB
    gen_flip_script(unique_id=unique_id)

    # Run pre execution function
    pre_execution(conf=conf, section=section)

    # Create one thread to start gdb script
    th = RunGDB(section, conf, unique_id)

    # Start couting time
    timestamp_start = int(time.time())

    # Start fault injection tread
    th.start()

    # Check if app stops execution (otherwise kill it after a time)
    isHang = finish(section=section, conf=conf, logging=logging, timestamp_start=timestamp_start)

    # Run pos execution function
    pos_execution(conf=conf, section=section)

    # Check output files for SDCs
    gold_file = conf.get(section, "goldFile")
    output_file = conf.get(section, "outputFile")
    # isSDC = check_sdcs(gold_file=gold_file, output_file=output_file, logging=logging)

    # Copy output files to a folder
    # save_output(section, isSDC, isHang)

    # Make sure threads finish before trying to execute again
    th.join()


"""
Select a valid stop address
from the file created in the profiler
step
"""


def get_valid_address(addresses):
    m = None
    registers = []
    instruction = ''
    address = ''
    byte_location = ''

    # search for a valid instruction
    while not m:
        element = random.randrange(2, len(addresses) - 1)
        instruction_line = addresses[element]

        expression = ".*([0-9a-fA-F][xX][0-9a-fA-F]+) (\S+):[ \t\n\r\f\v]*(\S+)[ ]*(\S+)"

        for i in [2, 3, 4, 5]:
            # INSTRUCTION R1, R2...
            # 0x0000000000b418e8 <+40>: MOV R4, R2...
            expression += ",[ ]*(\S+)"
            m = re.match(expression + ".*", instruction_line)

            if m:
                address = m.group(1)
                byte_location = m.group(2)
                instruction = m.group(3)
                registers.extend([m.group(3 + t) for t in range(0, i)])
                print(registers, m.groups())
                break

        if DEBUG:
            if not m:
                print("it is stoped here:", instruction_line)
            else:
                print("it choose something:", instruction_line)

    return registers, instruction, address, byte_location


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


def gen_injection_site(kernel_info_dict):
    global max_size_register, injection_mode
    # A valid block is a [block_x, block_y, block_z] coordinate
    # A valid thread is a [thread_x, thread_y, thread_z] coordinate
    valid_block, valid_thread = get_valid_thread(kernel_info_dict["threads"])

    # A injection site is a list of [registers, instruction, address, byte_location]
    registers, _, injection_site, _ = get_valid_address(kernel_info_dict["addresses"])

    # Randomly select (a) bit(s) to flip
    # Max double bit flip
    bits_to_flip = [0] * 2
    bits_to_flip[0] = random.randint(0, max_size_register - 1)

    # Selects it it is in the instruction output
    # or register file
    valid_register = None
    print("Inside injector", registers)
    if injection_mode == 0:
        valid_register = registers[-1]

    # Register file
    elif injection_mode == 1:
        raise NotImplementedError

    # Make sure that the same bit is not going to be selected
    r = range(0, bits_to_flip[0]) + range(bits_to_flip[0] + 1, max_size_register)
    bits_to_flip[1] = random.choice(r)

    return valid_thread, valid_block, valid_register, bits_to_flip, injection_site


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--conf', dest="configFile", help='Configuration file', required=True)
    parser.add_argument('-i', '--iter', dest="iterations",
                        help='How many times to repeat the programs in the configuration file', required=True, type=int)

    args = parser.parse_args()
    if args.iterations < 1:
        parser.error('Iterations must be greater than zero')

    # Start with a different seed every time to vary the random numbers generated
    # the seed will be the current number of second since 01/01/70
    random.seed()

    # Read the configuration file with data for all the apps that will be executed
    conf = cf.load_config_file(args.configFile)

    # Generate an unique id for this fault injection
    unique_id = str(uuid.uuid4())

    ########################################################################
    # Profiler step

    profiler_file = gen_profiler_script(unique_id=unique_id, conf_filename=args.configFile)
    profiler_cmd = conf.get("DEFAULT", "gdbExecName") + " -n -q -batch -x " + profiler_file
    print(profiler_cmd)
    if os.path.isfile(profiler_file):
        os.system(profiler_cmd)
    else:
        print(profiler_file, "not found, please set the correct profiler file before trying again.")
        raise IOError

    ########################################################################
    # Fault injection

    # Load information file generated in profiler step
    kernel_info_dir = "/tmp/carol-fi-kernel-info.txt"
    kernel_info_list = cf.load_file(kernel_info_dir)

    # Get fault models
    fault_models = range(0, int(conf.get('DEFAULT', 'faultModel')) + 1)

    # noinspection PyCompatibility
    for num_rounds in range(args.iterations):
        # Execute the fault injector for each one of the sections(apps) of the configuration file
        for fault_model in fault_models:
            # Execute one fault injection for a specific app
            # For each kernel
            for kernel_info_dict in kernel_info_list:
                valid_thread, valid_block, valid_register, bits_to_flip, injection_address = gen_injection_site(
                    kernel_info_dict=kernel_info_dict)
                run_gdb_fault_injection(section="DEFAULT", conf=conf,
                                        unique_id=unique_id, valid_block=valid_block,
                                        valid_thread=valid_thread, valid_register=valid_register,
                                        bits_to_flip=bits_to_flip, fault_model=fault_model,
                                        injection_address=injection_address,
                                        breakpoint_location=str(kernel_info_dict["kernel_name"] + ":"
                                                                + kernel_info_dict["kernel_line"]))

    # Clear /tmp files generated
    os.system("rm -f /tmp/*" + unique_id + "*")
    os.system("rm -f /tmp/carol-fi-kernel-info.txt")


########################################################################
#                                   Main                               #
########################################################################

if __name__ == "__main__":
    main()
