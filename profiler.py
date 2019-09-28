import gdb

"""
Main function
"""

# Initialize GDB to run the app
gdb.execute("set confirm off")
gdb.execute("set pagination off")
gdb.execute("set target-async off")
gdb.execute("set non-stop off")

# gdb_init_strings = str(os.environ["CAROL_FI_INFO"])
gdb_init_strings = arg0

for init_str in gdb_init_strings.split(";"):
     gdb.execute(init_str)

gdb.execute("r")
