import gdb
import os
import re
import random

validAdress = None
validRegisters = None
validInstruction = None

validThread = None
validBlock = None

# function called when the execution is stopped
def faultInjection(event):
    global validBlock, validThread, validRegisters
    
    threadFocus = gdb.execute("cuda kernel 0 block " + str(validBlock[0]) + "," + str(validBlock[1]) + "," + str(validBlock[2]) +
                " thread "+ str(validThread[0]) + "," + str(validThread[1]) + "," + str(validThread[2]), to_string=True)
    
    randRegister = random.randrange(0, len(validRegisters))
    flipInstruction(validRegisters[randRegister],  "bit_flip")
    
    

def littleProfiler(event):
    global validBlock, validThread 
    global  validRegisters, validInstruction, validAdress
    
    threads = executeToList("info cuda threads")
    validBlock, validThread = getValidThread(threads)
     
    addresses = executeToList("disassemble")
    with open("addresses.txt", "w") as f:
        for i in addresses: f.write(str(i) + "\n")
        
    validRegisters, validInstruction, validAdress, byteLocation = getValidAddress(addresses)

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
    

def executeToList(toExecute):
    ret = gdb.execute(toExecute, to_string=True)
    return ret.splitlines()
    
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


#gdbInitStrings = file /tmp/quicksort/quicksort;set args 5000000 4 /tmp/quicksort/inputsort_134217728 /tmp/quicksort/output_5000000


try:
    gdbInitStrings = "file /home/carol/carol-fi/codes/cuda/matrixMul/matrixMul; set args -wA=512 -hA=512 -hB=512 -wB=512"

    for initStr in gdbInitStrings.split(";"):
        print initStr
        gdb.execute(initStr)

except gdb.error as err:
    print "initializing setup: " + str(err)
    
########################################################################
# Little profiler
    
gdb.events.stop.connect(littleProfiler)
breakpoint = gdb.Breakpoint("matrixMul.cu:51", gdb.BP_BREAKPOINT)
runString = gdb.execute("r", to_string=True)
gdb.events.stop.disconnect(littleProfiler)
breakpoint.delete()


########################################################################
# Fault injection

fiBreakpoint = gdb.Breakpoint("*" + validAdress, gdb.BP_BREAKPOINT)
gdb.events.stop.connect(faultInjection)

gdb.execute("c")
fiBreakpoint.delete()
gdb.events.stop.disconnect(faultInjection)
gdb.execute("c")

########################################################################




