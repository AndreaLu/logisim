# Example of a simple 16 bit harvard CPU

import sys


sys.path.append("../../") # let python find logisim
from logisim.seq import WEREG,OSCILLATOR,RAM
from logisim.comb import MUX
from logisim import Net,Vector,GND,VDD,gates
from logisim import simulateTimeUnit,writeVCD

from CPUDefs import *
from CU import ControlUnit
from ALU import ALU





sigAQ, sigAWE = Vector(16), Net()
sigBQ, sigBWE = Vector(16), Net()
sigCQ, sigCWE = Vector(16), Net()
sigDQ, sigDWE = Vector(16), Net()
sigALU,sigALUA,sigALUB = Vector(16),Vector(16),Vector(16)
sigRegD = Vector(16)
sigIm = Vector(16)
sigMemDout = Vector(16)
clk = Net()
sigRegDSel = Vector(3)
sigMemAddr = Vector(16)
sigMemAddrSel,sigMemDinSel = Vector(3),Vector(3)
sigMemRE,sigMemWE = Net(),Net()
sigMemDin = Vector(16)
(cZero32 := Vector(32)).set(0)

sigIMemAddr = Vector(16)
sigIMemRE = Net()


OSCILLATOR(100,clk)

# Registers
MUX(Inputs=(sigIm,sigAQ,sigBQ,sigCQ,sigDQ,sigMemDout,sigALU),Output=sigRegD,Sel=sigRegDSel)
WEREG(D=sigRegD,Q=sigAQ,WE=sigAWE,CLK=clk)
WEREG(D=sigRegD,Q=sigBQ,WE=sigBWE,CLK=clk)
WEREG(D=sigRegD,Q=sigCQ,WE=sigCWE,CLK=clk)
WEREG(D=sigRegD,Q=sigDQ,WE=sigDWE,CLK=clk)

# Data Memory
MUX(Inputs=(sigIm,sigAQ,sigBQ,sigCQ,sigDQ),Output=sigMemAddr,Sel=sigMemAddrSel)
MUX(Inputs=(sigIm,sigAQ,sigBQ,sigCQ,sigDQ),Output=sigMemDin,Sel=sigMemDinSel)
dmem = RAM(size=65536,address=sigMemAddr,clock=clk,we=sigMemWE,re=sigMemRE,dataIn=sigMemDin,dataOut=sigMemDout)
dmem.ram[82] = 63320
dmem.ram[112] = 37

# Instruction Memory
sigIMemDout = Vector(32)
imem = RAM(size=65536,address=sigIMemAddr,clock=clk,we=GND,re=sigIMemRE,dataIn=cZero32,dataOut=sigIMemDout)
imem.ram[0] = OPCODE.NOP
imem.ram[1] = OPCODE.MOV | (MOVOP.A << 8)      | (MOVOP.IM << 11)      | (112 << 14)     | 0
imem.ram[2] = OPCODE.MOV | (MOVOP.B << 8)      | (MOVOP.A << 11)       | 0               | 0
imem.ram[3] = OPCODE.MOV | (MOVOP.C << 8)      | (MOVOP.IM2MEM << 11)  | (82 << 14)      | 0
imem.ram[4] = OPCODE.MOV | (MOVOP.D << 8)      | (MOVOP.REG2MEM << 11) | 0               | (MOVOP.C << 30)
#imem.ram[6]= OPCODE.MOV | (OP.REG2MEM << 8)   | (OP.REGC << 11)       | 0               | (OP.B << 30)
imem.ram[7] = OPCODE.MOV | (MOVOP.IM2MEM << 8) | (MOVOP.A)             | (32 << 14)      | 0


# Controller
controller = ControlUnit(
    # Instruction Memory
    Instruction=sigIMemDout,
    Clock=clk,
    IMemRE=sigIMemRE,
    IMemAddr=sigIMemAddr,
    # Data Memory
    DMemAddrMuxSel=sigMemAddrSel,
    DMemDinMuxSel=sigMemDinSel,
    DMemRE=sigMemRE,
    DMemWE=sigMemWE,
    # Immediate
    Immediate=sigIm,
    # Registers
    RegMuxSel=sigRegDSel,
    AWE=sigAWE,
    BWE=sigBWE,
    CWE=sigCWE,
    DWE=sigDWE,
    ALUCntrl=(sigALUControl := ALUControl())
)

ALU(ctrl=sigALUControl,A=sigALUA,B=sigALUB,Out=sigALU,Carry=Net(),Overflow=Net(),Zero=Net())

simulateTimeUnit(3600)
# Store the ram to a file to make it easier to debug
with open("ram.hex","wb") as fout:
    for word in dmem.ram:
        fout.write(bytes([word & 0xFF,(word >> 8) & 0xFF ]))

writeVCD("cpu.vcd")