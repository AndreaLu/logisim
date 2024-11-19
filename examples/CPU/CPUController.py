from enum import Enum
from math import log2,ceil

sys.path.append("../../") # let python find logisim

from logisim import Vector,Net,Cell
from logisim import simulateTimeUnit,writeVCD
from logisim.seq import WEREG,REG,BUFF,OSCILLATOR
from logisim.arith import ADDER,EQUALS
from logisim.comb import MUX

from CPU import INSTRUCTION_LENGTH

class State(Enum):
    FETCH   = 0
    DECODE  = 1
    EXECUTE = 2
    COUNT   = 3 

class Controller(Cell):
    def __init__(self,iInstruction:Vector, clk:Net,oIMemRE:Net):

        # Instruction Memory control ports
        self.iIMemInstruction = iInstruction
        self.oIMemAddr = Vector(16)
        # Data Memory control ports
        self.oDMemAddr = Vector(16)
        self.oDMemAddrSel = Vector(2)
        self.oDMemDinSel = Vector(4)
        self.oDMemDoutSel = Vector(4)
        self.oDMemRE = Net()
        self.oDMemWR = Net()
        # ALU Control ports
        self.oALUOperation = Vector(2)
        self.oALUOp1Sel = Vector(2)
        self.oALUOp2Sel = Vector(2)


        sigStateIsFetch = Net()
        sigStateIsDecode = Net()
        self.sigStateIsDecode = sigStateIsDecode

        # Constants
        stateLen = ceil(log2(State.COUNT.value))
        (cFetch := Vector(stateLen)).set(State.FETCH.value)
        (cDecode := Vector(stateLen)).set(State.DECODE.value)
        (cExecute := Vector(stateLen)).set(State.EXECUTE.value)
        (cOnes := Vector(stateLen)).set(1)
        (cZeros := Vector(stateLen)).set(0)

        # Program Counter register
        self.sigPCD = (sigPCD := Vector(16))
        self.sigPCQ = (sigPCQ := Vector(16))
        self.pcdInt = (sigPCDint := Vector(16))
        (cOne16 := Vector(16)).set(1)
        REG(D=sigPCD,clock=clk,Q=sigPCQ)
        ADDER(A=sigPCQ,B=cOne16,Out=sigPCDint)
        MUX((sigPCQ,sigPCDint),sigPCD,sigStateIsDecode)

        # FSM State Register
        self.sigStateQ = (sigStateQ := Vector(stateLen))
        self.sigStateD = (sigStateD := Vector(stateLen))

        # oIMemRE =========================================================
        # this is asserted only during the fetch state
        EQUALS( sigStateQ, cFetch, sigStateIsFetch )
        EQUALS( sigStateQ, cDecode, sigStateIsDecode )
        BUFF((sigStateIsFetch,),oIMemRE)

        # oIMemAddr =======================================================
        # This is just the PC
        BUFF( (sigPCQ,), self.oIMemAddr)

        # sigStateD =======================================================
        # Each state lasts exactly one clock cycle we can just always
        # go to the next state
        sigStateInt = Vector(stateLen)
        self.sigStateClear = (sigStateClear := Net())
        (cStateCount := Vector(stateLen)).set(State.COUNT.value-1)
        ADDER( cOnes, sigStateQ, sigStateInt )
        # cycle back to zero
        EQUALS( sigStateQ, cStateCount, sigStateClear )
        MUX( (sigStateInt,cZeros), sigStateD, sigStateClear)
        REG( D=sigStateD, clock=clk, Q=sigStateQ)


clk = Net()
instruction = Vector(INSTRUCTION_LENGTH)
instruction.set(0)

IMemRE = Net()

OSCILLATOR(100,clk)
controller = Controller(instruction,clk,IMemRE)

simulateTimeUnit(10000)


writeVCD("cpu.vcd")


