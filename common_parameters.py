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
DIFF_LOG = '/tmp/diff.log'
DIFF_ERR_LOG = '/tmp/diff_err.log'

# Debug env vars
# Debug FI process
DEBUG = True
# Debug profiler process
DEBUG_PROFILER = True

# Log file for SignalApp thread
SIGNAL_APP_LOG = "/tmp/signal_app_thread.txt"

# Time before first signal
# Before the first signal we define the percentage of the overall time
# to send the first signal (IT IS THE PERCENTAGE)
# A value between 0.01 and 0.1 is desirable
TIME_WAIT_START_SIGNAL = 0.1

# Num of sleep time divisor
NUM_DIVISION_TIMES = 100.0

# time to sleep between the signals
TIME_TO_SLEEP = 0.01

# Common body of log filename
LOG_DEFAULT_NAME = "/tmp/carolfi-flipvalue-{}.log"

# If there are multiple GPUs set the one that will be used
GPU_INDEX = '0'

# Multiple gpus execution
PROCESS_ID = "/tmp/carol_fi_process_id_{}.txt"

# MAX INT 32 bits
MAX_INT_32 = 4294967295


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
