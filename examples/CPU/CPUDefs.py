from enum import Enum, auto
from math import ceil, log2
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
# ADDRM REG(2bit) | REG ADDRESS(2 bit)
# ADDRD REG(2bit) | IMMEDIATE ADDRESS(16 bit)

INSTRUCTION_LENGTH = 32
INSTRUCTION_OPCODE_LENGTH = 8

class OP(int,Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    REGA    = auto()
    REGB    = auto()
    REGC    = auto()
    REGD    = auto()
    REG2MEM = auto()   # MEMORY AT REGISTER ADDRESS, bits 30 and 31 indicate the register
    IM2MEM  = auto()   # MEMORY AT IMMEDIATE ADDRESS
    IM      = auto()   # operand is a constant immediate value

class OPCODE(int,Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    NOP   = auto() # NOP is 0
    MOV   = auto() 

    COUNT = auto() # This is not an opcode, but the number of opcodes

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