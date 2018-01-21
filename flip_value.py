import gdb
import os
import re
import random

import sys
sys.path.append("/home/carol/carol-fi") # I have to fix it
import common_functions as cf # All common functions will be at common_functions module


# function called when the execution is stopped
def faultInjection(event):
    global validBlock, validThread, validRegisters
    
    threadFocus = gdb.execute("cuda kernel 0 block " + str(validBlock[0]) + "," + str(validBlock[1]) + "," + str(validBlock[2]) +
                " thread "+ str(validThread[0]) + "," + str(validThread[1]) + "," + str(validThread[2]), to_string=True)
    
    randRegister = random.randrange(0, len(validRegisters))
    flipInstruction(validRegisters[randRegister],  "bit_flip")
    
    


def getValidAddress(addresses):
    m = None
    registers = []
    instruction = ''
    address = ''
    byteLocation = ''

    # search for a valid instruction 
    while not m:
        element = random.randrange((len(addresses) - 1)/2, len(addresses) - 1)
        instructionLine = addresses[element]
        
        expression = ".*([0-9a-fA-F][xX][0-9a-fA-F]+) (\S+):[ \t\n\r\f\v]*(\S+)[ ]*(\S+)"
        
        for i in [1, 3, 4, 5]:
            # INSTRUCTION R1, R2...
            # 0x0000000000b418e8 <+40>: MOV R4, R2...
            expression += ",[ ]*(\S+)"
            m = re.match(expression + ".*", instructionLine)
            
            if m:
                address = m.group(1)
                byteLocation = m.group(2)
                instruction = m.group(3)
                registers.extend([m.group(3 + t) for t in xrange(0, i)])
                break
    
        if not m:
            print "it is stoped here:", instructionLine
        else:
            print "it choose something:", instructionLine

    return registers, instruction, address, byteLocation


def flipInstruction(register, faultModel):
    if faultModel == "bit_flip":
        pass
    elif faultModel == "multiple_bitflip":
        pass
    elif faultModel == "random_value":
        pass
    elif faultModel == "zero_value":
        pass
    


def getValidThread(threads):
    element = random.randrange(0, len(threads) - 4)
    #  (15,2,0) (31,12,0)    (15,2,0) (31,31,0)    20 0x0000000000b41a28 matrixMul.cu    47
    splited = threads[element].replace("\n", "").split()

    # randomly chosen first block and thread
    block = re.match(".*\((\d+),(\d+),(\d+)\).*", splited[0])
    threa = re.match(".*\((\d+),(\d+),(\d+)\).*", splited[1])
    
    blockX = blockY = blockZ = 0
    threadX = threadY = threadZ = 0
    try:
        blockX = block.group(1)
        blockY = block.group(2)
        blockZ = block.group(3)
    
        threadX = threa.group(1)
        threadY = threa.group(2)
        threadZ = threa.group(3) 
    except:
        raise ValueError
    
    
    return [blockX, blockY, blockZ], [threadX, threadY, threadZ] 


########################################################################
# Initialize GDB to run the app
gdb.execute("set confirm off")
gdb.execute("set pagination off")



conf = cf.load_config_file()

try:
    gdbInitStrings = conf.get("DEFAULT", "gdbInitStrings")

    for initStr in gdbInitStrings.split(";"):
        print initStr
        gdb.execute(initStr)

except gdb.error as err:
    print "initializing setup: " + str(err)





