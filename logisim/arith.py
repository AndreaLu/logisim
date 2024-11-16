import logisim
from .logisim import Net,Vector,XOR,AND,GND,OR
from .seq import REG

class HalfAdder:
    def __init__(self,A:Net,B:Net,C:Net,S:Net):
        XOR( (A,B), S )
        AND( (A,B), C )

class FullAdder:
    def __init__(self,A:Net,B:Net,Cin:Net,S:Net,Cout:Net):
        self.sint = Net()
        self.cint = Net()
        self.cint2 = Net()
        HalfAdder(A,B,self.cint,self.sint)
        HalfAdder(self.sint,Cin,self.cint2,S)
        OR( (self.cint2,self.cint), Cout)

class ADDER:
    def __init__(self, A:Vector, B:Vector, Out:Vector):
        wordLen = A.length
        assert B.length == wordLen
        assert Out.length == wordLen
        
        self.carry = Vector(wordLen+1)
        self.carry.nets[0].set(0)
        for i in range(wordLen):
            FullAdder( 
                A.nets[i],           # A
                B.nets[i],           # B
                self.carry.nets[i],  # Cin
                Out.nets[i],         # S
                self.carry.nets[i+1] # Cout
            )




