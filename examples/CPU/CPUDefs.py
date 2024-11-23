import sys

sys.path.append("../../") # let python find logisim

from enum import Enum, auto
from math import ceil, log2
from dataclasses import dataclass
from logisim import Net,Vector,Cell

# An instruction is 32 bit long
# In an instruction, only the opcode is fixed size (8 bits)
# The remaining 24 bits depend on the instruction

# In general:
# the suffix D means memory[immediate]
# the suffix M means memory[REG]

# In MOV instructions:
# the syntax is MOV TYPE | DST | SRC
# MOVRR REG(2bit) | REG(2bit)                   OK
# MOVRI REG(2bit) | IMMEDIATE(16bit)            OK
# MOVRD REG(2bit) | IMMEDIATE ADDRESS(16 bit)   OK
# MOVRM REG(2bit) | REG ADDRESS(2 bit)          OK
# MOVMR REG ADDRESS(2 bit) | REG(2 bit)         TEST
# MOVMI REG ADDRESS(2 BIT) | IMMEDIATE(16 bit)  TEST
# MOVDR IMMEDIATE ADDRESS (16 bit) | REG(2 bit) TEST

# in ALU instructions:
# the syntax is ADD DST A B
# ADDRR REG(2bit) | REG(2bit) | REG(2bit)
# ADDRI REG(2bit) | REG(2bit) | Immediate(16 bit)


INSTRUCTION_LENGTH = 32
INSTRUCTION_OPCODE_LENGTH = 8

class MOVOP(int,Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    A       = auto()
    B       = auto()
    C       = auto()
    D       = auto()
    REG2MEM = auto()   # MEMORY AT REGISTER ADDRESS, bits 30 and 31 indicate the register
    IM2MEM  = auto()   # MEMORY AT IMMEDIATE ADDRESS
    IM      = auto()   # operand is a constant immediate value

class ADDOP(int,Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    A = auto()
    B = auto()
    C = auto()
    D = auto()
    IMMEDIATE = auto()

class OPCODE(int,Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    NOP   = auto() # NOP - do nothing
    MOV   = auto() # MOV - move a word from/to registers,immediate and memory
    ADD   = auto() # ADD - sum two words
    SUB   = auto() # SUB - subtract two words
    SFL   = auto() # SFL - Shift left (arithmetic or logic) a register
    SFR   = auto() # SFR - Shift right (arithmetic or logic) a register
    ROTL  = auto() # ROTL - Rotate lef a register
    ROTR  = auto() # ROTR - Rotate right a register

    COUNT = auto() # Number of defined opcodes

assert log2(OPCODE.COUNT) <= 8

class STATE(int,Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    FETCH   = auto()
    EXECUTE = auto()
    SIZE    = auto()
StateSize = ceil(log2(STATE.SIZE))

class REGMUXSEL(int,Enum):
    IMMEDIATE = 0
    REGA      = 1
    REGB      = 2
    REGC      = 3
    REGD      = 4
    MEMORY    = 5

class DMEMADDRMUXSEL(int,Enum):
    IMMEDIATE = 0
    REGA      = 1
    REGB      = 2
    REGC      = 3
    REGD      = 4

class DMEMDINMUXSEL(int,Enum):
    IMMEDIATE = 0
    REGA      = 1
    REGB      = 2
    REGC      = 3
    REGD      = 4

# ALU
class ALUOpType(int,Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    ADD = auto()
    SUB = auto()
    ROTR = auto()
    ROTL = auto()
    SHIFTR = auto()
    SHIFTL = auto()
    MAX = auto()


class ALUControl(Cell):
    opType : Vector
    def __init__(self):
        self.opType =  Vector(ceil(log2(ALUOpType.MAX-1)))
