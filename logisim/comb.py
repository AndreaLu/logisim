from .logisim import Vector,NOT,Net,AND,OR
from math import log2, ceil

class MUX:
    def __init__(self,Inputs: tuple[Vector], Output: Vector, Sel:Vector|Net):
        wordLen = Output.length
        for input in Inputs:
            assert input.length == wordLen
        
        size = len(Inputs)
        selSize = ceil(log2(size))
        if selSize > 1:
            assert type(Sel) is Vector
            assert Sel.length >= selSize

        # Create the negated version of sel
        if type(Sel) is Vector:
            SelN = Vector(selSize)
            for i in range(selSize):
                NOT((Sel.nets[i],),SelN.nets[i])
        else: # sel is a single Net
            SelN = Net()
            NOT((Sel,),SelN)


        inputInts = []

        index = -1
        for input in Inputs:
            index += 1
            inputInt = Vector(wordLen)
            inputInts.append(inputInt)

            # Create a selector for this input
            selector = Net()
            andNets = [] # list nof Nets to and to create the selector
            if type(Sel) is Net:
                if index == 0:
                    andNets.append( SelN )
                else:
                    andNets.append( Sel )
            else:
                for i in range(selSize):
                    if (index >> i) & 1 == 1:
                        andNets.append( Sel.nets[i] )
                    else:
                        andNets.append( SelN.nets[i] )
            AND( andNets, selector )
            
            # Generate this internal input gated by the selector
            for i in range(wordLen):
                AND( (input.nets[i], selector), inputInt.nets[i] )
        
        # Or all the internal inputs into the output
        for i in range(wordLen):
            OR( [j.nets[i] for j in inputInts], Output.nets[i] )

class DEMUX:
    def __init__(self,Input:Vector,Sel:Vector|Net,Outputs:tuple[Vector]):
        wordLen = Input.length
        for output in Outputs:
            assert output.length == wordLen

        
        size = len(Outputs)
        selSize = ceil(log2(size))
        if selSize > 1:
            assert type(Sel) is Vector
            assert Sel.length >= selSize

        # Create the negated version of sel
        if type(Sel) is Vector:
            SelN = Vector(selSize)
            for i in range(selSize):
                NOT((Sel.nets[i],),SelN.nets[i])
        else: # sel is a single Net
            SelN = Net()
            NOT((Sel,),SelN)
        
        outputIndex = -1
        for output in Outputs:

            outputIndex += 1
            # For each possible output, generate a selctor net
            outputSelector = Net()

            andNets = [] # list nof Nets to and to create the outputSelector
            if type(Sel) is Net:
                if outputIndex == 0:
                    andNets.append( SelN )
                else:
                    andNets.append( Sel )
            else:
                for i in range(selSize):
                    if (outputIndex >> i) & 1 == 1:
                        andNets.append( Sel.nets[i] )
                    else:
                        andNets.append( SelN.nets[i] )
            AND( andNets, outputSelector )
            
            for i in range(wordLen):
                AND( (Input.nets[i], outputSelector), output.nets[i] )



# Test procedure, run with `python -m logisim.comb`
if __name__ == "__main__":
    from .logisim import simulateTimeUnit, writeVCD, Net
    from .arith import ADDER
    from .seq import REG, OSCILLATOR
    
    # Test circuit for the multiplexer, create a selector which sweeps
    # through all the inputs with a counter and use it to connect the given
    # input to the output
    inputs = [Vector(8) for i in range(8)]
    out = Vector(8)
    clkSlow = Net()
    selD = Vector(3)
    selQ = Vector(3)
    one = Vector(3)
    ADDER(A=one,B=selQ,Out=selD)
    REG(D=selD,clock=clkSlow,Q=selQ)
    OSCILLATOR(50,clkSlow)
    MUX(Inputs=inputs,Output=out,Sel=selQ)

    for i in range(8):
        inputs[i].set(i)
    one.set(1)

    simulateTimeUnit(3000)
    writeVCD("mux.vcd")

