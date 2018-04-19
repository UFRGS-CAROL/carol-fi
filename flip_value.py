import random
import gdb
import re
import os
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters


class Breakpoint(gdb.Breakpoint):
    def __init__(self, **kwargs):
        super(Breakpoint, self).__init__(*args, **kwargs)

        # If kernel is not accessible it must return
        if kwargs.get('kludge') != 'None':
            self.__kludge = True
            return

        self.__block = kwargs.get('block')
        self.__thread = kwargs.get('thread')
        self.__register = kwargs.get('register')
        self.__bits_to_flip = kwargs.get('bits_to_flip')
        self.__fault_model = kwargs.get('fault_model')
        self.__logging = kwargs.get('logging')

    def stop(self):
        if self.__kludge:
            return

        # This if avoid the creation of another event connection
        # for some reason gdb cannot breakpoint addresses before
        # a normal breakpoint is hit
        self.__logging.debug("Trying Fault Injection")

        try:
            change_focus_cmd = "cuda kernel 0 block {0},{1},{2} thread {3},{4},{5}".format(str(self.__block[0]),
                                                                                           str(self.__block[1]),
                                                                                           str(self.__block[2]),
                                                                                           str(self.__thread[0]),
                                                                                           str(self.__thread[1]),
                                                                                           str(self.__thread[2]))
            thread_focus = gdb.execute(change_focus_cmd, to_string=True)
            # Thread focus return information
            self.__logging.info(str(thread_focus).replace("[", "").replace("]", "").strip())
        except Exception as err:
            self.__logging.exception("CUDA_FOCUS_exception: " + str(err))
            self.__logging.exception("Fault Injection Went Wrong")
            return True

        try:
            # Do the fault injection magic
            self.__generic_injector()

            self.__logging.info("Fault Injection Successful")
        except Exception as err:
            self.__logging.exception("fault_injection_python_exception: " + str(err))
            self.__logging.exception("Fault Injection Went Wrong")

        return True

    """
    Flip a bit or multiple bits based on a fault model
    """

    def __generic_injector(self):
        # get register content
        reg_cmd = cf.execute_command(gdb, "p/t $" + str(self.__register))
        m = re.match('\$(\d+)[ ]*=[ ]*(\S+).*', reg_cmd[0])

        if m:
            reg_content = str(m.group(2))
            # Make sure that binary value will have max size register
            reg_content_old = str('0' * (common_parameters.MAX_SIZE_REGISTER - len(reg_content))) + reg_content
            # Logging info result extracted from register
            self.__logging.info("reg_old_value: " + reg_content_old)
            reg_content_new = ''

            # Single bit flip
            if self.__fault_model == 0:
                # single bit flip
                reg_content_new = flip_a_bit(self.__bits_to_flip[0], reg_content_old)

            # Double bit flip
            elif self.__fault_model == 1:
                # multiple bit flip
                for bit_to_flip in self.__bits_to_flip:
                    reg_content_new = flip_a_bit(bit_to_flip, reg_content_old)

            # Random value
            elif self.__fault_model == 2:
                # random value is stored at bits_to_flip[0]
                reg_content_new = str(self.__bits_to_flip[0])

            # Zero values
            elif self.__fault_model == 3:
                reg_content_new = '0'

            # Least significant bits, not implemented
            elif self.__fault_model == 4:
                raise NotImplementedError

            reg_content_fliped = str(int(reg_content_new, 2))
            # send the new value to gdb
            reg_cmd_flipped = cf.execute_command(gdb, "set $" + str(self.__register) + " = " + reg_content_fliped)

            self.__logging.info("reg_new_value: " + str(reg_content_new))

            # Log command return only something was printed
            if len(reg_cmd_flipped) > 0:
                self.__logging.info("flip command return: " + str(reg_cmd_flipped))

            # print("REG MODIFIED ", cf.execute_command(gdb, "p/t $" + str(valid_register)))

            # Return the fault confirmation
            return reg_content_old != reg_content_new
        else:
            raise NotImplementedError


"""
Flip only a bit in a register content
"""


def flip_a_bit(bit_to_flip, reg_content):
    new_bit = '0' if reg_content[bit_to_flip] == '1' else '1'
    reg_content = reg_content[:bit_to_flip] + new_bit + reg_content[bit_to_flip + 1:]
    return reg_content


"""
Handler attached to exit event
"""


def exit_handler(event):
    global logging
    logging.info(str("event type: exit"))
    try:
        logging.info("exit code: {}".format(str(event.exit_code)))
    except:
        logging.exception(str("exit code: no exit code available "))


"""
Main function
"""


def main():
    global logging
    # Initialize GDB to run the app
    gdb.execute("set confirm off")

    # Connecting to a exit handler event
    gdb.events.exited.connect(exit_handler)

    # Get variables values from environment
    # First parse line
    # CAROL_FI_INFO = blockX,blockY,blockZ;threadX,threadY,threadZ;validRegister;bits_0,bits_1;fault_model;
    # injection_site;breakpoint;flip_log_file;debug;gdb_init_strings
    [block, thread, register, bits_to_flip, fault_model, injection_site, breakpoint_location,
     flip_log_file, debug, gdb_init_strings, inj_type, kludge] = str(os.environ['CAROL_FI_INFO']).split('|')

    # Logging
    logging = cf.Logging(log_file=flip_log_file, debug=debug)
    logging.info("Starting flip_value script")
    try:
        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
            logging.info("initializing setup: " + str(init_str))

    except gdb.error as err:
        print("initializing setup: " + str(err))

    # Set Breakpoint attributes to be used
    block = block.split(",")
    thread = thread.split(",")
    bits_to_flip = [int(i) for i in bits_to_flip.split(",")]
    fault_model = int(fault_model)
    # debug = bool(debug)

    # Place the first breakpoint, it is only to avoid
    # address memory error
    # breakpoint_kernel_line = gdb.Breakpoint(spec=breakpoint_location, type=gdb.BP_BREAKPOINT)
    breakpoint_kernel_line = Breakpoint(block=block, thread=thread, register=register, bits_to_flip=bits_to_flip,
                                        fault_model=fault_model, logging=logging, kludge=kludge,
                                        spec=breakpoint_location, type=gdb.BP_BREAKPOINT)

    kludge_breakpoint = None
    if kludge != 'None':
        kludge_breakpoint = Breakpoint(kludge=kludge, spec=kludge, type=gdb.BP_BREAKPOINT)

    # Start app execution
    gdb.execute("r")

    # Man, this is a quick fix
    if kludge_breakpoint:
        kludge_breakpoint.delete()
        del kludge_breakpoint
        gdb.execute('c')

    # Delete the breakpoint
    breakpoint_kernel_line.delete()
    del breakpoint_kernel_line

    # Continue execution until the next breakpoint
    gdb.execute("c")


# Call main execution
logging = None
main()
