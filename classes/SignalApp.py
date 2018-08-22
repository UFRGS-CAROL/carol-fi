import time
from classes.Logging import Logging
from threading import Thread
from random import uniform

import common_parameters as cp  # All common parameters will bet at common_parameters module
import os

"""
Signal the app to stop so GDB can execute the script to flip a value
"""


class SignalApp(Thread):
    def __init__(self, signal_cmd, max_wait_time, log_path, unique_id):
        super(SignalApp, self).__init__()
        self.__signal_cmd = signal_cmd
        self.__log = Logging(log_file=log_path, unique_id=unique_id)
        self.__init_wait_time = uniform(0, float(max_wait_time) * cp.TIME_BEFORE_FIRST_SIGNAL)

    def run(self):
        # fix failed injections
        ready_to_go = False
        while not ready_to_go:
            try:
                with open(cp.LOCK_FILE, "r") as fi:
                    if '1' in fi.read():
                        ready_to_go = True
            except:
                continue

        # Sleep for a random time
        time.sleep(self.__init_wait_time)

        # Send a series of signal to make sure gdb will flip a value in one of the interrupt signals
        log_string = "Sending a signal using command: {} after {}s.".format(self.__signal_cmd, self.__init_wait_time)

        if cp.DEBUG:
            print(log_string)

        self.__log.info(log_string)

        os.system(self.__signal_cmd)

    def get_int_wait_time(self):
        return self.__init_wait_time
