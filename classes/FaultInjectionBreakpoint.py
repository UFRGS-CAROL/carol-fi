import gdb
import re
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will be at common_parameters module

"""
Fault injection breakpoint class, will do a flip of the bit(s) when breakpoint is hit
"""


class FaultInjectionBreakpoint(gdb.Breakpoint):
    def __init__(self, *args, **kwargs):
        # If kernel is not accessible it must return
        self.__kludge = kwargs.pop('kludge') if 'kludge' in kwargs else None
        self.__block = kwargs.pop('block') if 'block' in kwargs else None
        self.__thread = kwargs.pop('thread') if 'thread' in kwargs else None
        self.__register = kwargs.pop('register') if 'register' in kwargs else None
        self.__bits_to_flip = kwargs.pop('bits_to_flip') if 'bits_to_flip' in kwargs else None
        self.__fault_model = kwargs.pop('fault_model') if 'fault_model' in kwargs else None
        self.__logging = kwargs.pop('logging') if 'logging' in kwargs else None
        # self.ignore_count = int(kwargs.pop('breaks_to_ignore')) if 'breaks_to_ignore' in kwargs else 0

        super(FaultInjectionBreakpoint, self).__init__(*args, **kwargs)

    def stop(self):
        if self.__kludge:
            return True

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
            if self.__generic_injector():
                self.__logging.info("Fault Injection Successful")
            else:
                self.__logging.info("Fault Injection Went Wrong, reg_old and reg_new are the same")

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
            reg_content_old = str('0' * (cp.SINGLE_MAX_SIZE_REGISTER - len(reg_content))) + reg_content
            # Logging info result extracted from register
            self.__logging.info("reg_old_value: " + reg_content_old)
            reg_content_new = ''

            # Single bit flip or Least significant bits
            if self.__fault_model == 0 or self.__fault_model == 4:
                # single bit flip
                reg_content_new = self.flip_a_bit(self.__bits_to_flip[0], reg_content_old)

            # Double bit flip
            elif self.__fault_model == 1:
                # multiple bit flip
                for bit_to_flip in self.__bits_to_flip:
                    reg_content_new = self.flip_a_bit(bit_to_flip, reg_content_old)

            # Random value
            elif self.__fault_model == 2:
                # random value is stored at bits_to_flip[0]
                reg_content_new = str(self.__bits_to_flip[0])

            # Zero values
            elif self.__fault_model == 3:
                reg_content_new = '0'

            reg_content_flipped = str(int(reg_content_new, 2))
            # send the new value to gdb
            reg_cmd_flipped = cf.execute_command(gdb, "set $" + str(self.__register) + " = " + reg_content_flipped)

            # ['$2 = 100000000111111111111111']
            reg_modified = str(cf.execute_command(gdb, "p/t $" + str(self.__register))[0]).split("=")[1].strip()
            self.__logging.info("reg_new_value: " + reg_modified)

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

    @staticmethod
    def __flip_a_bit(bit_to_flip, reg_content):
        new_bit = '0' if reg_content[bit_to_flip] == '1' else '1'
        reg_content = reg_content[:bit_to_flip] + new_bit + reg_content[bit_to_flip + 1:]
        return reg_content

    def __select_frame(self):
        pass
