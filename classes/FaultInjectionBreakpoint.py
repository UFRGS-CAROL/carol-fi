import random
import gdb
import re
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters as cp  # All common parameters will be at common_parameters module

GDB_TYPES_DICT = {
    gdb.TYPE_CODE_PTR: "The type is a pointer.",
    gdb.TYPE_CODE_ARRAY: "The type is an array.",
    gdb.TYPE_CODE_STRUCT: "The type is a structure.",
    gdb.TYPE_CODE_UNION: "The type is a union.",
    gdb.TYPE_CODE_ENUM: "The type is an enum.",
    gdb.TYPE_CODE_FLAGS: "A bit flags type, used for things such as status registers.",
    gdb.TYPE_CODE_FUNC: "The type is a function.",
    gdb.TYPE_CODE_INT: "The type is an integer type.",
    gdb.TYPE_CODE_FLT: "A floating point type.",
    gdb.TYPE_CODE_VOID: "The special type void.",
    gdb.TYPE_CODE_SET: "A Pascal set type.",
    gdb.TYPE_CODE_RANGE: "A range type, that is, an integer type with bounds.",
    gdb.TYPE_CODE_STRING: "A string type. Note that this is only used for certain languages with "
                          "language-defined string types; C strings are not represented this way.",
    gdb.TYPE_CODE_BITSTRING: "A string of bits. It is deprecated.",
    gdb.TYPE_CODE_ERROR: "An unknown or erroneous type.",
    gdb.TYPE_CODE_METHOD: "A method type, as found in C++ or Java.",
    gdb.TYPE_CODE_METHODPTR: "A pointer-to-member-function.",
    gdb.TYPE_CODE_MEMBERPTR: "A pointer-to-member.",
    gdb.TYPE_CODE_REF: "A reference type.",
    gdb.TYPE_CODE_CHAR: "A character type.",
    gdb.TYPE_CODE_BOOL: "A boolean type.",
    gdb.TYPE_CODE_COMPLEX: "A complex float type.",
    gdb.TYPE_CODE_TYPEDEF: "A typedef to some other type.",
    gdb.TYPE_CODE_NAMESPACE: "A C++ namespace.",
    gdb.TYPE_CODE_DECFLOAT: "A decimal floating point type.",
    gdb.TYPE_CODE_INTERNAL_FUNCTION: "A function internal to gdb. This "
                                     "is the type used to represent convenience functions."
}

"""
Fault injection breakpoint class, will do a flip of the bit(s) when breakpoint is hit
"""


class FaultInjectionBreakpoint(gdb.Breakpoint):
    def __init__(self, *args, **kwargs):
        # If kernel is not accessible it must return
        self.__kludge = kwargs.pop('kludge') if 'kludge' in kwargs else None
        self.__register = kwargs.pop('register') if 'register' in kwargs else None
        self.__bits_to_flip = kwargs.pop('bits_to_flip') if 'bits_to_flip' in kwargs else None
        self.__fault_model = kwargs.pop('fault_model') if 'fault_model' in kwargs else None
        self.__logging = kwargs.pop('logging') if 'logging' in kwargs else None
        self.__injection_mode = kwargs.pop('injection_mode') if 'injection_mode' in kwargs else None

        super(FaultInjectionBreakpoint, self).__init__(*args, **kwargs)

    def stop(self):
        if self.__kludge:
            return True

        # This if avoid the creation of another event connection
        # for some reason gdb cannot breakpoint addresses before
        # a normal breakpoint is hit
        self.__logging.debug("Trying Fault Injection")

        # Focusing the thread
        if not self.__thread_focus():
            # If it return False breakpoint is going to be repeated
            return True

        try:
            # RF is the default mode of injection
            if self.__injection_mode == 'RF' or self.__injection_mode is None:
                # Do the fault injection magic
                fault_injected = self.__rf_generic_injector()
                if fault_injected:
                    self.__logging.info("Fault Injection Successful")
                else:
                    self.__logging.info("Fault Injection Went Wrong")

            elif self.__injection_mode == 'VARS':
                self.__var_generic_injector()

            elif self.__injection_mode == 'INST':
                raise NotImplementedError("INST INJECTION MODE NOT IMPLEMENTED YET")

        except Exception as err:
            self.__logging.exception("fault_injection_python_exception: {}".format(err))
            self.__logging.exception("Fault Injection Went Wrong")
        return True

    """
    Selects a valid thread for a specific
    kernel
    return the coordinates for the block
    and the thread
    """

    def __thread_focus(self):
        # Selecting the block
        try:
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
                "CUDA_BLOCK_FOCUS: " + str(block_focus).replace("[", "").replace("]", "").strip())

        except Exception as err:
            self.__logging.exception("CUDA_BLOCK_FOCUS_EXCEPTION: " + str(err))
            self.__logging.exception("Fault Injection Went Wrong")
            return False

        # Selecting the thread
        try:
            threads = cf.execute_command(gdb=gdb, to_execute="info cuda threads")
            thread = None
            thread_len = len(threads)
            print("TEST1", thread, thread_len)

            while not thread:
                thread_index = random.randint(0, thread_len)
                if 'running' in threads[thread_index] and '*' not in threads[thread_index]:
                    pattern = ".*\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*"
                    pattern += "\((\d+),(\d+),(\d+)\).*\((\d+),(\d+),(\d+)\).*"
                    m = re.match(pattern, threads[thread_index])
                    if m:
                        thread = "{},{},{}".format(m.group(10), m.group(11), m.group(12))
            print("TEST", thread)

            change_focus_thread_cmd = "cuda thread {}".format(thread)
            thread_focus = cf.execute_command(gdb=gdb, to_execute=change_focus_thread_cmd)

            # Thread focus return information
            self.__logging.info(
                "CUDA_THREAD_FOCUS: " + str(thread_focus).replace("[", "").replace("]", "").strip())

        except Exception as err:
            self.__logging.exception("CUDA_THREAD_FOCUS_EXCEPTION: " + str(err))
            self.__logging.exception("Fault Injection Went Wrong")
            return False

        return True

    """
    Flip a bit or multiple bits based on a fault model
    """

    def __rf_generic_injector(self):
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
                reg_content_new = self.__flip_a_bit(int(self.__bits_to_flip[0]), reg_content_old)

            # Double bit flip
            elif self.__fault_model == 1:
                # multiple bit flip
                reg_content_new = reg_content_old
                for bit_to_flip in self.__bits_to_flip:
                    reg_content_new = self.__flip_a_bit(int(bit_to_flip), reg_content_new)

            # Random value
            elif self.__fault_model == 2:
                # random value is stored at bits_to_flip[0]
                reg_content_new = self.__bits_to_flip[0]

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
    Instructions generic injector
    """

    def __inst_generic_injector(self):
        raise NotImplementedError

    """
    Variable generic injector
    """

    def __var_generic_injector(self):
        raise NotImplementedError

        # """
        # Flip only a bit in a register content
        # """
        #
        # @staticmethod
        # def __flip_a_bit(bit_to_flip, reg_content):
        #     new_bit = '0' if reg_content[bit_to_flip] == '1' else '1'
        #     reg_content = reg_content[:bit_to_flip] + new_bit + reg_content[bit_to_flip + 1:]
        #     return reg_content
        #
        #
        # @staticmethod
        # def __single_bit_flip_word_address(address, byte_sizeof):
        #     buf_fog = "Fault Model: Single bit-flip"
        #     buf_fog += "\n"
        #     buf_fog += "base address to flip value: " + str(address)
        #     print(buf_fog)
        #     random.seed()
        #     address_offset = random.randint(0, byte_sizeof - 1)
        #     address_f = hex(int(address, 16) + address_offset)
        #     x_mem = "x/1tb " + str(address_f)
        #     bin_data = gdb.execute(x_mem, to_string=True)
        #     bin_data = re.sub(".*:|\s", "", bin_data)
        #     bin_data_l = list(bin_data)
        #     bit_pos = random.randint(0, len(bin_data_l) - 1)
        #     if bin_data_l[bit_pos] == '1':
        #         bin_data_l[bit_pos] = '0'
        #     else:
        #         bin_data_l[bit_pos] = '1'
        #     bin_data = ''.join(bin_data_l)
        #     set_cmd = "set {char}" + address_f + " = " + hex(int(bin_data, 2))
        #     gdb.execute(set_cmd)
        #
        # @staticmethod
        # def __show_memory_content(address, byte_sizeof):
        #     x_mem = "x/" + str(byte_sizeof) + "xb " + address
        #     hex_data = gdb.execute(x_mem, to_string=True)
        #     hex_data = re.sub(".*:|\s", "", hex_data)
        #     return hex_data
        #
        # def __generic_bit_flip(self, value):
        #     address = re.sub("<.*>|\".*\"", "", str(value.address))
        #     byte_sizeof = value.type.strip_typedefs().sizeof
        #     print("Memory content before bitflip:" + str(self.__show_memory_content(address, byte_sizeof)))
        #
        #     if self.__fault_model == 0:
        #         self.__single_bit_flip_word_address(address, byte_sizeof)
        #     elif self.__fault_model == 1:
        #         raise NotImplementedError("Fault model not implemented yet")
        #     elif self.__fault_model == 2:
        #         raise NotImplementedError("Fault model not implemented yet")
        #     elif self.__fault_model == 3:
        #         raise NotImplementedError("Fault model not implemented yet")
        #     elif self.__fault_model == 4:
        #         raise NotImplementedError("Fault model not implemented yet")
        #     print("Memory content after  bitflip:" + str(self.__show_memory_content(address, byte_sizeof)))
        #
        # def __chose_frame_to_flip(self, frame_symbols):
        #     try:
        #         frames_num = len(frame_symbols)
        #         if frames_num <= 0:
        #             return False
        #
        #         random.seed()
        #         frame_pos = random.randint(0, frames_num - 1)
        #         frame = frame_symbols[frame_pos][0]
        #         symbols = frame_symbols[frame_pos][1]
        #         symbols_num = len(symbols)
        #
        #         while symbols_num <= 0:
        #             frame_symbols.pop(frame_pos)
        #             frames_num += 1
        #             if frames_num <= 0:
        #                 return False
        #
        #             frame_pos = random.randint(0, frames_num - 1)
        #             frame = frame_symbols[frame_pos][0]
        #             symbols = frame_symbols[frame_pos][1]
        #             symbols_num = len(symbols)
        #
        #         symbol_pos = random.randint(0, symbols_num - 1)
        #         symbol = symbols[symbol_pos]
        #         var_gdb = symbol.value(frame)
        #
        #         try:
        #             self.__var_bit_flip_value(var_gdb)
        #             if var_gdb.type.strip_typedefs().code is gdb.TYPE_CODE_RANGE:
        #                 print("Type range: " + str(var_gdb.type.strip_typedefs().range()))
        #
        #             try:
        #                 for field in symbol.type.fields():
        #                     print("Field name: " + str(field.name))
        #                     print("Field Type: " + str(GDB_TYPES_DICT[field.type.strip_typedefs().code]))
        #                     print("Field Type sizeof: " + str(field.type.strip_typedefs().sizeof))
        #                     if field.type.strip_typedefs().code is gdb.TYPE_CODE_RANGE:
        #                         print("Field Type range: " + str(field.type.strip_typedefs().range()))
        #             except:
        #                 pass
        #             return True
        #         except gdb.error as err:
        #             print("gdbException: " + str(err))
        #             return False
        #
        #     except Exception as err:
        #         print("pythonException: " + str(err))
        #         return False
        #
        # def __var_bit_flip_value(self, value):
        #
        #     if value.type.strip_typedefs().code is gdb.TYPE_CODE_PTR:
        #         random.seed()
        #         pointer_flip = random.randint(0, 1)
        #         pointed_address = re.sub("<.*>|\".*\"", "", str(value.referenced_value().address))
        #         if pointer_flip or hex(int(pointed_address, 16)) <= hex(int("0x0", 16)):
        #             print("Flipping a bit of the pointer")
        #             self.__generic_bit_flip(value)
        #         else:
        #             print("Flipping a bit of the value pointed by a pointer")
        #             self.__bit_flip_value(value.referenced_value())
        #     elif value.type.strip_typedefs().code is gdb.TYPE_CODE_REF:
        #         random.seed()
        #         ref_flip = random.randint(0, 1)
        #         pointed_address = re.sub("<.*>|\".*\"", "", str(value.referenced_value().address))
        #         if ref_flip or hex(int(pointed_address, 16)) <= hex(int("0x0", 16)):
        #             print("Flipping a bit of the reference")
        #             self.__generic_bit_flip(value)
        #         else:
        #             print("Flipping a bit of the value pointed by a reference")
        #             self.__bit_flip_value(value.referenced_value())
        #     elif value.type.strip_typedefs().code is gdb.TYPE_CODE_ARRAY:
        #         range_max = value.type.strip_typedefs().range()[1]
        #         random.seed()
        #         array_pos = random.randint(0, range_max)
        #         print("Flipping array at pos: " + str(array_pos))
        #         self.__bit_flip_value(value[array_pos])
        #     elif value.type.strip_typedefs().code is gdb.TYPE_CODE_STRUCT:
        #         fields = value.type.fields()
        #         if not fields:
        #             self.__generic_bit_flip(value)
        #         random.seed()
        #         field_pos = random.randint(0, len(fields) - 1)
        #         new_value = value[fields[field_pos]]
        #         count = 0
        #         new_address = re.sub("<.*>|\".*\"", "", str(new_value.address))
        #         while new_value.address is None or new_value.is_optimized_out or hex(int(new_address, 16)) <= hex(
        #                 int("0x0", 16)):
        #             random.seed()
        #             field_pos = random.randint(0, len(fields) - 1)
        #             new_value = value[fields[field_pos]]
        #             new_address = re.sub("<.*>|\".*\"", "", str(new_value.address))
        #             count += 1
        #             if count == 20:
        #                 raise Exception("Unable to exit loop in struct fields; Exiting wihtout making a bit flip")
        #
        #         print("Flipping value of field: " + str(fields[field_pos].name))
        #         self.__bit_Flip_value(new_value)
        #     elif value.type.strip_typedefs().code is gdb.TYPE_CODE_UNION:
        #         fields = value.type.fields()
        #         random.seed()
        #         field_pos = random.randint(0, len(fields) - 1)
        #         new_value = value[fields[field_pos]]
        #         count = 0
        #         new_address = re.sub("<.*>|\".*\"", "", str(new_value.address))
        #         while new_value.address is None or new_value.is_optimized_out or hex(int(new_address, 16)) <= hex(
        #                 int("0x0", 16)):
        #             random.seed()
        #             field_pos = random.randint(0, len(fields) - 1)
        #             new_value = value[fields[field_pos]]
        #             count += 1
        #             if count == 20:
        #                 # logMsg(str("Error: unable to exit loop in union fields; Exiting wihtout making bitflip"))
        #                 # return
        #                 raise Exception("Unable to exit loop in union fields; Exiting wihtout making bitflip")
        #
        #         print("Flipping value of field name: " + str(fields[field_pos].name))
        #         self.__bit_flip_value(new_value)
        #     else:
        #         print("Generic bit flip")
        #         self.__generic_bit_flip(value)
        #
        # """
        #  generic injector
        # """
        #
        # def __var_generic_injector(self):
        #     inferior = gdb.selected_inferior()
        #
        #     for inf in gdb.inferiors():
        #         print("Inferior PID: " + str(inf.pid))
        #         print("Inferior is valid: " + str(inf.is_valid()))
        #         print("Inferior #threads: " + str(len(inf.threads())))
        #
        #     print("Backtrace BEGIN:")
        #     bt = gdb.execute("bt", to_string=True)
        #     print(bt)
        #     source_lines = gdb.execute("list", to_string=True)
        #     print(source_lines)
        #
        #     threads_symbols = list()
        #     for th in inferior.threads():
        #         print("FOR INFERIOR THREADS")
        #         try:
        #             th.switch()
        #             th_symbols = self.__get_all_valid_symbols()
        #             if len(th_symbols) > 0:
        #                 print("TH SYMBOLS APPEND")
        #
        #                 threads_symbols.append([th, th_symbols])
        #         except Exception as err:
        #             print(err)
        #             print("ERROR ON THREAD INFERIORS")
        #             continue
        #         th_len = len(threads_symbols)
        #         print("AFTER THREAD LEN")
        #         if th_len <= 0:
        #             print(str("No Threads with symbols"))
        #             return False
        #
        #         th_pos = random.randint(0, th_len - 1)
        #         print("AFTER THREAD rand int")
        #         cur_thread = threads_symbols[th_pos][0]
        #         print("Thread name: " + str(cur_thread.name))
        #         print("Thread num: " + str(cur_thread.num))
        #         print("Thread ptid: " + str(cur_thread.ptid))
        #         r = self.__chose_frame_to_flip(threads_symbols[th_pos][1])
        #         while r is False:
        #             threads_symbols.pop(th_pos)
        #             th_len -= 1
        #             if th_len <= 0:
        #                 break
        #             th_pos = random.randint(0, th_len - 1)
        #             try:
        #                 r = self.__chose_frame_to_flip(threads_symbols[th_pos][1])
        #             except Exception as err:
        #                 print(err)
        #                 r = False
        #
        #         return r
        #
        # """
        # Get all the symbols of the stacked frames, returns a list of tuples [frame, symbolsList]
        # where frame is a GDB Frame object and symbolsList is a list of all symbols of this frame
        # """
        #
        # def __get_all_valid_symbols(self):
        #     all_symbols = list()
        #     frame = gdb.selected_frame()
        #     while frame:
        #         # Cuda dgb behavior bad if this is not here
        #         if 'main' in frame.name():
        #             break
        #
        #         print("SELECTING NEW FRAME")
        #         print(frame.is_valid(), frame.name(), frame.architecture(), frame.type())
        #
        #         symbols = self.__get_frame_symbols(frame)
        #         if symbols is not None:
        #             all_symbols.append([frame, symbols])
        #         print("GETTING OLDER")
        #         frame = frame.older()
        #
        #     print("RETURNING ALL SYMBOLS")
        #     return all_symbols
        #
        # """
        # Returns a list of all symbols of the frame, frame is a GDB Frame object
        # """
        #
        # def __get_frame_symbols(self, frame):
        #     try:
        #         symbols = list()
        #         block = frame.block()
        #         while block:
        #             for symbol in block:
        #                 if self.__is_bit_flip_possible(symbol, frame):
        #                     symbols.append(symbol)
        #             block = block.superblock
        #         return symbols
        #     except Exception as err:
        #         print("GET_FRAME_SYMBOLS_ERROR: {}".format(err))
        #         return None
        #
        # """
        #      Returns True if we can bitflip some bit of this symbol, i.e. if this is a variable or
        #      constant and not functions and another symbols
        # """
        #
        # @staticmethod
        # def __is_bit_flip_possible(symbol, frame):
        #     if symbol.is_variable or symbol.is_constant or symbol.is_argument:
        #         var_GDB = symbol.value(frame)
        #         address = re.sub("<.*>|\".*\"", "", str(var_GDB.address))
        #         if var_GDB.address is not None and not var_GDB.is_optimized_out and hex(int(address, 16)) > hex(
        #                 int("0x0", 16)):
        #             print("BIT FLIP IS POSSIBLE")
        #             return True
        #     return False
