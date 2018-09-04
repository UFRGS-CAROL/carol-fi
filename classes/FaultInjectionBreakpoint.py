from inspect import currentframe
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
        self.__logging.debug("Trying Fault Injection with {} mode".format(self.__injection_mode))
        try:
            # Focusing the thread
            self.__thread_focus()
        except Exception as err:
            # Even if CUDA focus was not successful we keep going
            self.__logging.exception("CUDA_FOCUS_CANNOT_BE_REQUESTED. KEEP GOING, with error {}".format(err))

        try:
            # Register if fault was injected or not
            fault_injected = False
            # Do the fault injection magic
            # RF is the default mode of injection
            if 'RF' in self.__injection_mode or self.__injection_mode is None:
                fault_injected = self.__rf_generic_injector()
            elif 'VARS' in self.__injection_mode:
                fault_injected = self.__var_generic_injector()
            elif 'INST' in self.__injection_mode:
                fault_injected = self.__inst_generic_injector()

            # Test fault injection result
            if fault_injected:
                self.__logging.info("Fault Injection Successful")
            else:
                self.__logging.info("Fault Injection Went Wrong")

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
            "CUDA_THREAD_FOCUS: " + str(thread_focus).replace("[", "").replace("]", "").strip())

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
     generic injector
    """

    def __var_generic_injector(self):
        self.__logging.debug("VAR GENERIC INJECTOR")
        # inferior = gdb.selected_inferior()

        for inf in gdb.inferiors():
            self.__logging.debug("Inferior PID: " + str(inf.pid))
            self.__logging.debug("Inferior is valid: " + str(inf.is_valid()))
            self.__logging.debug("Inferior #threads: " + str(len(inf.threads())))

        self.__logging.debug("Backtrace BEGIN:")
        bt = gdb.execute("bt", to_string=True)
        self.__logging.debug(bt)
        source_lines = gdb.execute("list", to_string=True)
        self.__logging.debug(source_lines)

        self.__logging.debug("FOR INFERIOR THREADS")
        threads_symbols = self.__get_all_valid_symbols()
        if len(threads_symbols) > 0:
            self.__logging.debug("TH SYMBOLS APPEND")

        self.__logging.debug("Thread name: " + str(self.thread.name))
        self.__logging.debug("Thread num: " + str(self.thread.num))
        self.__logging.debug("Thread ptid: " + str(self.thread.ptid))
        return self.__chose_frame_to_flip(threads_symbols)

    """
    Get all the symbols of the stacked frames, returns a list of tuples [frame, symbolsList]
    where frame is a GDB Frame object and symbolsList is a list of all symbols of this frame
    """

    def __get_all_valid_symbols(self):
        frame = gdb.selected_frame()
        symbols = self.__get_frame_symbols(frame)
        return symbols

    """
    Returns a list of all symbols of the frame, frame is a GDB Frame object
    """

    def __get_frame_symbols(self, frame):
        try:
            symbols = list()
            block = frame.block()
            while block:
                for symbol in block:
                    if self.__is_bit_flip_possible(symbol, frame):
                        symbols.append(symbol)
                block = block.superblock
            return symbols
        except Exception as err:
            self.__logging.exception("GET_FRAME_SYMBOLS_ERROR: {}".format(err))
            return None

    """
         Returns True if we can bitflip some bit of this symbol, i.e. if this is a variable or
         constant and not functions and another symbols
    """

    def __is_bit_flip_possible(self, symbol, frame):
        if symbol.is_variable or symbol.is_constant or symbol.is_argument:
            var = symbol.value(frame)
            address = re.sub("<.*>|\".*\"", "", str(var.address))
            if var.address is not None and not var.is_optimized_out and hex(int(address, 16)) > hex(
                    int("0x0", 16)):
                self.__logging.debug("BIT FLIP IS POSSIBLE")
                return True
        return False

    def __single_bit_flip_word_address(self, address, byte_sizeof):
        buf_fog = "Fault Model: Single bit-flip"
        buf_fog += "\n"
        buf_fog += "base address to flip value: " + str(address)
        self.__logging.debug(buf_fog)
        random.seed()
        address_offset = random.randint(0, byte_sizeof - 1)
        address_f = hex(int(address, 16) + address_offset)
        x_mem = "x/1tb " + str(address_f)
        bin_data = gdb.execute(x_mem, to_string=True)
        bin_data = re.sub(".*:|\s", "", bin_data)
        bin_data_l = list(bin_data)
        bit_pos = random.randint(0, len(bin_data_l) - 1)
        if bin_data_l[bit_pos] == '1':
            bin_data_l[bit_pos] = '0'
        else:
            bin_data_l[bit_pos] = '1'
        bin_data = ''.join(bin_data_l)
        set_cmd = "set {char}" + address_f + " = " + hex(int(bin_data, 2))
        gdb.execute(set_cmd)

    @staticmethod
    def __show_memory_content(address, byte_sizeof):
        x_mem = "x/" + str(byte_sizeof) + "xb " + address
        hex_data = gdb.execute(x_mem, to_string=True)
        hex_data = re.sub(".*:|\s", "", hex_data)
        return hex_data

    def __generic_bit_flip(self, value):
        address = re.sub("<.*>|\".*\"", "", str(value.address))
        byte_sizeof = value.type.strip_typedefs().sizeof
        self.__logging.debug("old_value:{}".format(self.__show_memory_content(address, byte_sizeof)))

        if self.__fault_model == 0:
            self.__single_bit_flip_word_address(address, byte_sizeof)
        elif self.__fault_model == 1:
            raise NotImplementedError("Fault model not implemented yet")
        elif self.__fault_model == 2:
            raise NotImplementedError("Fault model not implemented yet")
        elif self.__fault_model == 3:
            raise NotImplementedError("Fault model not implemented yet")
        elif self.__fault_model == 4:
            raise NotImplementedError("Fault model not implemented yet")
        self.__logging.debug("new_value:{}".format(self.__show_memory_content(address, byte_sizeof)))

    def __chose_frame_to_flip(self, frame_symbols):
        frames_num = len(frame_symbols)
        if frames_num <= 0:
            return False

        self.__logging.debug("INSIDE CHOOSED FRAME TO FLIP FRAME POS {}".format(frames_num))
        random.seed()
        symbols = frame_symbols
        symbols_num = len(symbols)

        symbol_pos = random.randint(0, symbols_num - 1)
        symbol = symbols[symbol_pos]
        var_gdb = symbol.value(gdb.selected_frame())
        # Testing if I can access GDB registers
        self.__logging.info("TEST VAR GDB {}".format(var_gdb))
        self.__logging.info(
            "SYMTAB {}\nis_valid() {}\n".format(symbol.symtab, symbol.symtab.is_valid()))
        self.__logging.info(
            "Filename {}\nObjfile {}\nproducer {}\nfullname {}\nglobal block {}\nstatic block {}linetable {}".format(
                symbol.symtab.filename, symbol.symtab.objfile, symbol.symtab.producer, symbol.symtab.is_valid(),
                symbol.symtab.fullname(), symbol.symtab.global_block(), symbol.symtab.static_block(),
                symbol.symtab.linetable()))

        self.__logging.info("TEST SYMBOL ATTRIBUTES")
        self.__logging.info(
            "Symbol type {}\nline {}\nname {}\nlinkage_name {}\nprint_name {}\naddr_class {}\nneeds_frame {}\n".format(
                symbol.type, symbol.line, symbol.name, symbol.linkage_name, symbol.print_name, symbol.addr_class,
                symbol.needs_frame))

        self.__var_bit_flip_value(var_gdb)
        if var_gdb.type.strip_typedefs().code is gdb.TYPE_CODE_RANGE:
            self.__logging.debug("Type range: " + str(var_gdb.type.strip_typedefs().range()))

        # If it is an structure it has fields
        try:
            for field in symbol.type.fields():
                self.__logging.debug("Field name: " + str(field.name))
                self.__logging.debug("Field Type: " + str(GDB_TYPES_DICT[field.type.strip_typedefs().code]))
                self.__logging.debug("Field Type sizeof: " + str(field.type.strip_typedefs().sizeof))
                if field.type.strip_typedefs().code is gdb.TYPE_CODE_RANGE:
                    self.__logging.debug("Field Type range: " + str(field.type.strip_typedefs().range()))
        except Exception as err:
            self.__logging.debug("ERR {} LINE {}".format(err, currentframe().f_back.f_lineno))

        return True

    def __var_bit_flip_value(self, value):
        self.__logging.debug("{}. VALUE {}".format(GDB_TYPES_DICT[value.type.strip_typedefs().code], value))
        if value.type.strip_typedefs().code is gdb.TYPE_CODE_PTR:
            random.seed()
            pointer_flip = random.randint(0, 1)
            pointed_address = re.sub("<.*>|\".*\"", "", str(value.referenced_value().address))
            if pointer_flip or hex(int(pointed_address, 16)) <= hex(int("0x0", 16)):
                self.__logging.debug("Flipping a bit of the pointer")
                self.__generic_bit_flip(value)
            else:
                self.__logging.debug("Flipping a bit of the value pointed by a pointer")
                self.__var_bit_flip_value(value.referenced_value())
        elif value.type.strip_typedefs().code is gdb.TYPE_CODE_REF:
            random.seed()
            ref_flip = random.randint(0, 1)
            pointed_address = re.sub("<.*>|\".*\"", "", str(value.referenced_value().address))
            if ref_flip or hex(int(pointed_address, 16)) <= hex(int("0x0", 16)):
                self.__logging.debug("Flipping a bit of the reference")
                self.__generic_bit_flip(value)
            else:
                self.__logging.debug("Flipping a bit of the value pointed by a reference")
                self.__var_bit_flip_value(value.referenced_value())
        elif value.type.strip_typedefs().code is gdb.TYPE_CODE_ARRAY:
            range_max = value.type.strip_typedefs().range()[1]
            random.seed()
            array_pos = random.randint(0, range_max)
            self.__logging.debug("Flipping array at pos: " + str(array_pos))
            self.__var_bit_flip_value(value[array_pos])
        elif value.type.strip_typedefs().code is gdb.TYPE_CODE_STRUCT:
            fields = value.type.fields()
            if not fields:
                self.__generic_bit_flip(value)
            random.seed()
            field_pos = random.randint(0, len(fields) - 1)
            new_value = value[fields[field_pos]]
            count = 0
            new_address = re.sub("<.*>|\".*\"", "", str(new_value.address))
            while new_value.address is None or new_value.is_optimized_out or hex(int(new_address, 16)) <= hex(
                    int("0x0", 16)):
                random.seed()
                field_pos = random.randint(0, len(fields) - 1)
                new_value = value[fields[field_pos]]
                new_address = re.sub("<.*>|\".*\"", "", str(new_value.address))
                count += 1
                if count == 20:
                    raise Exception("Unable to exit loop in struct fields; Exiting wihtout making a bit flip")

            self.__logging.debug("Flipping value of field: " + str(fields[field_pos].name))
            self.__var_bit_flip_value(new_value)
        elif value.type.strip_typedefs().code is gdb.TYPE_CODE_UNION:
            fields = value.type.fields()
            random.seed()
            field_pos = random.randint(0, len(fields) - 1)
            new_value = value[fields[field_pos]]
            count = 0
            new_address = re.sub("<.*>|\".*\"", "", str(new_value.address))
            while new_value.address is None or new_value.is_optimized_out or hex(int(new_address, 16)) <= hex(
                    int("0x0", 16)):
                random.seed()
                field_pos = random.randint(0, len(fields) - 1)
                new_value = value[fields[field_pos]]
                count += 1
                if count == 20:
                    # logMsg(str("Error: unable to exit loop in union fields; Exiting wihtout making bitflip"))
                    # return
                    raise Exception("Unable to exit loop in union fields; Exiting wihtout making bitflip")

            self.__logging.debug("Flipping value of field name: " + str(fields[field_pos].name))
            self.__var_bit_flip_value(new_value)
        else:
            self.__logging.debug("Generic bit flip")
            self.__generic_bit_flip(value)

    """
    Instructions generic injector
    """

    def __inst_generic_injector(self):
        raise NotImplementedError
