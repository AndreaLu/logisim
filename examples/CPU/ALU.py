import sys

sys.path.append("../../") # let python find logisim

from logisim import Net,Vector,NOT,BUFF,PROCESS,Cell,NOR,AND,VDD
from logisim.arith import ADDER,EQUALS
from logisim.comb import MUX
from logisim.seq import WEREG
from CPUDefs import ALUControl,ALUOpType,ALUStatus,STATE

# Generates the 2's complement of the input
class Complementer:
    def __init__(self, Input : Vector, Output: Vector):
        assert (wordLen := Input.length) == Output.length
        
        sigInputN = Vector(wordLen)
        (cOne := Vector(wordLen)).set(1)
        
        NOT(inputs=(Input,),output=sigInputN)
        ADDER(A=cOne,B=sigInputN,Out=Output)

class Rotator:
    def __init__(self,Input : Vector, Output: Vector, ):
        pass

class ALUCU:
    def __init__(self, ctrl: ALUControl, adderMuxSel:Vector):
        def p():
            opType = ctrl.opType.get()
            if opType == ALUOpType.ADD:
                adderMuxSel.set(0)
            elif opType == ALUOpType.SUB:
                adderMuxSel.set(1)

        PROCESS(p)

class ALU(Cell):
    def __init__(self, ctrl: ALUControl, A: Vector,B:Vector, Out :Vector, Carry: Net, Overflow:Net,Clock: Net, Status:ALUStatus, CPUState:Net):
        assert (wordLen := A.length) == B.length
    
        # Control Unit
        ALUCU(ctrl=ctrl,adderMuxSel=(sigAdderMuxSel := Net()))

        # Addition/Subtraction
        Complementer(Input=B,Output=(sigBCompl:=Vector(wordLen)))
        MUX(Inputs=(B,sigBCompl), Output=(sigB:=Vector(wordLen)), Sel=sigAdderMuxSel)
        ADDER(A=A,B=sigB,Out=(sigOutAdder := Vector(wordLen)))

        # Status Register
        (cEXECUTE := Net()).set(STATE.EXECUTE)
        (one := Net()).set(1)
        AND(inputs=(one,CPUState),output=(sigStateIsExecute:=Net()))
        WEREG(D=(sigStatD:=ALUStatus()),Q=Status,WE=(sigStatWE:=Net()),CLK=Clock)
        AND(inputs=(sigStateIsExecute,ctrl.enable),output=sigStatWE)
        NOR(inputs=sigOutAdder.nets,output=sigStatD.Z)
        BUFF(inputs=(sigOutAdder,),output=Out)


if __name__ == "__main__":
    from logisim import simulateTimeUnit, writeVCD

    (ctrl := ALUControl()).opType.set(ALUOpType.SUB)
    (A := Vector(16)).set(1300)
    (B := Vector(16)).set(83)
    Out = Vector(16)

    Carry,Overflow,Zero = Net(),Net(),Net()
    ALU(ctrl,A,B,Out,Carry,Overflow,Zero)
    
    simulateTimeUnit(300)
    writeVCD("alu.vcd")

    
