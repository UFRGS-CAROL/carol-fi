import random
import gdb
import re
import os
import common_functions as cf  # All common functions will be at common_functions module

gdbTypesDict = {
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
    gdb.TYPE_CODE_STRING: "A string type. Note that this is only used for certain languages with language-defined string types; C strings are not represented this way.",
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
    gdb.TYPE_CODE_INTERNAL_FUNCTION: "A function internal to gdb. This is the type used to represent convenience functions.", }


def choose_frame_flip(frame_symbols):
    tag = "choose_frame_flip"
    buf_log = ""
    try:
        frames_num = len(frame_symbols)
        if frames_num <= 0:
            # logging.debug(str("No frames to get symbols, returning False"))
            return False
        random.seed()
        frame_pos = random.randint(0, frames_num - 1)
        frame = frame_symbols[frame_pos][0]
        symbols = frame_symbols[frame_pos][1]
        print("\n\n", symbols, "\n\n")
        symbols_num = len(symbols)
        while symbols_num <= 0:
            frame_symbols.pop(frame_pos)
            frames_num -= 1
            if frames_num <= 0:
                # logging.debug(str("Could not get symbols to flip values, returning False"))
                return False

            frame_pos = random.randint(0, frames_num - 1)
            frame = frame_symbols[frame_pos][0]
            symbols = frame_symbols[frame_pos][1]
            symbols_num = len(symbols)

        symbol_pos = random.randint(0, symbols_num - 1)
        symbol = symbols[symbol_pos]
        varGDB = symbol.value(frame)

        return False, buf_log
    except Exception as err:
        # logging.exception("pythonException: " + str(err))
        return False, buf_log


"""
Get all the symbols of the stacked frames, returns a list of tuples [frame, symbolsList]
where frame is a GDB Frame object and symbolsList is a list of all symbols of this frame
"""


def get_all_valid_symbols():
    all_symbols = list()
    frame = gdb.selected_frame()
    while frame:
        symbols = get_frame_symbols(frame)
        if symbols is not None:
            all_symbols.append([frame, symbols])
        frame = frame.older()
    return all_symbols


"""
Returns a list of all symbols of the frame, frame is a GDB Frame object
"""


def get_frame_symbols(frame):
    try:
        symbols = list()
        block = frame.block()
        while block:
            for symbol in block:
                if is_bit_flip_possible(symbol, frame):
                    symbols.append(symbol)
            block = block.superblock
        return symbols
    except:
        return None

"""
Returns True if we can bitflip some bit of this symbol, i.e. if this is a variable or
constant and not functions and another symbols
"""


def is_bit_flip_possible(symbol, frame):
    if symbol.is_variable or symbol.is_constant or symbol.is_argument:
        varGDB = symbol.value(frame)
        address = re.sub("<.*>|\".*\"", "", str(varGDB.address))
        if varGDB.address is not None and not varGDB.is_optimized_out and hex(int(address, 16)) > hex(int("0x0", 16)):
            return True
    return False


########################################################################################################################

"""
Getting information
"""


def getting_frame_information():
    all_frames = get_all_valid_symbols()
    choose_frame_flip(all_frames)


"""
function called when the execution is stopped by a signal
"""


def fault_injector_signal(event):
    getting_frame_information()


"""
function called when the execution is stopped by a breakpoint
"""


def fault_injection_breakpoint(event):
    global global_valid_block, global_valid_thread, global_valid_register
    global global_bits_to_flip, global_fault_model, global_logging

    # This if avoid the creation of another event connection
    # for some reason gdb cannot breakpoint addresses before
    # a normal breakpoint is hit
    global_logging.debug("Trying Fault Injection")

    try:
        change_focus_cmd = "cuda kernel 0 block {0},{1},{2} thread {3},{4},{5}".format(str(global_valid_block[0]),
                                                                                       str(global_valid_block[1]),
                                                                                       str(global_valid_block[2]),
                                                                                       str(global_valid_thread[0]),
                                                                                       str(global_valid_thread[1]),
                                                                                       str(global_valid_thread[2]))
        thread_focus = gdb.execute(change_focus_cmd, to_string=True)

        # Thread focus return information
        global_logging.info(str(thread_focus).replace("[", "").replace("]", "").strip())

        # Do the fault injection magic
        generic_injector(global_valid_register, global_bits_to_flip, global_fault_model)
        global_logging.exception("Fault Injection Successful")

    except Exception as err:
        global_logging.exception("fault_injection_python_exception: " + str(err))
        global_logging.exception("Fault Injection Went Wrong")


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
    reg_cmd = cf.execute_command(gdb, "p/t $" + str(valid_register))

    m = re.match('\$(\d+)[ ]*=[ ]*(\S+).*', reg_cmd[0])

    if m:
        reg_content = str(m.group(2))
        # Make sure that binary value will have max size register
        reg_content_old = str('0' * (cf.MAX_SIZE_REGISTER - len(reg_content))) + reg_content
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

    # Initialize GDB to run the app
    gdb.execute("set confirm off")
    gdb.execute("set pagination off")

    # Connecting to a exit handler event
    gdb.events.exited.connect(exit_handler)

    # Get variables values from environment
    # First parse line
    # CAROL_FI_INFO = blockX,blockY,blockZ;threadX,threadY,threadZ;validRegister;bits_0,bits_1;fault_model;
    # injection_site;breakpoint;flip_log_file;debug;gdb_init_strings

    [valid_block, valid_thread, global_valid_register, bits_to_flip, fault_model, injection_site, breakpoint_location,
     flip_log_file, debug, gdb_init_strings, inj_type] = str(os.environ['CAROL_FI_INFO']).split('|')

    # Set global vars to be used
    global_valid_block = valid_block.split(",")
    global_valid_thread = valid_thread.split(",")
    global_bits_to_flip = [int(i) for i in bits_to_flip.split(",")]
    global_fault_model = int(fault_model)
    debug = bool(debug)

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
    breakpoint_kernel_line = None
    if inj_type == 'break':
        # Place the first breakpoint, it is only to avoid
        # address memory error
        breakpoint_kernel_line = gdb.Breakpoint(spec=breakpoint_location, type=gdb.BP_BREAKPOINT)

        # Define which function to call when the execution stops, e.g. when a breakpoint is hit
        # or a interruption signal is received
        gdb.events.stop.connect(fault_injection_breakpoint)
    elif inj_type == 'signal':
        # Connect to signal handler event
        gdb.events.stop.connect(fault_injector_signal)

    print(valid_block, valid_thread, global_valid_register, bits_to_flip, fault_model, injection_site, breakpoint_location,
     flip_log_file, debug, gdb_init_strings, inj_type)
    # Start app execution
    gdb.execute("r")

    # Put breakpoint only it is breakpoint mode
    if inj_type == 'break':
        breakpoint_kernel_line.delete()
        breakpoint_kernel_address = gdb.Breakpoint(spec="*" + injection_site, type=gdb.BP_BREAKPOINT)

        # Continue execution until the next breakpoint
        gdb.execute("c")
        breakpoint_kernel_address.delete()


global_valid_block, global_valid_thread, global_bits_to_flip = [None] * 3
global_fault_model, global_valid_register, global_logging = [None] * 3

# Call main execution
main()
