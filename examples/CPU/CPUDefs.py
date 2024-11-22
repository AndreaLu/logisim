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

INSTRUCTION_LENGTH = 32
INSTRUCTION_OPCODE_LENGTH = 8

class OP(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    REGA    = auto()
    REGB    = auto()
    REGC    = auto()
    REGD    = auto()
    REG2MEM = auto()   # MEMORY AT REGISTER ADDRESS, bits 30 and 31 indicate the register
    IM2MEM  = auto()   # MEMORY AT IMMEDIATE ADDRESS
    IM      = auto()   # operand is a constant immediate value

class OPCODE(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    NOP   = auto() # NOP is 0
    MOV   = auto() 

    COUNT = auto() # This is not an opcode, but the number of opcodes

assert log2(OPCODE.COUNT.value) <= 8

class STATE(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    FETCH   = auto()
    EXECUTE = auto()
    SIZE    = auto()
StateSize = ceil(log2(STATE.SIZE.value))

class REGMUXSEL(Enum):
    IMMEDIATE = 0
    REGA      = 1
    REGB      = 2
    REGC      = 3
    REGD      = 4
    MEMORY    = 5

class DMEMADDRMUXSEL(Enum):
    IMMEDIATE = 0
    REGA      = 1
    REGB      = 2
    REGC      = 3
    REGD      = 4