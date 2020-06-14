import random
import sys

import gdb
import re
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will be at common_parameters module
# from collections import deque

"""
BitFlip class
to implement the bit flip process.
The methods in this class will execute only inside a CUDA kernel
"""


class BitFlip:
    def __init__(self, **kwargs):
        # If kernel is not accessible it must return
        self.__bits_to_flip = kwargs.get('bits_to_flip')
        self.__fault_model = kwargs.get('fault_model')
        self.__logging = kwargs.get('logging')
        self.__injection_site = kwargs.get('injection_site')
        self.fault_injected = False

    """
    print exception info
    """

    @staticmethod
    def __exception_str():
        exc_type, exc_obj, exc_tb = sys.exc_info()
        return "Exception type {} at line {}".format(exc_type, exc_tb.tb_lineno)

    """
    TODO: Describe the method
    """

    def single_event(self):
        # fault_injected attribute will be set by the methods that perform fault injection
        # Focusing the thread. If focus succeed, otherwise not
        if self.__thread_focus():
            # Do the fault injection magic

            # Register File mode
            if cp.RF == self.__injection_site:
                # Select the register before the injection
                self.__select_register()
                # RF is the default mode of injection
                self.__rf_generic_injector()

            # Instruction Output mode
            elif cp.INST_OUT == self.__injection_site:
                self.__inst_generic_injector()

            # Instruction Address mode
            elif cp.INST_ADD == self.__injection_site:
                self.__logging.exception("INST_ADD NOT IMPLEMENTED YET")
                self.__logging.exception(self.__exception_str())
                self.fault_injected = False

            # Test fault injection result
            self.__logging.info("Fault Injection " + ("Successful" if self.fault_injected else "Went Wrong"))

    """
    Selects a valid thread for a specific
    kernel
    return the coordinates for the block
    and the thread
    """

    def __thread_focus(self):
        try:
            # Selecting the block
            blocks = cf.execute_command(gdb=gdb, to_execute="info cuda blocks")
            # it must be a valid block
            block = None
            block_len = len(blocks)
            while not block:
                block_index = random.randint(0, block_len)
                if 'running' in blocks[block_index] and '*' not in blocks[block_index]:
                    m = re.match(r".*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*", blocks[block_index])
                    if m:
                        block = "{},{},{}".format(m.group(4), m.group(5), m.group(6))

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
                patt = r".*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*"
                m = re.match(patt, threads[thread_index])
                if m:
                    thread = "{},{},{}".format(m.group(10), m.group(11), m.group(12))

            change_focus_thread_cmd = "cuda thread {}".format(thread)
            thread_focus = cf.execute_command(gdb=gdb, to_execute=change_focus_thread_cmd)

            # Thread focus return information
            self.__logging.info(
                "CUDA_THREAD_FOCUS:{}".format(str(thread_focus).replace("[", "").replace("]", "").strip()))

        except Exception as err:
            # Even if CUDA focus was not successful we keep going
            err_str = str(err)
            self.__logging.exception("CUDA_FOCUS_CANNOT_BE_REQUESTED, ERROR:" + err_str)
            self.__logging.exception(self.__exception_str())

            # No need to continue if no active kernel
            if err_str == cp.FOCUS_ERROR_STRING:
                return False

        # If we are inside the kernel return true
        return True

    """
    Flip a bit or multiple bits based on a fault model
    """

    def __rf_generic_injector(self):
        try:
            # get register content
            reg_cmd = cf.execute_command(gdb, "p/t ${}".format(self.__register))
            m = re.match(r'\$(\d+)[ ]*=[ ]*(\S+).*', reg_cmd[0])

            reg_content_old = str(m.group(2))
            # Make sure that binary value will have max size register
            reg_content_full_bits = str(
                '0' * (cp.SINGLE_MAX_SIZE_REGISTER - len(reg_content_old))) + reg_content_old

            reg_content_new = ''

            # Single or double bit flip or Least significant bits
            if self.__fault_model in [cp.FLIP_SINGLE_BIT, cp.FLIP_TWO_BITS, cp.LEAST_16_BITS, cp.LEAST_8_BITS]:
                try:
                    # single bit flip or Double bit flip
                    reg_content_new = reg_content_full_bits
                    for bit_to_flip in self.__bits_to_flip:
                        reg_content_new = self.__flip_a_bit(int(bit_to_flip), reg_content_new)
                    reg_content_new = hex(int(reg_content_new, 2))
                except Exception as err:
                    self.__logging.exception("exception: {}".format(err))
                    self.__logging.exception(self.__exception_str())

            # Random value or Zero value
            elif self.__fault_model == cp.RANDOM_VALUE or self.__fault_model == cp.ZERO_VALUE:
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
            self.fault_injected = reg_content_old != reg_modified

        except Exception as err:
            self.__logging.exception("fault_injection_python_exception: {}".format(err))
            self.__logging.exception(self.__exception_str())
            self.fault_injected = False

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
        # try:
        # registers_list = deque(cf.execute_command(gdb=gdb, to_execute="info registers"))
        # Start on 1 to consider R0
        max_num_register = 1
        # registers_list.popleft()
        registers_list = cf.execute_command(gdb=gdb, to_execute="info registers")
        for line in registers_list:
            m = re.match(r".*R.*0x([0-9a-fA-F]+).*", line)
            if m and m.group(1) != '0':
                max_num_register += 1

        self.__register = "R{}".format(random.randint(0, max_num_register))
        self.__logging.info("SELECTED_REGISTER:{}".format(self.__register))
        #     return True
        # except Exception as err:
        #     err_str = "CANNOT SELECT THE REGISTER, FAULT WILL NOT BE INJECTED. Error {}".format(err)
        #     self.__logging.exception(err_str)
        #     self.__logging.exception(self.__exception_str())
        #     return False

    """
    Instruction injector    
    """

    def __inst_generic_injector(self):
        disassemble_array = cf.execute_command(gdb=gdb, to_execute="disassemble")
        # Search the line to inject
        # -1 will use the next instruction after program counter
        for i in range(0, len(disassemble_array) - 1):
            next_line = disassemble_array[i + 1]

            # => defines where the program counter is
            # There is an instruction on this line
            # then inject in the output register
            if "=>" in disassemble_array[i] and re.match(r".*:\t(\S+) .*", next_line):
                # If it gets the PC + 1 then I must inject in the input of the next instruction
                # Which is the most right register (-1 index)
                self.__register = "R{}".format(re.findall(r"R(\d+)", next_line)[-1])
                self.__logging.info("SELECTED_REGISTER:{}".format(self.__register))
                self.__logging.info("ASSM_LINE:{}".format(next_line))

                # __rf_generic_injector will set fault_injected attribute
                self.__rf_generic_injector()
                break  # avoid execute the else
        else:
            self.fault_injected = False
