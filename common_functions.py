import gdb
import pickle
import sys


if sys.version_info >= (3,0):
    import configparser # python 3
else:
    import ConfigParser # python 2

flipConfigFile = "/home/carol/carol-fi/codes/cuda/matrixMul/matrixmul.conf"


"""
Support function to execute a command
and return the output.
If the command contains NEWLINE character
it will result in a list.
"""


def execute_command(to_execute):
    ret = gdb.execute(to_execute, to_string=True)
    return ret.splitlines()


"""
Serialize a dictionary into a
file path using pickle.
"""


def save_file(file_path, data):
    f_out = open(file_path, "wb")
    pickle.dump(data, f_out)
    f_out.close()


"""
Load a dictionary from a file path using pickle.
return a dictionary
"""


def load_file(file_path):
    f_in = open(file_path, "rb")
    data = pickle.load(f_in)
    f_in.close()
    return data

"""
Read configuration file
"""

def load_config_file():
    # Read configuration file
    if sys.version_info >= (3, 0):
        conf = configparser.ConfigParser()
    else:
        conf = ConfigParser.ConfigParser()

    conf.read(flipConfigFile)
    return conf

