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
        self.__max_wait_time = float(max_wait_time)
        self.__log = Logging(log_file=log_path, unique_id=unique_id)
        cp.SHARED_FLAG.value = 0

    def run(self):
        init = 0
        end = self.__max_wait_time * cp.TIME_BEFORE_FIRST_SIGNAL

        # Sleep for a random time
        init_wait_time = uniform(init, end)

        time_interval = float(self.__max_wait_time) / cp.NUM_OF_SIGNALS
        time.sleep(init_wait_time)

        # Send a series of signal to make sure gdb will flip a value in one of the interrupt signals
        log_string = "sending {} signals using command: {} after {}s. The time interval is: {}".format(
            cp.NUM_OF_SIGNALS, self.__signal_cmd, init_wait_time, time_interval)

        if cp.DEBUG:
            print(log_string)

        self.__log.info(log_string)

        for i in range(0, cp.NUM_OF_SIGNALS):
            if cp.DEBUG:
                print("SHARED FLAG {}".format(cp.SHARED_FLAG.value))
            if cp.SHARED_FLAG.value == 0:
                os.system(self.__signal_cmd)
                time.sleep(time_interval)
