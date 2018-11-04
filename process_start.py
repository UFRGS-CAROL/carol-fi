from subprocess import Popen
from sys import argv

with open(argv[1], "w") as fp:
    fp.write(str(Popen(argv[2]).pid))
