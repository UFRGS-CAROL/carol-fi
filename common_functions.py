import gdb
import pickle


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