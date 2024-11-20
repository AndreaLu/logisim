from enum import Enum, auto
from math import ceil,log2
import sys

sys.path.append("../../") # let python find logisim

from logisim import Cell,Net,Vector,BUFF,Gate,OR,AND
from logisim.arith import EQUALS,ADDER
from logisim.seq import REG,WEREG
from logisim.comb import MUX
from CPU import OPCODE,INSTRUCTION_OPCODE_LENGTH

class STATE(Enum):
    def _generate_next_value_(name, start, count, last_values):
        return count
    FETCH   = auto()
    EXECUTE = auto()
    SIZE    = auto()

StateSize = ceil(log2(STATE.SIZE.value))

class Controller(Cell):
    def __init__(self,
        # Inputs
        Instruction : Vector,
        Clock : Net,
        # Outputs
        IMemRE : Net,
        IMemAddr : Vector,
        DMemAddrMuxSel : Vector,
        DMemDinMuxSel : Vector,
        DMemRE : Net,
        DMemWE : Net,
        Immediate : Vector,
        RegMuxSel : Vector,
        AWE : Net,
        BWE : Net,
        CWE : Net,
        DWE : Net
        ):

        sigStateQ = Vector(StateSize)
        sigStateD = Vector(StateSize)
        self.sigStateQ = sigStateQ
        sigStateIsFetch = Net()
        sigStateIsExecute = Net()
        (cOneS := Vector(StateSize)).set(1)
        (cFetch := Vector(StateSize)).set(STATE.FETCH.value)
        (cExecute := Vector(StateSize)).set(STATE.EXECUTE.value)
        EQUALS(A=sigStateQ,B=cFetch,Out=sigStateIsFetch)
        EQUALS(A=sigStateQ,B=cExecute,Out=sigStateIsExecute)

        # Passa al prossimo stato con +1 o torna a fetch se lo stato è l'ultimo
        ADDER(A=cOneS,B=sigStateQ,Out=(sigStateInt := Vector(StateSize)))
        MUX(Inputs=(sigStateInt,cFetch),Output=sigStateD,Sel=sigStateIsExecute)
        REG(D=sigStateD,clock=Clock,Q=sigStateQ)

        # Program Counter
        (cOne16 := Vector(16)).set(1)
        sigPCD,sigPCQ = Vector(16), Vector(16)
        ADDER(A=sigPCQ,B=cOne16,Out=sigPCD)
        WEREG(D=sigPCD,Q=sigPCQ,WE=sigStateIsFetch,CLK=Clock,Qinit=0xFFFF)

        # Instruction memory
        BUFF(inputs=(sigPCQ,),output=IMemAddr)
        BUFF(inputs=(sigStateIsExecute,),output=IMemRE)

        # MOV INSTRUCTIONS
        (cMOVRR := Vector(INSTRUCTION_OPCODE_LENGTH)).set(OPCODE.MOVRR)
        EQUALS(A=Insturction,B=cMOVRR,Out=(sigInstrIsMOVRR := Net()))
        
        
        OR(
        inputs=(
            AND(
            inputs=(
                sigInstrIsMOVRR,
                
            ), ouptut=Net()
            )
        ),
        output=RegMuxSel
        )




        

if __name__ == "__main__":*
    from logisim.seq import OSCILLATOR
    from logisim import simulateTimeUnit,writeVCD
    clk = Net()
    OSCILLATOR(100,clk)
    controller = Controller(
        Vector(16), clk, Net(), Vector(3), Vector(3), Net(), Net(), Vector(16), Vector(3), Net(), Net(), Net(), Net()
    )

    simulateTimeUnit(1000)
    writeVCD("Controller.vcd")
