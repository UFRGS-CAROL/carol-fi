# Max size of register
SINGLE_MAX_SIZE_REGISTER = 32

# Times to profile
# this will be the max number of executions
# to profiler application
MAX_TIMES_TO_PROFILE = 2

# Temporary file to store kernel information
KERNEL_INFO_DIR = "/tmp/carol-fi-kernel-info.txt"

# For golden generation
GOLD_ERR_PATH = "/tmp/carol_fi_golden_bench_err.txt"
GOLD_OUTPUT_PATH = "/tmp/carol_fi_golden_bench_output.txt"

# Files that will be compared to golden ones
INJ_OUTPUT_PATH = "/tmp/carol_fi_inj_bench_output_{}.txt"
INJ_ERR_PATH = "/tmp/carol_fi_inj_bench_err_{}.txt"

# Internal python scripts
FLIP_SCRIPT = 'flip_value.py'
PROFILER_SCRIPT = 'profiler.py'

# Temporary difference logs
DIFF_LOG = '/tmp/diff_{}.log'
DIFF_ERR_LOG = '/tmp/diff_err_{}.log'

# Debug env vars
# Debug FI process
DEBUG = True
# Debug profiler process
DEBUG_PROFILER = True

# Log file for SignalApp thread
SIGNAL_APP_LOG = "/tmp/signal_app_thread_{}.txt"

# Num of sleep time divisor
NUM_DIVISION_TIMES = 100.0

# Common body of log filename
LOG_DEFAULT_NAME = "/tmp/carolfi-flipvalue-{}.log"


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
