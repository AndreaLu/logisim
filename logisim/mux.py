from .logisim import Vector,NOT,Net,AND,OR
from math import log2, ceil
class MUX:
    def __init__(self,Inputs: tuple[Vector], Output: Vector, Address:Vector):
        wordLen = Output.length
        for input in Inputs:
            assert input.length == wordLen
        size = len(Inputs)
        addressSize = ceil(log2(size))
        assert Address.length >= addressSize

        inputInts = []

        index = -1
        for input in Inputs:
            inputInt = Vector(wordLen)
            inputInts.append(inputInt)
            index += 1
            selector = Net()

            addrNets = [] # list nof Nets to and to create the selector
            for i in range(addressSize):
                if (index >> i) & 1 == 1:
                    addrNets.append( Address.nets[i] )
                else:
                    newNet = Net()
                    NOT( (Address.nets[i],),newNet)
                    addrNets.append( newNet )
            AND( addrNets, selector )
            
            for i in range(wordLen):
                AND( (input.nets[i], selector), inputInt.nets[i] )
        
        for i in range(wordLen):
            OR( [j.nets[i] for j in inputInts], Output.nets[i] )
