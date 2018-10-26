import gdb
import re
import time
import datetime
import ctypes
import random
import os
import sys

if sys.version_info >= (3,0):
    import configparser # python 3
else:
    import ConfigParser # python 2

### Script version
VERSION = "1.1"

flipConfigFile = "<conf-location>"

gdbTypesDict = {
gdb.TYPE_CODE_PTR:"The type is a pointer.",
gdb.TYPE_CODE_ARRAY:"The type is an array.",
gdb.TYPE_CODE_STRUCT:"The type is a structure.",
gdb.TYPE_CODE_UNION:"The type is a union.",
gdb.TYPE_CODE_ENUM:"The type is an enum.",
gdb.TYPE_CODE_FLAGS:"A bit flags type, used for things such as status registers.",
gdb.TYPE_CODE_FUNC:"The type is a function.",
gdb.TYPE_CODE_INT:"The type is an integer type.",
gdb.TYPE_CODE_FLT:"A floating point type.",
gdb.TYPE_CODE_VOID:"The special type void.",
gdb.TYPE_CODE_SET:"A Pascal set type.",
gdb.TYPE_CODE_RANGE:"A range type, that is, an integer type with bounds.",
gdb.TYPE_CODE_STRING:"A string type. Note that this is only used for certain languages with language-defined string types; C strings are not represented this way.",
gdb.TYPE_CODE_BITSTRING:"A string of bits. It is deprecated.",
gdb.TYPE_CODE_ERROR:"An unknown or erroneous type.",
gdb.TYPE_CODE_METHOD:"A method type, as found in C++ or Java.",
gdb.TYPE_CODE_METHODPTR:"A pointer-to-member-function.",
gdb.TYPE_CODE_MEMBERPTR:"A pointer-to-member.",
gdb.TYPE_CODE_REF:"A reference type.",
gdb.TYPE_CODE_CHAR:"A character type.",
gdb.TYPE_CODE_BOOL:"A boolean type.",
gdb.TYPE_CODE_COMPLEX:"A complex float type.",
gdb.TYPE_CODE_TYPEDEF:"A typedef to some other type.",
gdb.TYPE_CODE_NAMESPACE:"A C++ namespace.",
gdb.TYPE_CODE_DECFLOAT:"A decimal floating point type.",
gdb.TYPE_CODE_INTERNAL_FUNCTION:"A function internal to gdb. This is the type used to represent convenience functions.",}


class logging:
    @staticmethod
    def info(msg):
        fp = open(conf.get("DEFAULT","flipLogFile"), "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[INFO -- "+d+"]\n"+msg+"\n")
        fp.close()

    @staticmethod
    def exception(msg):
        fp = open(conf.get("DEFAULT","flipLogFile"), "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[EXCEPTION -- "+d+"]\n"+msg+"\n")
        fp.close()

    @staticmethod
    def error(msg):
        fp = open(conf.get("DEFAULT","flipLogFile"), "a")
        d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        fp.write("[ERROR -- "+d+"]\n"+msg+"\n")
        fp.close()

    @staticmethod
    def debug(msg):
        if conf.getboolean("DEFAULT","debug"):
            fp = open(conf.get("DEFAULT","flipLogFile"), "a")
            d = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
            fp.write("[DEBUG -- "+d+"]\n"+msg+"\n")
            fp.close()


def exit_handler (event):
    logging.info(str ("event type: exit"))
    try:
        logging.info(str ("exit code: %d" % (event.exit_code)))
    except:
        logging.exception(str("exit code: no exit code available"))
gdb.events.exited.connect(exit_handler)

def abnormal_stop(event):
    logging.debug("Abnormal stop, signal:"+str(event.stop_signal))

faultSuccesuful = False
# function called when the execution is stopped
def fault_injection(event):
    global faultSuccesuful
    r = False

    if not faultSuccesuful:
        logging.debug("Trying Fault Injection")
        r = chooseThreadFlip()
        secs = time.time() - timestampStart
        if r:   
            logging.info("Fault Injection Successful after "+str(secs)+"s")
            faultSuccesuful = True
        else:
            logging.debug("Fault Injection Failed after "+str(secs)+"s")
    else:
        logging.debug("Fault Already Injected")

    gdb.execute("c")

def chooseThreadFlip():
    tag = "chooseThreadFlip"
    bufLog = ""
    try:
        inferior = gdb.selected_inferior()

        for inf in gdb.inferiors():
            logging.debug("Inferior PID: "+str(inf.pid))
            logging.debug("Inferior is valid: "+str(inf.is_valid()))
            logging.debug("Inferior #threads: "+str(len(inf.threads())))
        th = gdb.selected_thread()
        bufLog += str("Backtrace BEGIN:")
        bufLog += "\n"
        bt = gdb.execute("bt", to_string=True)
        sourceLines = gdb.execute("list", to_string=True)
        bufLog += str(bt)
        bufLog += "\n"
        bufLog += str(sourceLines)
        bufLog += "\n"
        bufLog += str("Backtrace END")
        bufLog += "\n"
        threadsSymbols = list()
        for th in inferior.threads():
            try:
                th.switch()
                thSymbols = getAllValidSymbols()
                if len(thSymbols) > 0:
                    threadsSymbols.append([th,thSymbols])
            except:
                continue
        thLen = len(threadsSymbols)
        if thLen <= 0:
            logging.debug(str("No Threads with symbols"))
            return False
        thPos = random.randint(0, thLen-1)
        curThread = threadsSymbols[thPos][0]
        logging.debug("Thread name: "+str(curThread.name))
        logging.debug("Thread num: "+str(curThread.num))
        logging.debug("Thread ptid: "+str(curThread.ptid))
        bufLogFFText = ""
        (r,bufLogFFText) = chooseFrameFlip(threadsSymbols[thPos][1])
        while r is False:
            threadsSymbols.pop(thPos)
            thLen -= 1
            if(thLen <= 0):
                break
            thPos = random.randint(0, thLen-1)
            try:
                (r,bufLogFFText) = chooseFrameFlip(threadsSymbols[thPos][1])
            except:
                r = False
        bufLog += bufLogFFText
        if r or conf.getboolean("DEFAULT","debug"):
            logging.info(bufLog)
        return r 
    except Exception as err:
        logging.exception("pythonException: "+str(err))
        if conf.getboolean("DEFAULT","debug"):
            logging.info(bufLog)
        return False


def chooseFrameFlip(frameSymbols):
    tag = "chooseFrameFlip"
    bufLog = ""
    try:
        framesNum = len(frameSymbols)
        if framesNum <= 0:
            logging.debug(str("No frames to get symbols, returning False"))
            return False
        random.seed()
        framePos = random.randint(0, framesNum-1)
        frame = frameSymbols[framePos][0]
        symbols = frameSymbols[framePos][1]
        symbolsNum = len(symbols)
        while symbolsNum <= 0:
            frameSymbols.pop(framePos)
            framesNum -= 1
            if (framesNum <=0 ):
                logging.debug(str("Could not get symbols to flip values, returning False"))
                return False

            framePos = random.randint(0, framesNum-1)
            frame = frameSymbols[framePos][0]
            symbols = frameSymbols[framePos][1]
            symbolsNum = len(symbols)
    
        symbolPos = random.randint(0, symbolsNum-1)
        symbol = symbols[symbolPos]
        varGDB = symbol.value(frame)
    
        try:
            bufLog += bitFlipValue(varGDB)
            bufLog += "frame name: "+str(frame.name())
            bufLog += "\n"
            bufLog += "symbol name: "+str(symbol.name)
            bufLog += "\n"
            bufLog += "symbol filename: "+str(symbol.symtab.filename)
            bufLog += "\n"
            bufLog += "symbol line: "+str(symbol.line)
            bufLog += "\n"
            bufLog += "value: "+str(varGDB)
            bufLog += "\n"
            bufLog += "value address: "+str(varGDB.address)
            bufLog += "\n"
            bufLog += "Type: "+str(gdbTypesDict[varGDB.type.strip_typedefs().code])
            bufLog += "\n"
            bufLog += "Type sizeof: "+str(varGDB.type.strip_typedefs().sizeof)
            bufLog += "\n"
            if varGDB.type.strip_typedefs().code is gdb.TYPE_CODE_RANGE:
                bufLog += "Type range: "+str(varGDB.type.strip_typedefs().range())
                bufLog += "\n"
            try:
                for field in symbol.type.fields():
                    bufLog += "Field name: "+str(field.name)
                    bufLog += "\n"
                    bufLog += "Field Type: "+str(gdbTypesDict[field.type.strip_typedefs().code])
                    bufLog += "\n"
                    bufLog += "Field Type sizeof: "+str(field.type.strip_typedefs().sizeof)
                    bufLog += "\n"
                    if field.type.strip_typedefs().code is gdb.TYPE_CODE_RANGE:
                        bufLog += "Field Type range: "+str(field.type.strip_typedefs().range())
                        bufLog += "\n"
            except:
                pass
            return (True, bufLog)
        except gdb.error as err:
            logging.exception("gdbException: "+str(err))
        except Exception as err:
            logging.exception("pythonException: "+str(err))
    
        return (False, bufLog)
    except Exception as err:
        logging.exception("pythonException: "+str(err))
        return (False, bufLog)
        
def LSBFlipWordAddress(address, byteSizeof):
    tag = "LSBBitFlip"
    bufLog = ""
    bufLog += "Fault Model: LSB bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: "+str(address)
    bufLog += "\n"
    bufLog += "address max offset: "+str(byteSizeof)
    bufLog += "\n"
    addressOffset=byteSizeof-1 # get the least significant byte only
    addressF = hex(int(address,16)+addressOffset)
    xMem = "x/1tb "+str(addressF)
    binData = gdb.execute(xMem, to_string=True)
    binData = re.sub(".*:|\s","",binData)
    binDatal = list(binData)
    bitPos=random.randint(0, len(binDatal)-1)
    if binDatal[bitPos] == '1':
        binDatal[bitPos] = '0'
    else:
        binDatal[bitPos] = '1'
    binData = ''.join(binDatal)
    setCmd = "set {char}"+addressF+" = "+hex(int(binData, 2))
    gdb.execute(setCmd)
    return bufLog

def singleBitFlipWordAddress(address, byteSizeof):
    tag = "singleBitFlip"
    bufLog = ""
    bufLog += "Fault Model: Single bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: "+str(address)
    bufLog += "\n"
    bufLog += "address max offset: "+str(byteSizeof)
    bufLog += "\n"
    random.seed()
    addressOffset=random.randint(0, byteSizeof-1)
    addressF = hex(int(address,16)+addressOffset)
    xMem = "x/1tb "+str(addressF)
    binData = gdb.execute(xMem, to_string=True)
    binData = re.sub(".*:|\s","",binData)
    binDatal = list(binData)
    bitPos=random.randint(0, len(binDatal)-1)
    if binDatal[bitPos] == '1':
        binDatal[bitPos] = '0'
    else:
        binDatal[bitPos] = '1'
    binData = ''.join(binDatal)
    setCmd = "set {char}"+addressF+" = "+hex(int(binData, 2))
    gdb.execute(setCmd)
    return bufLog

def doubleBitFlipWordAddress(address, byteSizeof):
    tag = "doubleBitFlip"
    bufLog = ""
    bufLog += "Fault Model: Double bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: "+str(address)
    bufLog += "\n"
    bufLog += "address max offset: "+str(byteSizeof)
    bufLog += "\n"
    random.seed()
    addressOffset=random.randint(0, byteSizeof-1)
    addressF = hex(int(address,16)+addressOffset)
    xMem = "x/1tb "+str(addressF)
    binData = gdb.execute(xMem, to_string=True)
    binData = re.sub(".*:|\s","",binData)
    binDatal = list(binData)
    bitPos=random.randint(0, len(binDatal)-1)
    bitPos2=random.randint(0, len(binDatal)-1)
    while bitPos == bitPos2:
        bitPos2=random.randint(0, len(binDatal)-1)
    if binDatal[bitPos] == '1':
        binDatal[bitPos] = '0'
    else:
        binDatal[bitPos] = '1'
    if binDatal[bitPos2] == '1':
        binDatal[bitPos2] = '0'
    else:
        binDatal[bitPos2] = '1'
    binData = ''.join(binDatal)
    setCmd = "set {char}"+addressF+" = "+hex(int(binData, 2))
    gdb.execute(setCmd)
    return bufLog

def randomBitFlipWordAddress(address, byteSizeof):
    tag = "randomBitFlip"
    bufLog = ""
    bufLog += "Fault Model: Random bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: "+str(address)
    bufLog += "\n"
    bufLog += "address max offset: "+str(byteSizeof)
    bufLog += "\n"
    random.seed()
    addressOffset = 0
    while addressOffset < byteSizeof:
        addressF = hex(int(address,16)+addressOffset)
        xMem = "x/1tb "+str(addressF)
        binData = gdb.execute(xMem, to_string=True)
        binData = re.sub(".*:|\s","",binData)
        binDatal = list(binData)
        for i in range(0,len(binDatal)):
            binDatal[i] = str(random.randint(0,1))
        binData = ''.join(binDatal)
        setCmd = "set {char}"+addressF+" = "+hex(int(binData, 2))
        gdb.execute(setCmd)
        addressOffset += 1
    return bufLog

def zeroBitFlipWordAddress(address, byteSizeof):
    tag = "zeroBitFlip"
    bufLog = ""
    bufLog += "Fault Model: Zero bit-flip"
    bufLog += "\n"
    bufLog += "base address to flip value: "+str(address)
    bufLog += "\n"
    bufLog += "address max offset: "+str(byteSizeof)
    bufLog += "\n"
    random.seed()
    addressOffset = 0
    while addressOffset < byteSizeof:
        addressF = hex(int(address,16)+addressOffset)
        xMem = "x/1tb "+str(addressF)
        binData = gdb.execute(xMem, to_string=True)
        binData = re.sub(".*:|\s","",binData)
        binDatal = list(binData)
        for i in range(0,len(binDatal)):
            binDatal[i] = '0'
        binData = ''.join(binDatal)
        setCmd = "set {char}"+addressF+" = "+hex(int(binData, 2))
        gdb.execute(setCmd)
        addressOffset += 1
    return bufLog

def showMemoryContent(address, byteSizeof):
    xMem = "x/"+str(byteSizeof)+"xb "+address
    hexData = gdb.execute(xMem, to_string=True)
    hexData = re.sub(".*:|\s","",hexData)
    return hexData
    
def genericBitFlip(value):
    tag = "genericBitFlip"
    bufLog = ""

    address = re.sub("<.*>|\".*\"","",str(value.address))
    byteSizeof = value.type.strip_typedefs().sizeof
    bufLog += "Memory content before bitflip:"+str(showMemoryContent(address, byteSizeof))
    bufLog += "\n"
    choice = int(faultModel)
    if choice == 0:
        bufLog += singleBitFlipWordAddress(address,byteSizeof)
    elif choice == 1:
        bufLog += doubleBitFlipWordAddress(address,byteSizeof)
    elif choice == 2:
        bufLog += randomBitFlipWordAddress(address,byteSizeof)
    elif choice == 3:
        bufLog += zeroBitFlipWordAddress(address,byteSizeof)
    elif choice == 4:
        bufLog += LSBFlipWordAddress(address,byteSizeof)
    bufLog += "Memory content after  bitflip:"+str(showMemoryContent(address, byteSizeof))
    bufLog += "\n"
    return bufLog

def bitFlipValue(value):
    tag = "bitFlipValue"
    bufLog = ""
    if value.type.strip_typedefs().code is gdb.TYPE_CODE_PTR:
        random.seed()
        pointerFlip=random.randint(0, 1)
        pointedAddress = re.sub("<.*>|\".*\"","",str(value.referenced_value().address))
        if pointerFlip or hex(int(pointedAddress,16)) <= hex(int("0x0",16)):
            bufLog += str("Fliping a bit of the pointer")
            bufLog += "\n"
            bufLog += genericBitFlip(value)
        else:
            bufLog += str("Fliping a bit of the value pointed by a pointer")
            bufLog += "\n"
            bufLog += bitFlipValue(value.referenced_value())
    elif value.type.strip_typedefs().code is gdb.TYPE_CODE_REF:
        random.seed()
        refFlip=random.randint(0, 1)
        pointedAddress = re.sub("<.*>|\".*\"","",str(value.referenced_value().address))
        if refFlip or hex(int(pointedAddress,16)) <= hex(int("0x0",16)):
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
        arrayPos=random.randint(0, rangeMax)
        bufLog += "Fliping array at pos: "+str(arrayPos)
        bufLog += "\n"
        bufLog += bitFlipValue(value[arrayPos])
    elif value.type.strip_typedefs().code is gdb.TYPE_CODE_STRUCT:
        fields = value.type.fields()
        if not fields:
            bufLog += genericBitFlip(value)
        random.seed()
        fieldPos=random.randint(0, len(fields)-1)
        newValue = value[fields[fieldPos]]
        count=0
        newAddress = re.sub("<.*>|\".*\"","",str(newValue.address))
        while newValue.address is None or newValue.is_optimized_out or hex(int(newAddress,16)) <= hex(int("0x0",16)):
            random.seed()
            fieldPos=random.randint(0, len(fields)-1)
            newValue = value[fields[fieldPos]]
            newAddress = re.sub("<.*>|\".*\"","",str(newValue.address))
            count +=1
            if count == 20:
                raise Exception("Unable to exit loop in struct fields; Exiting wihtout making a bit flip")

        bufLog += "Fliping value of field: "+str(fields[fieldPos].name)
        bufLog += "\n"
        bufLog += bitFlipValue(newValue)
    elif value.type.strip_typedefs().code is gdb.TYPE_CODE_UNION:
        fields = value.type.fields()
        random.seed()
        fieldPos=random.randint(0, len(fields)-1)
        newValue = value[fields[fieldPos]]
        count=0
        newAddress = re.sub("<.*>|\".*\"","",str(newValue.address))
        while newValue.address is None or newValue.is_optimized_out or hex(int(newAddress,16)) <= hex(int("0x0",16)):
            random.seed()
            fieldPos=random.randint(0, len(fields)-1)
            newValue = value[fields[fieldPos]]
            count +=1
            if count == 20:
                #logMsg(str("Error: unable to exit loop in union fields; Exiting wihtout making bitflip"))
                #return
                raise Exception("Unable to exit loop in union fields; Exiting wihtout making bitflip")

        bufLog += "Fliping value of field name: "+str(fields[fieldPos].name)
        bufLog += "\n"
        bufLog += bitFlipValue(newValue)
    else: 
        bufLog += genericBitFlip(value)

    return bufLog

# The parameter is a GDB Type object, it prints the Type information
def printGDBType(gdbType):
    logMsg("Type: "+str(gdbTypesDict[gdbType.strip_typedefs().code]))
    logMsg("Type sizeof: "+str(gdbType.strip_typedefs().sizeof))
    if gdbType.strip_typedefs().code is gdb.TYPE_CODE_RANGE:
        logMsg("Type range: "+str(gdbType.strip_typedefs().range()))
    

# Get all the symbols of the stacked frames, returns a list of tuples [frame, symbolsList]
# where frame is a GDB Frame object and symbolsList is a list of all symbols of this frame
def getAllValidSymbols():
    allSymbols=list()
    frame = gdb.selected_frame()
    while frame:
        symbols=getFrameSymbols(frame)
        if symbols is not None:
            allSymbols.append([frame,symbols])
        frame = frame.older()
    return allSymbols

# Returns a list of all symbols of the frame, frame is a GDB Frame object
def getFrameSymbols(frame):
    try:
        symbols = list()
        block = frame.block()
        while block:
            for symbol in block:
                if isBitFlipPossible(symbol,frame):
                    symbols.append(symbol)
            block = block.superblock
        return symbols
    except:
        return None

# Returns True if we can bitflip some bit of this symbol, i.e. if this is a variable or 
# constant and not functions and another symbols
def isBitFlipPossible(symbol,frame):
    if symbol.is_variable or symbol.is_constant or symbol.is_argument:
        varGDB = symbol.value(frame)
        address = re.sub("<.*>|\".*\"","",str(varGDB.address))
        if varGDB.address is not None and not varGDB.is_optimized_out and hex(int(address,16)) > hex(int("0x0",16)):
            return True
    return False




############################ Main execution start ############################

# Read configuration file
if sys.version_info >= (3,0):
    conf = configparser.ConfigParser()
else:
    conf = ConfigParser.ConfigParser()
conf.read(flipConfigFile)


logging.info("Starting flip_value script\nversion: "+str(VERSION))

timestampStart = 0

# Initialize GDB to run the app
gdb.execute("set confirm off")
gdb.execute("set pagination off")
logging.info("Initialization strings:")
try:
    count=0
    gdbInitStrings = conf.get("DEFAULT","gdbInitStrings")
    for initStr in gdbInitStrings.split(";"):
        gdb.execute(initStr)
        count += 1
        logging.info("("+str(count)+") "+initStr)
except gdb.error as err:
    logging.error("initializing setup: "+str(err))

init = conf.get("DEFAULT","initSignal")
end = conf.get("DEFAULT","endSignal")
faultModel = conf.get("DEFAULT","faultModel")
logging.info("initSignal:"+str(init))
logging.info("endSignal:"+str(end))
logging.info("faultModel:"+str(faultModel))
# Define which function to call when the execution stops, e.g. when a breakpoint is hit 
# or a interruption signal is received
gdb.events.stop.connect(fault_injection)

timestampStart = int(time.time())

# Start app execution
gdb.execute("r")

