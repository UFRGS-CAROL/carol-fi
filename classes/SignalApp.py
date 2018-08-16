import time
from classes.Logging import Logging
from threading import Thread
from random import uniform
from os import system

import common_parameters as cp  # All common parameters will bet at common_parameters module

"""
Signal the app to stop so GDB can execute the script to flip a value
"""


class SignalApp(Thread):
    def __init__(self, signal_cmd, max_wait_time, seq_signals, log_path, unique_id):
        super(SignalApp, self).__init__()
        self.__signal_cmd = signal_cmd
        self.__max_wait_time = float(max_wait_time)
        self.__seq_signal = int(seq_signals) * 10
        self.__log = Logging(log_file=log_path, unique_id=unique_id)

    def run(self):
        init = 0
        end = self.__max_wait_time / self.__seq_signal

        # Sleep for a random time
        init_wait_time = uniform(init, end)

        time_interval = float(self.__max_wait_time) / (self.__seq_signal * 10)
        time.sleep(init_wait_time)

        # Send a series of signal to make sure gdb will flip a value in one of the interrupt signals
        log_string = "sending {} signals using command: {} after {}s. The time interval is: {}".format(
            self.__seq_signal, self.__signal_cmd, init_wait_time, time_interval)

        if cp.DEBUG:
            print(log_string)

        self.__log.info(log_string)

        for i in range(0, self.__seq_signal):
            system(self.__signal_cmd)
            time.sleep(time_interval)
