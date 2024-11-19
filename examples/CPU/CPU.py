import sys

# Example of a simple 16 bit harvard CPU

sys.path.append("../../") # let python find logisim
from logisim.seq import WEREG,OSCILLATOR,RAM
from logisim.comb import MUX

from enum import Enum
from math import log2

INSTRUCTION_LENGTH = 32
INSTRUCTION_OPCODE_LENGTH = 8

from enum import Enum, auto

class OPCODE(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    MOVRR = auto()
    MOVRI = auto()
    MOVRD = auto()
    MOVRM = auto()
    MOVMR = auto()
    MOVMI = auto()
    MOVDR = auto()

    COUNT = auto() # This is not an opcode, but the number of opcodes

assert log2(OPCODE.COUNT.value) <= 8


# An instruction is 32 bit long
# In an instruction, only the opcode is fixed size (8 bits)
# The remaining 24 bits depend on the instruction

# In general:
# the suffix D means memory[immediate]
# the suffix M means memory[REG]

# In MOV instructions:
# the syntax is MOV TYPE | DST | SRC
# MOVRR REG(2bit) | REG(2bit)
# MOVRI REG(2bit) | IMMEDIATE(16bit)
# MOVRD REG(2bit) | IMMEDIATE ADDRESS(16 bit)
# MOVRM REG(2bit) | REG ADDRESS(2 bit)
# MOVMR REG ADDRESS(2 bit) | REG(2 bit)
# MOVMI REG ADDRESS(2 BIT) | IMMEDIATE(16 bit)
# MOVDR IMMEDIATE ADDRESS (16 bit) | REG(2 bit)

# in ALU instructions:
# the syntax is ADD DST A B
# ADDRR REG(2bit) | REG(2bit) | REG(2bit)
# ADDRI REG(2bit) | REG(2bit) | Immediate(16 bit)
# ADDRM REG(2bit) | REG ADDRESS(2 bit)
# ADDRD REG(2bit) | IMMEDIATE ADDRESS(16 bit)


sigAQ, sigAWE = Vector(16), Net()
sigBQ, sigBWE = Vector(16), Net()
sigCQ, sigCWE = Vector(16), Net()
sigDQ, sigDWE = Vector(16), Net()
sigRegD = Vector(16)
sigIm = Vector(16)
sigMemDout = Vector(16)
clk = Net()
sigRegDSel = Vector(3)
sigMemAddr = Vector(16)
sigMemAddrSel,sigMemDinSel = vector(3),vector(3)
sigMemRE.sigMemWE = Net(),Net()

OSCILLATOR(100,clk)

# Registers
MUX(Inputs=(sigIm,sigAQ,sigBQ,sigCQ,sigDQ,sigMemDout),Output=SigRegD,Sel=SigRegDSel)
WEREG(D=SigRegD,Q=SigRegAQ,WE=sigAWE,CLK=clk)
WEREG(D=SigRegD,Q=SigRegBQ,WE=sigBWE,CLK=clk)
WEREG(D=SigRegD,Q=SigRegCQ,WE=sigCWE,CLK=clk)
WEREG(D=SigRegD,Q=SigRegDQ,WE=sigDWE,CLK=clk)

# Data Memory
MUX(Inputs=(sigIm,sigAq,sigBq,sigCq,sigDq),Output=sigMemAddr,Sel=sigMemAddrSel)
MUX(Inputs=(sigIm,sigAq,sigBq,sigCq,sigDq),Output=sigMemDin,Sel=sigMemDinSel)
RAM(size=65536,address=sigMemAddr,clock=clk,we=sigMemWE,re=sigMemRE,dataIn=sigMemDin,dataOut=sigMemDout)

