import random
import gdb
import re
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will be at common_parameters module

"""
BitFlip class
to implement the bit flip process
"""


class BitFlip:
    def __init__(self, **kwargs):
        # If kernel is not accessible it must return
        self.__kernel_registers = kwargs.pop('kernel_registers') if 'kernel_registers' in kwargs else None
        self.__bits_to_flip = kwargs.pop('bits_to_flip') if 'bits_to_flip' in kwargs else None
        self.__fault_model = kwargs.pop('fault_model') if 'fault_model' in kwargs else None
        self.__logging = kwargs.pop('logging') if 'logging' in kwargs else None
        self.__injection_mode = kwargs.pop('injection_mode') if 'injection_mode' in kwargs else None
        self.fault_injected = False

    """
    TODO: Describe the method
    """

    def single_event(self):
        # This if avoid the creation of another event connection
        # for some reason gdb cannot breakpoint addresses before
        # a normal breakpoint is hit
        self.__logging.debug("Trying Fault Injection with {} mode".format(self.__injection_mode))
        try:
            # Focusing the thread
            self.__thread_focus()
        except Exception as err:
            # Even if CUDA focus was not successful we keep going
            self.__logging.exception("CUDA_FOCUS_CANNOT_BE_REQUESTED. KEEP GOING, with error {}".format(err))

        try:
            self.__select_register()
        except Exception as err:
            err_str = "CANNOT SELECT THE REGISTER, PROBABLY FAULT WILL NOT BE INJECTED. Error {}".format(err)
            self.__logging.exception(err_str)

        # Register if fault was injected or not
        self.fault_injected = False
        try:
            # Do the fault injection magic
            # RF is the default mode of injection
            if 'RF' in self.__injection_mode or self.__injection_mode is None:
                self.fault_injected = self.__rf_generic_injector()
            elif 'INST' in self.__injection_mode:
                pass

            # Test fault injection result
            if self.fault_injected:
                self.__logging.info("Fault Injection Successful")
            else:
                self.__logging.info("Fault Injection Went Wrong")

        except Exception as err:
            self.__logging.exception("fault_injection_python_exception: {}".format(err))
            self.__logging.exception("Fault Injection Went Wrong")

    """
    Selects a valid thread for a specific
    kernel
    return the coordinates for the block
    and the thread
    """

    def __thread_focus(self):
        # Selecting the block
        blocks = cf.execute_command(gdb=gdb, to_execute="info cuda blocks")
        # it must be a valid block
        block = None
        block_len = len(blocks)
        while not block:
            block_index = random.randint(0, block_len)
            if 'running' in blocks[block_index] and '*' not in blocks[block_index]:
                m = re.match(".*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*", blocks[block_index])
                if m:
                    block = "{},{},{}".format(m.group(1), m.group(2), m.group(3))

        change_focus_block_cmd = "cuda block {}".format(block)
        block_focus = cf.execute_command(gdb=gdb, to_execute=change_focus_block_cmd)
        # Thread focus return information
        self.__logging.info(
            "CUDA_BLOCK_FOCUS:{}".format(str(block_focus).replace("[", "").replace("]", "").strip()))

        # Selecting the thread
        threads = cf.execute_command(gdb=gdb, to_execute="info cuda threads")
        thread = None
        thread_len = len(threads)

        while not thread:
            thread_index = random.randint(0, thread_len)
            pattern = ".*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*"
            m = re.match(pattern, threads[thread_index])
            if m:
                thread = "{},{},{}".format(m.group(10), m.group(11), m.group(12))

        change_focus_thread_cmd = "cuda thread {}".format(thread)
        thread_focus = cf.execute_command(gdb=gdb, to_execute=change_focus_thread_cmd)

        # Thread focus return information
        self.__logging.info(
            "CUDA_THREAD_FOCUS:{}".format(str(thread_focus).replace("[", "").replace("]", "").strip()))

    """
    Flip a bit or multiple bits based on a fault model
    """

    def __rf_generic_injector(self):
        # get register content
        reg_cmd = cf.execute_command(gdb, "p/t ${}".format(self.__register))
        m = re.match('\$(\d+)[ ]*=[ ]*(\S+).*', reg_cmd[0])

        reg_content_old = str(m.group(2))
        # Make sure that binary value will have max size register
        reg_content_full_bits = str('0' * (cp.SINGLE_MAX_SIZE_REGISTER - len(reg_content_old))) + reg_content_old

        reg_content_new = ''

        # Single bit flip or Least significant bits
        if self.__fault_model in [0, 1, 4]:
            # single bit flip or Double bit flip
            reg_content_new = reg_content_full_bits
            for bit_to_flip in self.__bits_to_flip:
                reg_content_new = self.__flip_a_bit(int(bit_to_flip), reg_content_new)
            reg_content_new = hex(int(reg_content_new, 2))

        # Random value or Zero value
        elif self.__fault_model in [2, 3]:
            # random value is stored at bits_to_flip[0]
            reg_content_new = self.__bits_to_flip[0]

        # send the new value to gdb
        flip_command = "set ${} = {}".format(self.__register, reg_content_new)
        reg_cmd_flipped = cf.execute_command(gdb, flip_command)

        # ['$2 = 100000000111111111111111']
        reg_modified = str(cf.execute_command(gdb, "p/t ${}".format(self.__register))[0]).split("=")[1].strip()

        # LOGGING
        # Logging info result extracted from register
        self.__logging.info("old_value:{}".format(reg_content_old))
        # Also logging the new value
        self.__logging.info("new_value:{}".format(reg_modified))

        # Log command return only something was printed
        if len(reg_cmd_flipped) > 0:
            self.__logging.info("flip command return:{}".format(reg_cmd_flipped))

        # Return the fault confirmation
        return reg_content_old != reg_modified

    """
    Flip only a bit in a register content
    """

    @staticmethod
    def __flip_a_bit(bit_to_flip, reg_content):
        new_bit = '0' if reg_content[bit_to_flip] == '1' else '1'
        reg_content = reg_content[:bit_to_flip] + new_bit + reg_content[bit_to_flip + 1:]
        return reg_content

    """
    Runtime select register
    """

    def __select_register(self):
        disassemble_array = cf.execute_command(gdb=gdb, to_execute="disassemble")
        self.__logging.debug("error on select register {}".format(disassemble_array[0]))
        m = re.match(".*Dump of assembler code for function[ ]+(\S+)\:.*", disassemble_array[0])
        max_num_register = 1
        kernel = ''
        if m:
            kernel = m.group(1)
            max_num_register = self.__kernel_registers[kernel]
        self.__register = "R{}".format(random.randint(0, max_num_register))
        self.__logging.info("SELECTED_REGISTER:{}".format(self.__register))
        self.__logging.info("SELECTED_KERNEL:{}".format(kernel))
