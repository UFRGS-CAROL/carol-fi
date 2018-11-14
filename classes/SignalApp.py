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
    def __init__(self, signal_cmd, max_wait_time, log_path, unique_id, signals_to_send, init_sleep=0.0):
        super(SignalApp, self).__init__()
        self.__signal_cmd = signal_cmd
        os.system("rm -f {}".format(log_path))
        self.__log = Logging(log_file=log_path, unique_id=unique_id)

        self.__init_wait_time = uniform(init_sleep, max_wait_time)
        self.__signals_to_send = signals_to_send
        self.__time_to_sleep = (max_wait_time - self.__init_wait_time) / self.__signals_to_send

    def run(self):
        # Send a series of signal to make sure gdb will flip a value in one of the interrupt signals
        log_string = "Sending a signal using command: {} after {}s.".format(self.__signal_cmd, self.__init_wait_time)

        if cp.DEBUG:
            print(log_string)

        # Sleep for a random time
        time.sleep(self.__init_wait_time)

        self.__log.info(log_string)
        for signals in range(0, self.__signals_to_send):
            # > /dev/null 2>/dev/null
            os.system("{} ".format(self.__signal_cmd))
            self.__log.info("sending signal {}".format(signals))
            time.sleep(self.__time_to_sleep)

    def get_int_wait_time(self):
        return self.__init_wait_time
