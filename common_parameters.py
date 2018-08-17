from multiprocessing import Value

# Max size of register
HALF_MAX_SIZE_REGISTER = 16
SINGLE_MAX_SIZE_REGISTER = 32
DOUBLE_MAX_SIZE_REGISTER = 64

# Times to profile
# this will be the max number of executions
# to profiler application
MAX_TIMES_TO_PROFILE = 2

# Max seconds to check process again
MAX_TIME_TO_CHECK_PROCESS = 0.01

# Temporary file to store kernel information
KERNEL_INFO_DIR = "/tmp/carol-fi-kernel-info.txt"

# For golden generation
GOLD_ERR_PATH = "/tmp/carol_fi_golden_bench_err.txt"
GOLD_OUTPUT_PATH = "/tmp/carol_fi_golden_bench_output.txt"

# Files that will be compared to golden ones
INJ_OUTPUT_PATH = "/tmp/carol_fi_inj_bench_output.txt"
INJ_ERR_PATH = "/tmp/carol_fi_inj_bench_err.txt"

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
TIME_BEFORE_FIRST_SIGNAL = 0.5

# Num of signals that will be send to the application
NUM_OF_SIGNALS = 10

SHARED_FLAG = Value('b', 0)

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


