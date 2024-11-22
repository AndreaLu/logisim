import sys
from CPUDefs import *
# Example of a simple 16 bit harvard CPU
from Controller import Controller

sys.path.append("../../") # let python find logisim
from logisim.seq import WEREG,OSCILLATOR,RAM
from logisim.comb import MUX
from logisim import Net,Vector,GND,VDD,gates
from logisim import simulateTimeUnit,writeVCD




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
sigMemAddrSel,sigMemDinSel = Vector(3),Vector(3)
sigMemRE,sigMemWE = Net(),Net()
sigMemDin = Vector(16)
(cZero32 := Vector(32)).set(0)

sigIMemAddr = Vector(16)
sigIMemRE = Net()


OSCILLATOR(100,clk)

# Registers
MUX(Inputs=(sigIm,sigAQ,sigBQ,sigCQ,sigDQ,sigMemDout),Output=sigRegD,Sel=sigRegDSel)
WEREG(D=sigRegD,Q=sigAQ,WE=sigAWE,CLK=clk)
WEREG(D=sigRegD,Q=sigBQ,WE=sigBWE,CLK=clk)
WEREG(D=sigRegD,Q=sigCQ,WE=sigCWE,CLK=clk)
WEREG(D=sigRegD,Q=sigDQ,WE=sigDWE,CLK=clk)

# Data Memory
MUX(Inputs=(sigIm,sigAQ,sigBQ,sigCQ,sigDQ),Output=sigMemAddr,Sel=sigMemAddrSel)
MUX(Inputs=(sigIm,sigAQ,sigBQ,sigCQ,sigDQ),Output=sigMemDin,Sel=sigMemDinSel)
dmem = RAM(size=65536,address=sigMemAddr,clock=clk,we=sigMemWE,re=sigMemRE,dataIn=sigMemDin,dataOut=sigMemDout)
dmem.ram[82] = 63320

# Instruction Memory
sigIMemDout = Vector(32)
imem = RAM(size=65536,address=sigIMemAddr,clock=clk,we=GND,re=sigIMemRE,dataIn=cZero32,dataOut=sigIMemDout)
imem.ram[0] = OPCODE.NOP.value
imem.ram[1] = OPCODE.MOV.value | (OP.REGA.value << 8) | (OP.IM.value << 11) | (17 << 14)
imem.ram[2] = OPCODE.MOV.value | (OP.REGB.value << 8) | (OP.REGA.value << 11)
imem.ram[3] = OPCODE.MOV.value | (OP.REGC.value << 8) | (OP.IM2MEM.value << 11) | (82 << 14)


# Controller
controller = Controller(
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
    DWE=sigDWE
)

simulateTimeUnit(3000)
writeVCD("cpu.vcd")