import sys

sys.path.append("../../") # let python find logisim

from logisim import Net,Vector,NOT,BUFFEN,PROCESS,Cell,NOR,AND,VDD,NAND,GND,BUFF
from logisim.arith import ADDER,FullAdder
from logisim.comb import MUX,DECODER
from logisim.seq import WEREG,OSCILLATOR
from CPUDefs import ALUControl,ALUOpType,ALUStatus,STATE
from math import log2,ceil
# Generates the 2's complement of the input
class Complementer:
    def __init__(self, Input : Vector, Output: Vector):
        assert (wordLen := Input.length) == Output.length
        
        sigInputN = Vector(wordLen)
        (cOne := Vector(wordLen)).set(1)
        
        NOT(inputs=(Input,),output=sigInputN)
        ADDER(A=cOne,B=sigInputN,Out=Output)

class ShiftBuffer(Cell):
    def __init__(self,x:Net,f:Net,force:Net,en:Net,y:Net):
        #MUX(Inputs=(x,f),Sel=force,Output=(sigInt:=Net()))
        # TODO: implement the Net version of mux to use here (the previous declaration does not work)
        self.sigInt = (sigInt := Net())
        def p():
            sigInt.set( x.get() if force.get() == 0 else f.get() )
        PROCESS(p)
        BUFFEN(x=sigInt,en=en,y=y)

class Shifter(Cell):
    """This block can apply arithmetic/logic shifts and rotations
    isArithmetic: 1 indicates that the requested shift is arithmetic, 0 indicates a logic shift
    isRot: 1 indicates that requested operation is a rotation (bits shifted out enter the other side), 0 indicates a  shift
    isLeft: 1 indicates that the requested shift/rotate operation is left, 0 indicates right
    """
    def __init__(self,Input : Vector, Output: Vector, isArithmetic:Net, isRot:Net, isLeft:Net, amount:Vector):
        
        # Create the buffer matrix
        assert (wordLen := Input.length) == Output.length
        matrix = []
        """matrix[x][y] is the buffer which connects the x-th input net to the y-th output net"""
        
        self.sigForce = (sigForce := Net())
        self.sigForceLeft = (sigForceLeft := Net())
        self.sigForceVal = (sigForceVal := Net())
        self.sigEnable = (sigEnable := Vector(wordLen))

        for x in range(wordLen):
            matrix.append([])
            for y in range(wordLen):
                if ((x < y) and (x < (wordLen-1))):
                    force = sigForce
                elif x > y and x > 0:
                    force = sigForceLeft
                else:
                    force = GND

                enable = sigEnable.nets[ (x-y) % wordLen ]
                #print(f"matrix[{x}][{y}] enable is sigEnable[{(x-y) % wordLen }]")
                matrix[x].append(
                    ShiftBuffer(
                        x=Input.nets[x],
                        y=Output.nets[y],
                        force=force,
                        f=sigForceVal,
                        en=enable
                    )
                )
        
        # Control force and forceVal
        # TODO: once the circuit works, implement this with logic
        def p():
            if isRot.get() == 1:
                sigForce.set(0)
                sigForceLeft.set(0)
            else:
                if isLeft.get() == 1:
                    sigForceVal.set(0)
                    sigForce.set(0)
                    sigForceLeft.set(1)
                else:
                    sigForce.set(1)
                    sigForceLeft.set(0)
                    if isArithmetic.get() == 1:
                        # Sign extension in case of right arithmetic shifts
                        sigForceVal.set( Input.nets[wordLen-1].get() )
                    else:
                        sigForceVal.set(0)
        PROCESS(p)

        
        amountSize = ceil(log2(wordLen))
        assert amount.length == amountSize
        
        pAmount = Vector(amountSize+1)
        pAmount[amountSize-1].set(0)
        for i in range(amountSize): BUFF((amount.nets[i],),pAmount.nets[i])
        Complementer(Input=pAmount,Output=(nAmount:=Vector(amountSize+1)))
        ADDER(A=nAmount,B=(cWordLen:=Vector(amountSize+1)),Out=(intAmount:=Vector(amountSize+1)))
        cWordLen.set(wordLen)
        leftShiftAmount = Vector(amountSize)
        for i in range(amountSize): BUFF((intAmount.nets[i],),leftShiftAmount.nets[i])
        MUX(Inputs=(amount,leftShiftAmount),Output=(actualAmount:=Vector(amountSize)),Sel=isLeft)
        self.actualAmount = actualAmount
        DECODER(Input=actualAmount,Outputs=sigEnable)


        
                


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

        for i in range(wordLen):
            FullAdder(
                A=VDD if i == 0 else carry,
                B=co[i],
                Cin= so[i] if i < wordLen-1 else VDD,
                S=C.nets[wordLen+i],
                Cout=(carry:=Net())
            )
        
        # Overflow is 1 when wordLen+1 most significant bits are not all the same
        AND(C.nets[wordLen-1:],(sigAllOnes:=Net()))
        NOR(C.nets[wordLen-1:],(sigAllZeros:=Net()))
        NOR((sigAllZeros,sigAllOnes),Overflow)

class ALUCU:
    def __init__(self, ctrl: ALUControl, adderMuxSel:Vector, outMuxSel:Vector):
        def p():
            opType = ctrl.opType.get()
            if opType == ALUOpType.ADD:
                adderMuxSel.set(0)
                outMuxSel.set(0)
            elif opType == ALUOpType.SUB:
                adderMuxSel.set(1)
                outMuxSel.set(0)
            elif opType == ALUOpType.MUL:
                outMuxSel.set(1)

        PROCESS(p)

class ALU(Cell):
    def __init__(self, ctrl: ALUControl, A: Vector,B:Vector, Out :Vector, Carry: Net, Overflow:Net,Clock: Net, Status:ALUStatus, CPUState:Net):
        assert (wordLen := A.length) == B.length
    
        # Control Unit
        ALUCU(ctrl=ctrl,adderMuxSel=(sigAdderMuxSel := Net()),outMuxSel=(sigOutMuxSel:=Vector(1)))

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

        # Multiplication
        BWMultiplier(A=A,B=B,C=(sigOutMul:=Vector(wordLen*2)),Overflow=sigStatD.O)

        # Output
        MUX((sigOutAdder,sigOutMul[:wordLen]),Output=Out,Sel=sigOutMuxSel)


if __name__ == "__main__":
    from logisim import simulateTimeUnit, writeVCD
    from logisim.seq import REG

    A = Vector(4)
    A.set(0b1011)
    (amount := Vector(2)).set(1)

    clk = Net()

    OSCILLATOR(100,clk)
    
    REG(D=(sigAmountD:=Vector(2)),clock=clk,Q=amount)
    ADDER(A=amount,B=(one2:=Vector(2)),Out=sigAmountD)
    one2.set(1)
    
    rotLeft     = Vector(4)
    rotRight    = Vector(4)
    shiftLeft   = Vector(4) # TODO: BUGGED, 0011 << 1 -> 0001 instead of 0110
    # Il motivo è probabilmente che per inserire gli zeri a destra mi servono i buffer con l'abilitazione a forzare dove non li ho...
    shiftLRight = Vector(4)
    shiftARight = Vector(4)
    
    sRotLeft   = Shifter(Input=A,Output=rotLeft,    isArithmetic=GND,  isRot=VDD,   isLeft=VDD,   amount=amount)
    sRotRight  = Shifter(Input=A,Output=rotRight,   isArithmetic=GND,  isRot=VDD,   isLeft=GND,   amount=amount)
    sShiLeft   = Shifter(Input=A,Output=shiftLeft,  isArithmetic=GND,  isRot=GND,   isLeft=VDD,   amount=amount)
    sShiLRight = Shifter(Input=A,Output=shiftLRight,isArithmetic=GND,  isRot=GND,   isLeft=GND,   amount=amount)
    sShiARight = Shifter(Input=A,Output=shiftARight,isArithmetic=VDD,  isRot=GND,   isLeft=GND,   amount=amount)

    simulateTimeUnit(400)
    writeVCD("alu.vcd")

    
