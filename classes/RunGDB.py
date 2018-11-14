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
    def __init__(self, unique_id, gdb_exec_name, flip_script, carol_fi_base_path, gdb_env_string,
                 inj_output_path, inj_err_path, gpu_to_execute):
        super(RunGDB, self).__init__()
        self.__gdb_exe_name = gdb_exec_name
        self.__flip_script = flip_script
        self.__unique_id = unique_id
        self.__base_path = carol_fi_base_path
        self.__gdb_env_string = gdb_env_string
        self.__inj_output_path = inj_output_path
        self.__inj_err_path = inj_err_path
        os.environ['CUDA_VISIBLE_DEVICES'] = str(gpu_to_execute)
        os.environ['OMP_NUM_THREADS'] = '1'

    def run(self):
        if cp.DEBUG:
            print("GDB Thread run, id: {}".format(self.__unique_id))

        start_cmd = "{}/{}".format(self.__base_path, self.__flip_script)
        script = '{} -ex \'"py arg0 = {}"\' -n -batch -x {} > {} 2>{} &'
        print(script.format(self.__gdb_exe_name, self.__gdb_env_string,
                                start_cmd, self.__inj_output_path,
                                self.__inj_err_path))
        os.system(script.format(self.__gdb_exe_name, self.__gdb_env_string,
                                start_cmd, self.__inj_output_path,
                                self.__inj_err_path))

    def kill_subprocess(self):
        os.system("killall -9 {}".format(os.path.basename(self.__gdb_exe_name)))

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

    """
    Run gdb python script with specific parameters
    It makes standart gdb script calls
    """

    def run_gdb_python(self, script):
        # cmd = 'env CUDA_DEVICE_WAITS_ON_EXCEPTION=1 ' + gdb_name
        cmd = gdb_name + ' ' + script  # -batch-silent
        return cmd
