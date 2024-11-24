import sys

sys.path.append("../../") # let python find logisim

from logisim import Cell,Net,Vector,BUFF,Gate,OR,AND,PROCESS
from logisim.arith import EQUALS,ADDER
from logisim.seq import REG,WEREG
from logisim.comb import MUX
from CPUDefs import *

class ControlUnit(Cell):
    def __init__(self,
            # Inputs
            Instruction : Vector,
            Clock : Net,
            AQ : Vector,
            BQ : Vector,
            CQ : Vector,
            DQ : Vector,
            Status : ALUStatus,
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
            DWE : Net,
            ALUCntrl : ALUControl,
            ALUMuxA : Vector,
            ALUMuxB : Vector,
            State : Net
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
        BUFF(inputs=(sigStateQ.nets[0],),output=State)

        # Program Counter
        (cOne16 := Vector(16)).set(1)
        sigPCD,sigPCQ = Vector(16), Vector(16)
        self.sigPCQ = sigPCQ
        ADDER(A=sigPCQ,B=cOne16,Out=(sigPCDDef:=Vector(16)))
        MUX(Inputs=(sigPCDDef,AQ,BQ,CQ,DQ,Immediate),Output=sigPCD,Sel=(sigPCDSel:=Vector(3)))
        self.sigPCDSel = sigPCDSel
        WEREG(D=sigPCD,Q=sigPCQ,WE=(sigPCWE := Net()),CLK=Clock,Qinit=0xFFFF)

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
                sigPCWE.set(1)
                sigPCDSel.set(PCDSEL.DEF)
                ALUCntrl.enable.set(0)
            else:
                DMemRE.set(0)
                sigPCWE.set(0)

            # MOV Instruction
            instruction = Instruction.get()
            opcode = instruction & 0xFF
            if opcode == OPCODE.MOV:
                dst = (Instruction.get() >> 8) & 0b111   # op1 = instr[8:11] = dst
                src = (Instruction.get() >> 11) & 0b111 # op2 = instr[11:14] = src
                if sigStateQ.get() == STATE.FETCH:
                    # Destination is a register
                    if dst in (MOVOP.A,MOVOP.B,MOVOP.C,MOVOP.D):
                        if src == MOVOP.A:
                            RegMuxSel.set( REGMUXSEL.REGA )
                        elif src == MOVOP.B:
                            RegMuxSel.set( REGMUXSEL.REGB )
                        elif src == MOVOP.C:
                            RegMuxSel.set( REGMUXSEL.REGC )
                        elif src == MOVOP.D:
                            RegMuxSel.set( REGMUXSEL.REGD )
                        elif src in (MOVOP.IM2MEM,MOVOP.REG2MEM):
                            RegMuxSel.set( REGMUXSEL.MEMORY )
                            if src == MOVOP.IM2MEM:
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

                        elif src == MOVOP.IM:
                            RegMuxSel.set( REGMUXSEL.IMMEDIATE )
                    elif dst in (MOVOP.REG2MEM,MOVOP.IM2MEM):
                        if src == MOVOP.A: DMemDinMuxSel.set(DMEMDINMUXSEL.REGA)
                        elif src == MOVOP.B: DMemDinMuxSel.set(DMEMDINMUXSEL.REGB)
                        elif src == MOVOP.C: DMemDinMuxSel.set(DMEMDINMUXSEL.REGC)
                        elif src == MOVOP.D: DMemDinMuxSel.set(DMEMDINMUXSEL.REGD)
                        elif src == MOVOP.IM: DMemDinMuxSel.set(DMEMDINMUXSEL.IMMEDIATE)
                        if dst == MOVOP.REG2MEM:
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
                    if dst == MOVOP.A: AWE.set(1)
                    elif dst == MOVOP.B: BWE.set(1)
                    elif dst == MOVOP.C: CWE.set(1)
                    elif dst == MOVOP.D: DWE.set(1)
                    elif dst in (MOVOP.REG2MEM,MOVOP.IM2MEM):
                        DMemWE.set(1)
            elif opcode in (OPCODE.ADD,OPCODE.SUB,OPCODE.CMP):
                if opcode in (OPCODE.SUB,OPCODE.CMP):
                    ALUCntrl.opType.set( ALUOpType.SUB )
                else:
                    ALUCntrl.opType.set( ALUOpType.ADD )
                ALUCntrl.enable.set(1)
                op = (instruction >> 8) & 0b111
                if op == ADDOP.A: ALUMuxA.set(DMEMADDRMUXSEL.REGA)
                elif op == ADDOP.B: ALUMuxA.set(DMEMADDRMUXSEL.REGB)
                elif op == ADDOP.C: ALUMuxA.set(DMEMADDRMUXSEL.REGC)
                elif op == ADDOP.D: ALUMuxA.set(DMEMADDRMUXSEL.REGD)
                elif op == ADDOP.IM: ALUMuxA.set(DMEMADDRMUXSEL.IMMEDIATE)
                else: raise Exception(f"invalid first operand value {hex(op)} in ADD instruction {hex(instruction)}")
                op = (instruction >> 11) & 0b111
                if op == ADDOP.A: ALUMuxB.set(DMEMADDRMUXSEL.REGA)
                elif op == ADDOP.B: ALUMuxB.set(DMEMADDRMUXSEL.REGB)
                elif op == ADDOP.C: ALUMuxB.set(DMEMADDRMUXSEL.REGC)
                elif op == ADDOP.D: ALUMuxB.set(DMEMADDRMUXSEL.REGD)
                elif op == ADDOP.IM: ALUMuxB.set(DMEMADDRMUXSEL.IMMEDIATE)
                else: raise Exception(f"invalid second operand value {hex(op)} in ADD instruction {hex(instruction)}")


                if sigStateQ.get() == STATE.EXECUTE and opcode != OPCODE.CMP:
                    RegMuxSel.set( REGMUXSEL.ALU )
                    dst = (instruction >> 30) & 0b11
                    if dst == MOVOP.A: AWE.set(1)
                    elif dst == MOVOP.B: BWE.set(1)
                    elif dst == MOVOP.C: CWE.set(1)
                    elif dst == MOVOP.D: DWE.set(1)
            elif opcode == OPCODE.JMP:
                cnd = (instruction >> 8) & 0b111
                src = (instruction >> 11) & 0b111
                if sigStateQ.get() == STATE.FETCH:
                    if (cnd == JMPCND.UNC) or \
                       (cnd == JMPCND.EQ and Status.Z.get() == 1) or \
                       (cnd == JMPCND.NEQ and Status.Z.get() == 0):
                        if   src == JMPOP.A: sigPCDSel.set(PCDSEL.A)
                        elif src == JMPOP.B: sigPCDSel.set(PCDSEL.B)
                        elif src == JMPOP.C: sigPCDSel.set(PCDSEL.C)
                        elif src == JMPOP.D: sigPCDSel.set(PCDSEL.D)
                        elif src == JMPOP.IM: sigPCDSel.set(PCDSEL.IM)

        PROCESS(p)



        

if __name__ == "__main__":
    from logisim.seq import OSCILLATOR
    from logisim import simulateTimeUnit,writeVCD
    clk = Net()
    OSCILLATOR(100,clk)
    controller = ControlUnit(
        Vector(16), clk, Net(), Vector(3), Vector(3), Net(), Net(), Vector(16), Vector(3), Net(), Net(), Net(), Net()
    )

    simulateTimeUnit(1000)
    writeVCD("Controller.vcd")
