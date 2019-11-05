import os
import pickle
import re
import sys
import common_parameters as cp

if sys.version_info >= (3, 0):
    import configparser  # python 3
else:
    import ConfigParser  # python 2

"""
Support function to execute a command
and return the output.
If the command contains NEWLINE character
it will result in a list.
"""


def execute_command(gdb, to_execute):
    ret = gdb.execute(to_execute, to_string=True)
    return ret.splitlines()


"""
Serialize a dictionary into a
file path using pickle.
"""


def save_file(file_path, data):
    with open(file_path, "wb") as f_out:
        pickle.dump(data, f_out)
        f_out.close()


"""
Serialize a dictionary into a
file path using pickle.
"""


def append_file(file_path, data):
    with open(file_path, "ab") as f_out:
        pickle.dump(data, f_out)
        f_out.close()


"""
Load a dictionary from a file path using pickle.
return a dictionary
"""


def load_file(file_path):
    with open(file_path, "rb") as f_in:
        data = pickle.load(f_in)
        return data


"""
Read configuration file
"""


def load_config_file(flip_config_file):
    # Read configuration file
    if sys.version_info >= (3, 0):
        conf = configparser.ConfigParser()
    else:
        conf = ConfigParser.ConfigParser()

    conf.read(flip_config_file)
    return conf


"""
Kill all remaining processes
"""


def kill_all(kill_string, logging=None):
    for cmd in kill_string.split(";"):
        os.system(cmd)
        if logging:
            logging.debug("kill cmd: {}".format(cmd))


"""
GDB python cannot find common_functions.py, so I added this directory to PYTHONPATH
"""


def set_python_env():
    current_path = os.path.dirname(os.path.realpath(__file__))
    os.environ['PYTHONPATH'] = "$PYTHONPATH:" + current_path + ":" + current_path + "/classes"
    os.environ['OMP_NUM_THREADS'] = '1'
    return current_path


"""
Remove all useless information produced by CUDA-GDB on the output files
before they got to the SDC check script
"""


def remove_useless_information_from_output(output_file_path):
    ok_output_lines = []
    with open(output_file_path, 'r') as ifp:
        lines = ifp.readlines()
        for line in lines:
            is_line_addable = True
            for pattern in cp.POSSIBLE_USELESS_GDB_OUTPUT_PATTERNS:
                # It is addable or not
                search_result = re.search(pattern=pattern, string=line)
                if search_result:
                    is_line_addable = False
            if is_line_addable:
                ok_output_lines.append(line)

    # Overwrite the output file
    with open(output_file_path, 'w') as ofp:
        ofp.writelines(ok_output_lines)


"""
Show output function
to allow pretty printing
"""


def printf(*string_to_print):
    for i in string_to_print:
        sys.stdout.write("\r{}".format(i))
    sys.stdout.write("\r\n")
