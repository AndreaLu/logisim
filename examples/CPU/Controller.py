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
        (cFetch := Vector(StateSize)).set(STATE.FETCH)
        (cExecute := Vector(StateSize)).set(STATE.EXECUTE)
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
            if sigStateQ.get() == STATE.FETCH:
                AWE.set(0)
                BWE.set(0)
                CWE.set(0)
                DWE.set(0)
                DMemWE.set(0)
            else:
                DMemRE.set(0)

            # MOV Instruction
            if Instruction.get() & 0xFF == OPCODE.MOV:
                dst = (Instruction.get() >> 8) & 0b111   # op1 = instr[8:11] = dst
                src = (Instruction.get() >> 11) & 0b111 # op2 = instr[11:14] = src
                if sigStateQ.get() == STATE.FETCH:
                    # Destination is a register
                    if dst in (OP.REGA,OP.REGB,OP.REGC,OP.REGD):
                        if src == OP.REGA:
                            RegMuxSel.set( REGMUXSEL.REGA )
                        elif src == OP.REGB:
                            RegMuxSel.set( REGMUXSEL.REGB )
                        elif src == OP.REGC:
                            RegMuxSel.set( REGMUXSEL.REGC )
                        elif src == OP.REGD:
                            RegMuxSel.set( REGMUXSEL.REGD )
                        elif src in (OP.IM2MEM,OP.REG2MEM):
                            RegMuxSel.set( REGMUXSEL.MEMORY )
                            if src == OP.IM2MEM:
                                DMemAddrMuxSel.set(DMEMADDRMUXSEL.IMMEDIATE)
                                DMemRE.set(1)
                            else:
                                DMemAddrMuxSel.set(
                                    (DMEMADDRMUXSEL.REGA,
                                    DMEMADDRMUXSEL.REGB,
                                    DMEMADDRMUXSEL.REGC,
                                    DMEMADDRMUXSEL.REGD)[
                                        (Instruction.get() >> 30) & 0b11
                                    ]
                                )
                                DMemRE.set(1)

                        elif src == OP.IM:
                            RegMuxSel.set( REGMUXSEL.IMMEDIATE )
                    elif dst in (OP.REG2MEM,OP.IM2MEM):
                        if src == OP.REGA: DMemDinMuxSel.set(DMEMDINMUXSEL.REGA)
                        elif src == OP.REGB: DMemDinMuxSel.set(DMEMDINMUXSEL.REGB)
                        elif src == OP.REGC: DMemDinMuxSel.set(DMEMDINMUXSEL.REGC)
                        elif src == OP.REGD: DMemDinMuxSel.set(DMEMDINMUXSEL.REGD)
                        elif src == OP.IM: DMemDinMuxSel.set(DMEMDINMUXSEL.IMMEDIATE)
                        if dst == OP.REG2MEM:
                            DMemAddrMuxSel.set(
                                (DMEMADDRMUXSEL.REGA,
                                DMEMADDRMUXSEL.REGB,
                                DMEMADDRMUXSEL.REGC,
                                DMEMADDRMUXSEL.REGD)[
                                    (Instruction.get() >> 30) & 0b11
                                ]
                            )
     
                        else:
                            DMemAddrMuxSel.set( DMEMADDRMUXSEL.IMMEDIATE )
                elif sigStateQ.get() == STATE.EXECUTE:
                    if dst == OP.REGA: AWE.set(1)
                    elif dst == OP.REGB: BWE.set(1)
                    elif dst == OP.REGC: CWE.set(1)
                    elif dst == OP.REGD: DWE.set(1)
                    elif dst in (OP.REG2MEM,OP.IM2MEM):
                        DMemWE.set(1)


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
