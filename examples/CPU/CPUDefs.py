import sys

sys.path.append("../../") # let python find logisim

from enum import Enum, auto
from math import ceil, log2
from dataclasses import dataclass
from logisim import Net,Vector,Cell

# An instruction is 32 bit long
# In an instruction, only the opcode is fixed size (8 bits)
# and it is always located at the lowest significant bits.
# Also, when an instruction uses a register immediate word, it
# is always at [14:29] in the instruction.
# The remaining bits depend on the instruction.
# It follows the instruction set architecture.


#     NOP  | 
#    [0:7] | [8:31]
#   -------|---------
#    0x00  | 0x000000
#
# No operation

#     MOV  |   DST    |   SRC    |   IM    | REGDST
#    [0:7] |  [8:10]  | [11:13]  | [14:29] | [30:31]
#   -------|----------|----------|---------|---------
#    0x01  | A  = 000 | A  = 000 |         | A = 00
#          | B  = 001 | B  = 001 |         | B = 01
#          | C  = 010 | C  = 010 |         | C = 10
#          | D  = 011 | D  = 011 |         | D = 11
#          | pR = 100 | pR = 100 |         |
#          | pI = 101 | pI = 101 |         |
#          |          | IM = 110 |         |
#
# Moves a word from SRC to DST.
# pR means an access to memory at the location specified by
# REGDST. pI means an access to memory at the location specified by
# the 16 bit Immediate in the instruction.
# An instruction cannot access to memory both for SRC and DST.

#     ADD  |    A     |    B    |   IM    | REGDST
#    [0:7] | [8:10]   | [11:13] | [14:29] | [30:31]
#   -------|----------|---------|---------|---------
#    0x02  | A  = 000 | A = 000 |         | A = 00
#          | B  = 001 | B = 001 |         | B = 01
#          | C  = 010 | C = 010 |         | C = 10
#          | D  = 011 | D = 011 |         | D = 11
#          | IM = 100 |         |         |
#  
# Adds two words and store the result to a register.
# operaend A can be a register or the instruction immediate.
# operand B must be a register.

#     JMP  |   CND     |  OP      |   IM    |
#    [0:7] |  [8:10]   | [11:13]  | [14:29] | [30:31]
#   -------|-----------|----------|---------|---------
#    0x03  | UNC = 000 | A  = 000 |         | 0b00
#          | EQ  = 001 | B  = 001 |         |
#          | NEQ = 010 | C  = 010 |         |
#          | GRE = 011 | D  = 011 |         |
#          | LOW = 100 | IM = 100 |         |
#          
# Branches to a new instruction memory address; a condition can be applied
# by using the CND field. Conditions are referred to the status registers
# that is updated after mathemeatical operations (ADD,SUB,CMP).
# UNC - unconditional jump
# EQ  - jump if equal
# NEQ - jump if not equal
# GRE - jump if greater
# LOW - jump if lower

INSTRUCTION_LENGTH = 32
INSTRUCTION_OPCODE_LENGTH = 8

class AutoEnum(int,Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count

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

class JMPCND(AutoEnum):
    UNC = auto() # Unconditionate jump
    EQ  = auto() # Jump if equal
    NEQ = auto() # Jump if not equal
    GRE = auto() # Jump if greater
    LOW = auto() # Jump if lower



class OPCODE(int,Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    NOP   = auto() # NOP  - do nothing
    MOV   = auto() # MOV  - move a word from/to registers,immediate and memory
    ADD   = auto() # ADD  - sum two words
    JMP   = auto() # JMP  - Jump to another location
    SUB   = auto() # SUB  - subtract two words
    SFL   = auto() # SFL  - Shift left (arithmetic or logic) a register
    SFR   = auto() # SFR  - Shift right (arithmetic or logic) a register
    ROTL  = auto() # ROTL - Rotate lef a register
    ROTR  = auto() # ROTR - Rotate right a register
    CMP   = auto() # CMP  - Compare (performs a sub without a destination)
    


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
    ALU       = 6

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
