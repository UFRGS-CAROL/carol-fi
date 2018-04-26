GOLD_OUTPUT_PATH = "/tmp/carol_fi_golden_bench_output.txt"

# Max size of register
MAX_SIZE_REGISTER = 32

# Times to profile
# this will be the max number of executions
# to profiler application
MAX_TIMES_TO_PROFILE = 2

KERNEL_INFO_DIR = "/tmp/carol-fi-kernel-info.txt"
INJ_OUTPUT_PATH = "/tmp/carol_fi_inj_bench_output.txt"
GOLD_ERR_PATH = "/tmp/carol_fi_inj_bench_err.txt"
INJ_ERR_PATH = "/tmp/carol_fi_inj_bench_err.txt"
CAROL_FI_RUN_SH = "carol_fi_run.sh"
FLIP_SCRIPT = 'flip_value.py'
DIFF_LOG = '/tmp/diff.log'
DIFF_ERR_LOG = '/tmp/diff_err.log'

# Debug env var
DEBUG = True

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