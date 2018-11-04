# from multiprocessing import Process
import os
from threading import Thread
from os import system, path
from subprocess import Popen, PIPE
from re import search
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will be at common_parameters module

"""
Class RunGdb: necessary to run gdb while
the main thread register the time
If RunGdb execution time > max timeout allowed
this thread will be killed
"""


class RunGDB(Thread):
    def __init__(self, unique_id, gdb_exec_name, flip_script, carol_fi_base_path, gdb_env_string):
        super(RunGDB, self).__init__()
        self.__process = None
        self.__gdb_exe_name = gdb_exec_name
        self.__flip_script = flip_script
        self.__unique_id = unique_id
        self.__process_file = cp.PROCESS_ID.format(unique_id)
        self.__base_path = carol_fi_base_path
        self.__gdb_env_string = gdb_env_string

    def run(self):
        if cp.DEBUG:
            print("GDB Thread run, section and id: {}".format(self.__unique_id))

        os.environ['OMP_NUM_THREADS'] = '1'

        start_cmd = cf.run_gdb_python(gdb_name=self.__gdb_exe_name, script=self.__base_path + "/" + self.__flip_script)
        script = "env CAROL_FI_INFO = {} OMP_NUM_THREADS=1 CUDA_VISIBLE_DEVICES={}"
        script += " PYTHONPATH=$PYTHONPATH:{}:{}/classes {} > {} 2>{} & "
        script = script.format(self.__gdb_env_string, cp.GPU_INDEX, self.__base_path, self.__base_path,
                               start_cmd, cp.INJ_OUTPUT_PATH, cp.INJ_ERR_PATH)
        print(script)
        # script = start_cmd + " >" + cp.INJ_OUTPUT_PATH + " 2>" + cp.INJ_ERR_PATH + " &"
        # os.system(to_execute.format(self.__process_file, script))
        self.__process = Popen(script)

    def kill_subprocess(self):
        system("kill -9 {}".format(self.__process.pid))
        self.__process.terminate()
        self.__process.kill()

    """
    Check if the process is still alive
    must also check the OS
    """

    def is_alive(self):
        if super(RunGDB, self).is_alive():
            return True

        # check both gdb and gdb bin name
        for exe in [path.basename(self.__gdb_exe_name), self.__gdb_exe_name]:
            check_running = "ps -e | grep -i " + exe
            process = Popen(check_running, stdout=PIPE, shell=True)
            (out, err) = process.communicate()

            # Mathews complains
            del process
            if search(exe, str(out)):
                return True

        return False
