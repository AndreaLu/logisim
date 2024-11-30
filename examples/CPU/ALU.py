import sys

sys.path.append("../../") # let python find logisim

from logisim import Net,Vector,NOT,BUFF,PROCESS,Cell,NOR,AND,VDD,NAND
from logisim.arith import ADDER,EQUALS,FullAdder
from logisim.comb import MUX
from logisim.seq import WEREG,OSCILLATOR
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


class BWMultiplier:
    """Baugh-Wooley multiplier"""
    def __init__(self,A:Vector, B:Vector, C:Vector, Overflow:Net):
        assert (wordLen := A.length) == B.length
        assert C.length == 2*wordLen

        class BWW:
            """Baugh-Wooley multiplier white-cell"""
            def __init__(self,a:Net, b:Net,ci:Net,si:Net,co:Net,so:Net):
                AND(inputs=(a,b),output=(_int:=Net()))
                FullAdder(A=_int,B=ci,Cin=si,S=so,Cout=co)

        class BWG:
            """Baugh-Wooley multiplier gray-cell"""
            def __init__(self,a:Net, b:Net,ci:Net,si:Net,co:Net,so:Net):
                NAND(inputs=(a,b),output=(_int:=Net()))
                FullAdder(A=_int,B=ci,Cin=si,S=so,Cout=co)
        
        si = [Net() for i in range(wordLen)]
        ci = [Net() for i in range(wordLen)]
        so = [Net() for i in range(wordLen)]
        co = [Net() for i in range(wordLen)]
        for i in range(wordLen-1):
            si[i].set(0)
            ci[i].set(0)

        for i in range(wordLen):
            for j in range(wordLen):
                gray = (wordLen-j) == 1
                if i == wordLen-1: gray = not gray
                if gray:
                    BWG(A.nets[j],B.nets[i],ci[j],si[j],co[j], C.nets[i] if j == 0 else so[j-1])
                else:
                    BWW(A.nets[j],B.nets[i],ci[j],si[j],co[j], C.nets[i] if j == 0 else so[j-1])
            so[wordLen-1].set(0)


            if i < wordLen-1:
                si,ci = so,co
                so = [Net() for i in range(wordLen)]
                co = [Net() for i in range(wordLen)]

        (carry := Net()).set(1)
        for i in range(wordLen):
           FullAdder(A=carry,B=co[i],Cin= so[i] if i < wordLen-1 else VDD,S=C.nets[wordLen+i],Cout=(cint:=Net()))
           carry = cint
        


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

    A,B,C,Overflow = Vector(16),Vector(16),Vector(32),Net()
    A.set(4320)
    B.set(321)
    clk = Net()

    OSCILLATOR(10,clk)
    BWMultiplier(A,B,C,Overflow)
    
    simulateTimeUnit(300)
    writeVCD("alu.vcd")

    
