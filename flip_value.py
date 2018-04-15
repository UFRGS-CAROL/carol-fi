import random

import gdb
import re
import os
import common_functions as cf  # All common functions will be at common_functions module
import common_parameters


"""

"""


def chooseFrameFlip(frameSymbols):
    tag = "chooseFrameFlip"
    bufLog = ""
    try:
        framesNum = len(frameSymbols)
        if framesNum <= 0:
            # logging.debug(str("No frames to get symbols, returning False"))
            return False
        random.seed()
        framePos = random.randint(0, framesNum - 1)
        frame = frameSymbols[framePos][0]
        symbols = frameSymbols[framePos][1]
        symbolsNum = len(symbols)
        while symbolsNum <= 0:
            frameSymbols.pop(framePos)
            framesNum -= 1
            if (framesNum <= 0):
                # logging.debug(str("Could not get symbols to flip values, returning False"))
                return False

            framePos = random.randint(0, framesNum - 1)
            frame = frameSymbols[framePos][0]
            symbols = frameSymbols[framePos][1]
            symbolsNum = len(symbols)

        symbolPos = random.randint(0, symbolsNum - 1)
        symbol = symbols[symbolPos]
        varGDB = symbol.value(frame)
        for t in frameSymbols:
            for symbol_i in t[1]:
                print(symbol_i.type, symbol_i.name, symbol_i.line,
                      symbol_i.print_name, symbol_i.is_variable, symbol_i.value)

        try:
            # bufLog += bitFlipValue(varGDB)
            # bufLog += "frame name: " + str(frame.name())
            # bufLog += "\n"
            # bufLog += "symbol name: " + str(symbol.name)
            # bufLog += "\n"
            # bufLog += "symbol filename: " + str(symbol.symtab.filename)
            # bufLog += "\n"
            # bufLog += "symbol line: " + str(symbol.line)
            # bufLog += "\n"
            # bufLog += "value: " + str(varGDB)
            # bufLog += "\n"
            # bufLog += "value address: " + str(varGDB.address)
            # bufLog += "\n"
            # bufLog += "Type: " + str(gdbTypesDict[varGDB.type.strip_typedefs().code])
            # bufLog += "\n"
            # bufLog += "Type sizeof: " + str(varGDB.type.strip_typedefs().sizeof)
            # bufLog += "\n"
            if varGDB.type.strip_typedefs().code is gdb.TYPE_CODE_RANGE:
                bufLog += "Type range: " + str(varGDB.type.strip_typedefs().range())
                bufLog += "\n"
            # try:
            #     for field in symbol.type.fields():
            #         bufLog += "Field name: " + str(field.name)
            #         bufLog += "\n"
            #         bufLog += "Field Type: " + str(gdbTypesDict[field.type.strip_typedefs().code])
            #         bufLog += "\n"
            #         bufLog += "Field Type sizeof: " + str(field.type.strip_typedefs().sizeof)
            #         bufLog += "\n"
            #         if field.type.strip_typedefs().code is gdb.TYPE_CODE_RANGE:
            #             bufLog += "Field Type range: " + str(field.type.strip_typedefs().range())
            #             bufLog += "\n"
            # except:
            #     pass
            return (True, bufLog)
        except gdb.error as err:
            raise
            # logging.exception("gdbException: " + str(err))
        except Exception as err:
            # logging.exception("pythonException: " + str(err))
            raise
        # return (False, bufLog)
    except Exception as err:
        # logging.exception("pythonException: " + str(err))
        raise

    # return (False, bufLog)

class Breakpoint(gdb.Breakpoint):
    # def __init__(self):
    #     super(Breakpoint, self).__init__()
    #     global global_valid_block, global_valid_thread, global_valid_register
    #     global global_bits_to_flip, global_fault_model, global_logging
    #     global ready_to_inject

        # if not ready_to_inject:
        #     return

    def stop(self):
        # This if avoid the creation of another event connection
        # for some reason gdb cannot breakpoint addresses before
        # a normal breakpoint is hit
        global_logging.debug("Trying Fault Injection")
        inferior = gdb.selected_inferior()

        # threadsSymbols = []
        #
        # for th in inferior.threads():
        #     print(dir(th))
        #     try:
        #         th.switch()
        #         thSymbols = getAllValidSymbols()
        #         if len(thSymbols) > 0:
        #             threadsSymbols.append([th, thSymbols])
        #     except:
        #         continue
        chooseFrameFlip(getAllValidSymbols())
        return True


"""
function called when the execution is stopped by a signal
"""


def fault_injector_signal(event):
    pass


def getAllValidSymbols():
    allSymbols = list()
    frame = gdb.selected_frame()
    while frame:
        symbols = getFrameSymbols(frame)
        print(frame)
        if symbols is not None:
            allSymbols.append([frame, symbols])
        frame = frame.older()
    return allSymbols


# Returns a list of all symbols of the frame, frame is a GDB Frame object
def getFrameSymbols(frame):
    try:
        symbols = list()
        block = frame.block()
        while block:
            print(block)
            for symbol in block:
                if isBitFlipPossible(symbol, frame):
                    symbols.append(symbol)
            block = block.superblock
        return symbols
    except:
        return None


# Returns True if we can bitflip some bit of this symbol, i.e. if this is a variable or
# constant and not functions and another symbols
def isBitFlipPossible(symbol, frame):
    if symbol.is_variable or symbol.is_constant or symbol.is_argument:
        varGDB = symbol.value(frame)
        address = re.sub("<.*>|\".*\"", "", str(varGDB.address))
        if varGDB.address is not None and not varGDB.is_optimized_out and hex(int(address, 16)) > hex(int("0x0", 16)):
            return True
    return False


"""
function called when the execution is stopped by a breakpoint
"""


def fault_injection_breakpoint(event):
    global global_valid_block, global_valid_thread, global_valid_register
    global global_bits_to_flip, global_fault_model, global_logging
    global ready_to_inject

    # if not ready_to_inject:
    #     return

    # This if avoid the creation of another event connection
    # for some reason gdb cannot breakpoint addresses before
    # a normal breakpoint is hit
    global_logging.debug("Trying Fault Injection")
    inferior = gdb.selected_inferior()

    threadsSymbols = []

    for th in inferior.threads():
        print(dir(th))
        try:
            th.switch()
            thSymbols = getAllValidSymbols()
            if len(thSymbols) > 0:
                threadsSymbols.append([th, thSymbols])
        except:
            continue


            # try:
            #     change_focus_cmd = "cuda kernel 0 block {0},{1},{2} thread {3},{4},{5}".format(str(global_valid_block[0]),
            #                                                                                    str(global_valid_block[1]),
            #                                                                                    str(global_valid_block[2]),
            #                                                                                    str(global_valid_thread[0]),
            #                                                                                    str(global_valid_thread[1]),
            #                                                                                    str(global_valid_thread[2]))
            #     thread_focus = gdb.execute(change_focus_cmd, to_string=True)
            #
            # except Exception as err:
            #     global_logging.exception("CUDA_FOCUS_exception: " + str(err))
            #     global_logging.exception("Fault Injection Went Wrong")
            #     return
            #
            # try:
            #     # Thread focus return information
            #     global_logging.info(str(thread_focus).replace("[", "").replace("]", "").strip())
            #
            #     # Do the fault injection magic
            #     generic_injector(global_valid_register, global_bits_to_flip, global_fault_model)
            #
            #     global_logging.info("Fault Injection Successful")
            # except Exception as err:
            #     global_logging.exception("fault_injection_python_exception: " + str(err))
            #     global_logging.exception("Fault Injection Went Wrong")


"""
Flip only a bit in a register content
"""


def flip_a_bit(bit_to_flip, reg_content):
    new_bit = '0' if reg_content[bit_to_flip] == '1' else '1'
    reg_content = reg_content[:bit_to_flip] + new_bit + reg_content[bit_to_flip + 1:]
    return reg_content


"""
Flip a bit or multiple bits based on a fault model
"""


def generic_injector(valid_register, bits_to_flip, fault_model):
    # get register content
    # print("STEP PASSOU")
    # print(cf.execute_command(gdb, "info frame"))
    reg_cmd = cf.execute_command(gdb, "p/t $" + str(valid_register))
    # print("REG BEFORE", reg_cmd)

    m = re.match('\$(\d+)[ ]*=[ ]*(\S+).*', reg_cmd[0])

    if m:
        reg_content = str(m.group(2))
        # Make sure that binary value will have max size register
        reg_content_old = str('0' * (common_parameters.MAX_SIZE_REGISTER - len(reg_content))) + reg_content
        # Logging info result extracted from register
        global_logging.info("reg_old_value: " + reg_content_old)
        reg_content_new = ''

        # Single bit flip
        if fault_model == 0:
            # single bit flip
            reg_content_new = flip_a_bit(bits_to_flip[0], reg_content_old)

        # Double bit flip
        elif fault_model == 1:
            # multiple bit flip
            for bit_to_flip in bits_to_flip:
                reg_content_new = flip_a_bit(bit_to_flip, reg_content_old)

        # Random value
        elif fault_model == 2:
            # random value is stored at bits_to_flip[0]
            reg_content_new = str(bits_to_flip[0])

        # Zero values
        elif fault_model == 3:
            reg_content_new = '0'

        # Least significant bits, not implemented
        elif fault_model == 4:
            raise NotImplementedError

        reg_content_fliped = str(int(reg_content_new, 2))
        # send the new value to gdb
        reg_cmd_flipped = cf.execute_command(gdb, "set $" + str(valid_register) + " = " + reg_content_fliped)

        global_logging.info("reg_new_value: " + str(reg_content_new))

        # Log command return only something was printed
        if len(reg_cmd_flipped) > 0:
            global_logging.info("flip command return: " + str(reg_cmd_flipped))

        # print("REG MODIFIED ", cf.execute_command(gdb, "p/t $" + str(valid_register)))

        # Return the fault confirmation
        return reg_content_old != reg_content_new
    else:
        raise NotImplementedError


"""
Handler attached to exit event
"""


def exit_handler(event):
    global_logging.info(str("event type: exit"))
    try:
        global_logging.info(str("exit code: %d" % event.exit_code))
    except:
        global_logging.exception(str("exit code: no exit code available"))


"""
Handler attached to crash event
"""


def abnormal_stop(event):
    global_logging.debug("Abnormal stop, signal:" + str(event.stop_signal))


"""
Main function
"""


def main():
    # Global vars that will be used by the FI events
    global global_valid_block, global_valid_thread, global_bits_to_flip
    global global_fault_model, global_valid_register, global_logging

    # This var will control if fault can be injected
    global ready_to_inject
    ready_to_inject = False

    # Initialize GDB to run the app
    gdb.execute("set confirm off")

    # Connecting to a exit handler event
    gdb.events.exited.connect(exit_handler)

    # Get variables values from environment
    # First parse line
    # CAROL_FI_INFO = blockX,blockY,blockZ;threadX,threadY,threadZ;validRegister;bits_0,bits_1;fault_model;
    # injection_site;breakpoint;flip_log_file;debug;gdb_init_strings
    # [valid_block, valid_thread, global_valid_register, bits_to_flip, fault_model, injection_site, breakpoint_location,
    #  flip_log_file, debug, gdb_init_strings, inj_type] = str(os.environ['CAROL_FI_INFO']).split('|')

    # Set global vars to be used
    # global_valid_block = valid_block.split(",")
    # global_valid_thread = valid_thread.split(",")
    # global_bits_to_flip = [int(i) for i in bits_to_flip.split(",")]
    # global_fault_model = int(fault_model)
    # debug = bool(debug)

    flip_log_file = "/tmp/flip_log_test.log"
    debug = True
    gdb_init_strings = "file /home/carol/carol-fi/codes/matrixMul/matrixMul;"
    breakpoint_location = "matrixMul.cu:100"

    # Logging
    global_logging = cf.Logging(log_file=flip_log_file, debug=debug)
    global_logging.info("Starting flip_value script")
    try:
        for init_str in gdb_init_strings.split(";"):
            gdb.execute(init_str)
            global_logging.info("initializing setup: " + str(init_str))

    except gdb.error as err:
        print("initializing setup: " + str(err))

    # Will only if breakpoint mode is activated
    # breakpoint_kernel_line = None
    # if inj_type == 'break':

    # Place the first breakpoint, it is only to avoid
    # address memory error
    # breakpoint_kernel_line = gdb.Breakpoint(spec=breakpoint_location, type=gdb.BP_BREAKPOINT)
    breakpoint_kernel_line = Breakpoint(spec=breakpoint_location, type=gdb.BP_BREAKPOINT, temporary=True)
    # Define which function to call when the execution stops, e.g. when a breakpoint is hit
    # or a interruption signal is received
    # gdb.events.stop.connect(fault_injection_breakpoint)
    # elif inj_type == 'signal':
    #     # Connect to signal handler event
    #     gdb.events.stop.connect(fault_injector_signal)

    # Start app execution
    gdb.execute("r")

    # Put breakpoint only it is breakpoint mode
    # if inj_type == 'break':
    # breakpoint_kernel_line.delete()
    # del breakpoint_kernel_line
    ready_to_inject = True
    # breakpoint_kernel_address = gdb.Breakpoint(spec="*" + injection_site, type=gdb.BP_BREAKPOINT)

    # Continue execution until the next breakpoint
    gdb.execute("c")
    del breakpoint_kernel_line
    # breakpoint_kernel_address.delete()
    # breakpoint_kernel_line.delete()
    # gdb.execute("c")

    # del breakpoint_kernel_address
    # del breakpoint_kernel_line


global_valid_block, global_valid_thread, global_bits_to_flip = [None] * 3
global_fault_model, global_valid_register, global_logging = [None] * 3
ready_to_inject = False

# Call main execution
main()
