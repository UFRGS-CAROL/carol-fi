import random
import gdb
import re
import os
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters


class Breakpoint(gdb.Breakpoint):
    def __init__(self, block, thread, register, bits_to_flip, fault_model, logging, *args, **kwargs):
        super(Breakpoint, self).__init__(*args, **kwargs)
        self.__block = block
        self.__thread = thread
        self.__register = register
        self.__bits_to_flip = bits_to_flip
        self.__fault_model = fault_model
        self.__logging = logging

    def stop(self):
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
        logging.info(str("exit code: %d" % event.exit_code))
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
     flip_log_file, debug, gdb_init_strings, inj_type] = str(os.environ['CAROL_FI_INFO']).split('|')

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
    breakpoint_kernel_line = Breakpoint(block, thread, register, bits_to_flip, fault_model, logging,
                                        spec=breakpoint_location, type=gdb.BP_BREAKPOINT)  # , temporary=True)

    # Start app execution
    gdb.execute("r")

    # Delete the breakpoint
    breakpoint_kernel_line.delete()
    del breakpoint_kernel_line

    # Continue execution until the next breakpoint
    gdb.execute("c")


# Call main execution
logging = None
main()


# """
# function called when the execution is stopped by a breakpoint
# """
#
#
# def fault_injection_breakpoint(event):
#     global global_valid_block, global_valid_thread, global_valid_register
#     global global_bits_to_flip, global_fault_model, global_logging
#     global ready_to_inject
#
#     # if not ready_to_inject:
#     #     return
#
#     # This if avoid the creation of another event connection
#     # for some reason gdb cannot breakpoint addresses before
#     # a normal breakpoint is hit
#     global_logging.debug("Trying Fault Injection")
#     inferior = gdb.selected_inferior()
#
#     threadsSymbols = []
#
#     for th in inferior.threads():
#         print(dir(th))
#         try:
#             th.switch()
#             thSymbols = getAllValidSymbols()
#             if len(thSymbols) > 0:
#                 threadsSymbols.append([th, thSymbols])
#         except:
#             continue
#
#
#             # try:
#             #     change_focus_cmd = "cuda kernel 0 block {0},{1},{2} thread {3},{4},{5}".format(str(global_valid_block[0]),
#             #                                                                                    str(global_valid_block[1]),
#             #                                                                                    str(global_valid_block[2]),
#             #                                                                                    str(global_valid_thread[0]),
#             #                                                                                    str(global_valid_thread[1]),
#             #                                                                                    str(global_valid_thread[2]))
#             #     thread_focus = gdb.execute(change_focus_cmd, to_string=True)
#             #
#             # except Exception as err:
#             #     global_logging.exception("CUDA_FOCUS_exception: " + str(err))
#             #     global_logging.exception("Fault Injection Went Wrong")
#             #     return
#             #
#             # try:
#             #     # Thread focus return information
#             #     global_logging.info(str(thread_focus).replace("[", "").replace("]", "").strip())
#             #
#             #     # Do the fault injection magic
#             #     generic_injector(global_valid_register, global_bits_to_flip, global_fault_model)
#             #
#             #     global_logging.info("Fault Injection Successful")
#             # except Exception as err:
#             #     global_logging.exception("fault_injection_python_exception: " + str(err))
#             #     global_logging.exception("Fault Injection Went Wrong")
#
# frame = gdb.selected_frame()
# block = frame.block()
# names = set()
# symbols = []
# while block:
#     for symbol in block:
#         if (symbol.is_argument or symbol.is_variable):
#             name = symbol.name
#             if not name in names and symbol is not None:
#                 # print('{} = {}'.format(name, symbol.value(frame)))
#                 # print(symbol.name, symbol.is_variable, symbol.value, symbol.addr_class,
#                 #       symbol.line, symbol.value(frame).type.strip_typedefs().code)
#                 symbols.append(symbol)
#                 names.add(name)
#     block = block.superblock
#
# pos = random.randint(0, len(symbols))
# print(symbols[pos].value(frame))
# print(bitFlipValue(symbols[pos].value(frame)))
# return True

def genericBitFlip(value):
    global global_fault_model
    tag = "genericBitFlip"
    bufLog = ""

    address = re.sub("<.*>|\".*\"", "", str(value.address))
    byteSizeof = value.type.strip_typedefs().sizeof
    bufLog += "Memory content before bitflip:" + str(showMemoryContent(address, byteSizeof))
    bufLog += "\n"
    choice = int(global_fault_model)
    if choice == 0:
        bufLog += singleBitFlipWordAddress(address, byteSizeof)
    elif choice == 1:
        bufLog += doubleBitFlipWordAddress(address, byteSizeof)
    elif choice == 2:
        bufLog += randomBitFlipWordAddress(address, byteSizeof)
    elif choice == 3:
        bufLog += zeroBitFlipWordAddress(address, byteSizeof)
    elif choice == 4:
        bufLog += LSBFlipWordAddress(address, byteSizeof)
    bufLog += "Memory content after  bitflip:" + str(showMemoryContent(address, byteSizeof))
    bufLog += "\n"
    return bufLog


def LSBFlipWordAddress(address, byteSizeof):
    tag = "LSBBitFlip"
    bufLog = ""
    bufLog += "Fault Model: LSB bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: " + str(address)
    bufLog += "\n"
    bufLog += "address max offset: " + str(byteSizeof)
    bufLog += "\n"
    addressOffset = byteSizeof - 1  # get the least significant byte only
    addressF = hex(int(address, 16) + addressOffset)
    xMem = "x/1tb " + str(addressF)
    binData = gdb.execute(xMem, to_string=True)
    binData = re.sub(".*:|\s", "", binData)
    binDatal = list(binData)
    bitPos = random.randint(0, len(binDatal) - 1)
    if binDatal[bitPos] == '1':
        binDatal[bitPos] = '0'
    else:
        binDatal[bitPos] = '1'
    binData = ''.join(binDatal)
    setCmd = "set {char}" + addressF + " = " + hex(int(binData, 2))
    gdb.execute(setCmd)
    return bufLog


def bitFlipValue(value):
    tag = "bitFlipValue"
    bufLog = ""
    if value.type.strip_typedefs().code is gdb.TYPE_CODE_PTR:
        random.seed()
        pointerFlip = random.randint(0, 1)
        pointedAddress = re.sub("<.*>|\".*\"", "", str(value.referenced_value().address))
        if pointerFlip or hex(int(pointedAddress, 16)) <= hex(int("0x0", 16)):
            bufLog += str("Fliping a bit of the pointer")
            bufLog += "\n"
            bufLog += genericBitFlip(value)
        else:
            bufLog += str("Fliping a bit of the value pointed by a pointer")
            bufLog += "\n"
            bufLog += bitFlipValue(value.referenced_value())
    elif value.type.strip_typedefs().code is gdb.TYPE_CODE_REF:
        random.seed()
        refFlip = random.randint(0, 1)
        pointedAddress = re.sub("<.*>|\".*\"", "", str(value.referenced_value().address))
        if refFlip or hex(int(pointedAddress, 16)) <= hex(int("0x0", 16)):
            bufLog += str("Fliping a bit of the reference")
            bufLog += "\n"
            bufLog += genericBitFlip(value)
        else:
            bufLog += str("Fliping a bit of the value pointed by a reference")
            bufLog += "\n"
            bufLog += bitFlipValue(value.referenced_value())
    elif value.type.strip_typedefs().code is gdb.TYPE_CODE_ARRAY:
        rangeMax = value.type.strip_typedefs().range()[1]
        random.seed()
        arrayPos = random.randint(0, rangeMax)
        bufLog += "Fliping array at pos: " + str(arrayPos)
        bufLog += "\n"
        bufLog += bitFlipValue(value[arrayPos])
    elif value.type.strip_typedefs().code is gdb.TYPE_CODE_STRUCT:
        fields = value.type.fields()
        if not fields:
            bufLog += genericBitFlip(value)
        random.seed()
        fieldPos = random.randint(0, len(fields) - 1)
        newValue = value[fields[fieldPos]]
        count = 0
        newAddress = re.sub("<.*>|\".*\"", "", str(newValue.address))
        while newValue.address is None or newValue.is_optimized_out or hex(int(newAddress, 16)) <= hex(int("0x0", 16)):
            random.seed()
            fieldPos = random.randint(0, len(fields) - 1)
            newValue = value[fields[fieldPos]]
            newAddress = re.sub("<.*>|\".*\"", "", str(newValue.address))
            count += 1
            if count == 20:
                raise Exception("Unable to exit loop in struct fields; Exiting wihtout making a bit flip")

        bufLog += "Fliping value of field: " + str(fields[fieldPos].name)
        bufLog += "\n"
        bufLog += bitFlipValue(newValue)
    elif value.type.strip_typedefs().code is gdb.TYPE_CODE_UNION:
        fields = value.type.fields()
        random.seed()
        fieldPos = random.randint(0, len(fields) - 1)
        newValue = value[fields[fieldPos]]
        count = 0
        newAddress = re.sub("<.*>|\".*\"", "", str(newValue.address))
        while newValue.address is None or newValue.is_optimized_out or hex(int(newAddress, 16)) <= hex(int("0x0", 16)):
            random.seed()
            fieldPos = random.randint(0, len(fields) - 1)
            newValue = value[fields[fieldPos]]
            count += 1
            if count == 20:
                # logMsg(str("Error: unable to exit loop in union fields; Exiting wihtout making bitflip"))
                # return
                raise Exception("Unable to exit loop in union fields; Exiting wihtout making bitflip")

        bufLog += "Fliping value of field name: " + str(fields[fieldPos].name)
        bufLog += "\n"
        bufLog += bitFlipValue(newValue)
    else:
        bufLog += genericBitFlip(value)

    return bufLog


def singleBitFlipWordAddress(address, byteSizeof):
    tag = "singleBitFlip"
    bufLog = ""
    bufLog += "Fault Model: Single bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: " + str(address)
    bufLog += "\n"
    bufLog += "address max offset: " + str(byteSizeof)
    bufLog += "\n"
    random.seed()
    addressOffset = random.randint(0, byteSizeof - 1)
    addressF = hex(int(address, 16) + addressOffset)
    xMem = "x/1tb " + str(addressF)
    binData = gdb.execute(xMem, to_string=True)
    binData = re.sub(".*:|\s", "", binData)
    binDatal = list(binData)
    bitPos = random.randint(0, len(binDatal) - 1)
    if binDatal[bitPos] == '1':
        binDatal[bitPos] = '0'
    else:
        binDatal[bitPos] = '1'
    binData = ''.join(binDatal)
    setCmd = "set {char}" + addressF + " = " + hex(int(binData, 2))
    gdb.execute(setCmd)
    return bufLog


def doubleBitFlipWordAddress(address, byteSizeof):
    tag = "doubleBitFlip"
    bufLog = ""
    bufLog += "Fault Model: Double bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: " + str(address)
    bufLog += "\n"
    bufLog += "address max offset: " + str(byteSizeof)
    bufLog += "\n"
    random.seed()
    addressOffset = random.randint(0, byteSizeof - 1)
    addressF = hex(int(address, 16) + addressOffset)
    xMem = "x/1tb " + str(addressF)
    binData = gdb.execute(xMem, to_string=True)
    binData = re.sub(".*:|\s", "", binData)
    binDatal = list(binData)
    bitPos = random.randint(0, len(binDatal) - 1)
    bitPos2 = random.randint(0, len(binDatal) - 1)
    while bitPos == bitPos2:
        bitPos2 = random.randint(0, len(binDatal) - 1)
    if binDatal[bitPos] == '1':
        binDatal[bitPos] = '0'
    else:
        binDatal[bitPos] = '1'
    if binDatal[bitPos2] == '1':
        binDatal[bitPos2] = '0'
    else:
        binDatal[bitPos2] = '1'
    binData = ''.join(binDatal)
    setCmd = "set {char}" + addressF + " = " + hex(int(binData, 2))
    gdb.execute(setCmd)
    return bufLog


def randomBitFlipWordAddress(address, byteSizeof):
    tag = "randomBitFlip"
    bufLog = ""
    bufLog += "Fault Model: Random bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: " + str(address)
    bufLog += "\n"
    bufLog += "address max offset: " + str(byteSizeof)
    bufLog += "\n"
    random.seed()
    addressOffset = 0
    while addressOffset < byteSizeof:
        addressF = hex(int(address, 16) + addressOffset)
        xMem = "x/1tb " + str(addressF)
        binData = gdb.execute(xMem, to_string=True)
        binData = re.sub(".*:|\s", "", binData)
        binDatal = list(binData)
        for i in range(0, len(binDatal)):
            binDatal[i] = str(random.randint(0, 1))
        binData = ''.join(binDatal)
        setCmd = "set {char}" + addressF + " = " + hex(int(binData, 2))
        gdb.execute(setCmd)
        addressOffset += 1
    return bufLog


def zeroBitFlipWordAddress(address, byteSizeof):
    tag = "zeroBitFlip"
    bufLog = ""
    bufLog += "Fault Model: Zero bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: " + str(address)
    bufLog += "\n"
    bufLog += "address max offset: " + str(byteSizeof)
    bufLog += "\n"
    random.seed()
    addressOffset = 0
    while addressOffset < byteSizeof:
        addressF = hex(int(address, 16) + addressOffset)
        xMem = "x/1tb " + str(addressF)
        binData = gdb.execute(xMem, to_string=True)
        binData = re.sub(".*:|\s", "", binData)
        binDatal = list(binData)
        for i in range(0, len(binDatal)):
            binDatal[i] = '0'
        binData = ''.join(binDatal)
        setCmd = "set {char}" + addressF + " = " + hex(int(binData, 2))
        gdb.execute(setCmd)
        addressOffset += 1
    return bufLog


def showMemoryContent(address, byteSizeof):
    xMem = "x/" + str(byteSizeof) + "xb " + address
    hexData = gdb.execute(xMem, to_string=True)
    hexData = re.sub(".*:|\s", "", hexData)
    return hexData
