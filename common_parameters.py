# Max size of register
SINGLE_MAX_SIZE_REGISTER = 32

# Times to profile
# this will be the max number of executions
# to profiler application
MAX_TIMES_TO_PROFILE = 2

# Log path to store all injections info
LOGS_PATH = 'logs'

# Temporary file to store kernel information
KERNEL_INFO_DIR = LOGS_PATH + '/tmp/carol-fi-kernel-info.txt'

# For golden generation
GOLD_ERR_PATH = LOGS_PATH + '/tmp/carol_fi_golden_bench_err.txt'
GOLD_OUTPUT_PATH = LOGS_PATH + '/tmp/carol_fi_golden_bench_output.txt'

# Files that will be compared to golden ones
INJ_OUTPUT_PATH = LOGS_PATH + '/tmp/carol_fi_inj_bench_output_{}.txt'
INJ_ERR_PATH = LOGS_PATH + '/tmp/carol_fi_inj_bench_err_{}.txt'

# Internal python scripts
FLIP_SCRIPT = 'flip_value.py'
PROFILER_SCRIPT = 'profiler.py'

# Temporary difference logs
DIFF_LOG = LOGS_PATH + '/tmp/diff_{}.log'
DIFF_ERR_LOG = LOGS_PATH + '/tmp/diff_err_{}.log'

# Debug env vars
# Debug FI process
DEBUG = False
# Debug profiler process
DEBUG_PROFILER = True

# Log file for SignalApp thread
SIGNAL_APP_LOG = LOGS_PATH + '/tmp/signal_app_thread_{}.txt'

# Num of sleep time divisor
NUM_DIVISION_TIMES = 100.0

# Common body of log filename
LOG_DEFAULT_NAME = LOGS_PATH + '/tmp/carolfi-flipvalue-{}.log'


# MAX INT 32 bits
MAX_INT_32 = 4294967295

# Most of the benchmarks we cannot wait until the end of the processing
# Considering most of 90% of the time
MAX_SIGNAL_BEFORE_ENDING = 0.9

# termination, program, alarm, asynchronous, job, operation error, miscellaneous, signal interruption
# 'SIGINT' must not be here, since I used it to send an interruption to app
SIGNALS = ['SIGKILL', 'SIGTERM', 'SIGQUIT', 'SIGHUP',  # termination codes
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

# All trash produced by GDB must be add here in this list
# Using the Regular Expression format (python re)

POSSIBLE_USELESS_GDB_OUTPUT_PATTERNS = [
        r'.*received signal SIGINT, Interrupt.*',  # Thread SIGINT message
        r'.*New Thread.*',  # New GDB Thread creation
        r'.*Thread debugging using.*enabled.*',  # Lib thread enabled
        r'.*Using host.*library.*',  # Using host library
        r'.*Switching focus to CUDA kernel.*',  # Switching focus to CUDA kernel message
        r'.*0x.*in.*<<<.*>>>.*',  # Kernel interruption message
        r'.*Inferior.*\(process.*\) exited normally.*',  # GDB exited normally message
        r'.*Thread 0x.*exited.*',  # Thread exited
        r'.*0x.* in cu.* () from /usr/lib/.*libcuda.*',  # Cuda lib calls
        r'.*0x.*in.*\[clone.*\].*\(\).*',  # OMP calls
        r'.*0x.*in.*',  # General API call
        r'.*Inferior.*\(process.*\).*',  # General inferior process
    ]


# Injection sites
RF = 0
INST_OUT = 1
INST_ADD = 2

INJECTION_SITES = {
    'RF': RF,
    'INST_OUT': INST_OUT,
    'INST_ADD': INST_ADD
}

# Which fault model to use, 0 -> single; 1 -> double;
# 2 -> random; 3 -> zeros; 4 -> least 16 significant bits (LSB);
# 5 -> least 8 significant bits (LSB)
FLIP_SINGLE_BIT = 0
FLIP_TWO_BITS = 1
RANDOM_VALUE = 2
ZERO_VALUE = 3
LEAST_16_BITS = 4
LEAST_8_BITS = 5
