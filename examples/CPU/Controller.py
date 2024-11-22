import sys

sys.path.append("../../") # let python find logisim

from logisim import Cell,Net,Vector,BUFF,Gate,OR,AND,PROCESS
from logisim.arith import EQUALS,ADDER
from logisim.seq import REG,WEREG
from logisim.comb import MUX
from CPUDefs import *

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

        
        # Immediate 
        for i in range(16):
            BUFF(inputs=(Instruction.nets[i+8+6],),output=Immediate.nets[i])
        #BUFF(inputs=Instruction.nets[8+6:8+6+16],output=Immediate)

        def p():
            if sigStateQ.get() == STATE.FETCH.value:
                AWE.set(0)
                BWE.set(0)
                CWE.set(0)
                DWE.set(0)
            else:
                DMemRE.set(0)

            # MOV Instruction
            if Instruction.get() & 0xFF == OPCODE.MOV.value:
                dst = (Instruction.get() >> 8) & 0b111   # op1 = instr[8:11] = dst
                src = (Instruction.get() >> 11) & 0b111 # op2 = instr[11:14] = src
                if sigStateQ.get() == STATE.FETCH.value:
                    # Destination is a register
                    if dst in (OP.REGA.value,OP.REGB.value,OP.REGC.value,OP.REGD.value):
                        if src == OP.REGA.value:
                            RegMuxSel.set( REGMUXSEL.REGA.value )
                        elif src == OP.REGB.value:
                            RegMuxSel.set( REGMUXSEL.REGB.value )
                        elif src == OP.REGC.value:
                            RegMuxSel.set( REGMUXSEL.REGC.value )
                        elif src == OP.REGD.value:
                            RegMuxSel.set( REGMUXSEL.REGD.value )
                        elif src in (OP.IM2MEM.value,OP.REG2MEM.value):
                            RegMuxSel.set( REGMUXSEL.MEMORY.value )
                            if src == OP.IM2MEM.value:
                                DMemAddrMuxSel.set(DMEMADDRMUXSEL.IMMEDIATE.value)
                                DMemRE.set(1)
                            else:
                                DMemAddrMuxSel.set(
                                    (DMEMADDRMUXSEL.REGA.value,
                                    DMEMADDRMUXSEL.REGB.value,
                                    DMEMADDRMUXSEL.REGC.value,
                                    DMEMADDRMUXSEL.REGD.value)[
                                        (Instruction.get() >> 30) & 0b11
                                    ]
                                )
                                DMemRE.set(1)

                        elif src == OP.IM:
                            RegMuxSel.set( REGMUXSEL.IMMEDIATE.value )
                elif sigStateQ.get() == STATE.EXECUTE.value:
                    
                    if dst == OP.REGA.value: AWE.set(1)
                    elif dst == OP.REGB.value: BWE.set(1)
                    elif dst == OP.REGC.value: CWE.set(1)
                    elif dst == OP.REGD.value: DWE.set(1)

        PROCESS(p)



        

if __name__ == "__main__":
    from logisim.seq import OSCILLATOR
    from logisim import simulateTimeUnit,writeVCD
    clk = Net()
    OSCILLATOR(100,clk)
    controller = Controller(
        Vector(16), clk, Net(), Vector(3), Vector(3), Net(), Net(), Vector(16), Vector(3), Net(), Net(), Net(), Net()
    )

    simulateTimeUnit(1000)
    writeVCD("Controller.vcd")
