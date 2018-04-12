import datetime
import pickle
import sys
import time

if sys.version_info >= (3, 0):
    import configparser  # python 3
else:
    import ConfigParser  # python 2

# Max size of register
MAX_SIZE_REGISTER = 32

# Times to profile
# this will be the max number of executions
# to profiler application
MAX_TIMES_TO_PROFILE = 2

# TMP file that will store kernel information
KERNEL_INFO_DIR = "/tmp/carol-fi-kernel-info.txt"
GOLD_OUTPUT_PATH = "/tmp/carol_fi_golden_bench_output.txt"
INJ_OUTPUT_PATH = "/tmp/carol_fi_inj_bench_output.txt"
GOLD_ERR_PATH = "/tmp/carol_fi_inj_bench_err.txt"
INJ_ERR_PATH = "/tmp/carol_fi_inj_bench_err.txt"
CAROL_FI_RUN_SH = "carol_fi_run.sh"
FLIP_SCRIPT = 'flip_value.py'
DIFF_LOG = '/tmp/diff.log'
DIFF_ERR_LOG = '/tmp/diff_err.log'

# Debug env var
DEBUG = False

# termination, program, alarm, asynchronous, job, operation error, miscellaneous, si
SIGNALS = ['SIGKILL', 'SIGTERM', 'SIGINT', 'SIGQUIT', 'SIGHUP',  # termination codes
           'SIGFPE', 'SIGILL', 'SIGSEGV', 'SIGBUS', 'SIGABRT', 'SIGIOT', 'SIGTRAP', 'SIGEMT', 'SIGSYS',  # program codes
           'SIGALRM', 'SIGVTALRM', 'SIGPROF',  # alarm codes
           'SIGIO', 'SIGURG', 'SIGPOLL',  # asynchronous codes
           'SIGCHLD', 'SIGCLD', 'SIGCONT', 'SIGSTOP', 'SIGTSTP', 'SIGTTIN', 'SIGTTOU',  # job control
           'SIGPIPE', 'SIGLOST', 'SIGXCPU', 'SIGXFSZ',  # operation codes
           'SIGUSR1', 'SIGUSR2', 'SIGWINCH', 'SIGINFO',  # miscellaneous codes
           'strsignal', 'psignal',  # signal messages
           # cuda signals
           'CUDA_EXCEPTION_0', 'CUDA_EXCEPTION_1', 'CUDA_EXCEPTION_2', 'CUDA_EXCEPTION_3', 'CUDA_EXCEPTION_4',
           'CUDA_EXCEPTION_5',
           'CUDA_EXCEPTION_6', 'CUDA_EXCEPTION_7', 'CUDA_EXCEPTION_8', 'CUDA_EXCEPTION_9', 'CUDA_EXCEPTION_10',
           'CUDA_EXCEPTION_11',
           'CUDA_EXCEPTION_12', 'CUDA_EXCEPTION_13', 'CUDA_EXCEPTION_14', 'CUDA_EXCEPTION_15']

"""
Support function to execute a command
and return the output.
If the command contains NEWLINE character
it will result in a list.
"""


def execute_command(gdb, to_execute):
    ret = gdb.execute(to_execute, to_string=True)
    return ret.splitlines()


"""
Serialize a dictionary into a
file path using pickle.
"""


def save_file(file_path, data):
    f_out = open(file_path, "wb")
    pickle.dump(data, f_out)
    f_out.close()


"""
Load a dictionary from a file path using pickle.
return a dictionary
"""


def load_file(file_path):
    f_in = open(file_path, "rb")
    data = pickle.load(f_in)
    f_in.close()
    return data


"""
Read configuration file
"""


def load_config_file(flip_config_file):
    # Read configuration file
    if sys.version_info >= (3, 0):
        conf = configparser.ConfigParser()
    else:
        conf = ConfigParser.ConfigParser()

    conf.read(flip_config_file)
    return conf


class Logging:
    log_file = None
    debug_var = None
    unique_id = None

    def __init__(self, log_file, debug, unique_id=''):
        self.log_file = log_file
        self.debug_var = debug
        self.unique_id = unique_id

    def info(self, msg):
        fp = open(self.log_file, "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[INFO -- " + d + "]\n" + msg + "\n")
        fp.close()

    def exception(self, msg):
        fp = open(self.log_file, "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[EXCEPTION -- " + d + "]\n" + msg + "\n")
        fp.close()

    def error(self, msg):
        fp = open(self.log_file, "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[ERROR -- " + d + "]\n" + msg + "\n")
        fp.close()

    def debug(self, msg):
        if self.debug_var:
            fp = open(self.log_file, "a")
            d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            fp.write("[DEBUG -- " + d + "]\n" + msg + "\n")
            fp.close()

    def summary(self, msg):
        fp = open(self.log_file, "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[SUMMARY -- " + d + "]\nFI-uniqueID=" + str(self.unique_id) + "\n" + msg + "\n")
        fp.close()

    def search(self, find):
        fp = open(self.log_file, "r")
        lines = fp.readlines()
        fp.close()
        for l in lines:
            if find in l:
                return l
        return None
