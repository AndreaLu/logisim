from .logisim import NAND,Net,Vector
from math import log2,ceil
# D-PET Flip Flop
class DFF:
    def __init__(self, Din: Net, clock: Net, Q: Net, QInit=0):
        A = Net()
        B = Net()
        C = Net()
        D = Net()
        C.set(1)
        B.set(1)
        A.set(1)
        D.set(1)
        Qn = Net()
        Q.set(QInit)
        Qn.set(1-QInit)
        NAND( (D,B), A)
        NAND( (A,clock), B )
        NAND( (B,clock,D),C )
        NAND( (Din,C), D)
        NAND( (B,Qn), Q)
        NAND( (Q,C), Qn)

# Array of DFF. The size is the sam as the input/output vectors
class REG:
    def __init__(self, D : Vector, clock: Net, Q:Vector, Vinit=0):
        self.length = D.length
        if D.length != Q.length:
            raise Exception("D and Q vectors must have the same length")
        for i in range(self.length):
            DFF(D.nets[i],clock,Q.nets[i], (Vinit >> i) & 1 )

class REGFILE:
    def __init__(self, size:int, address:Vector, clock: Net, we: Net, re: Net, dataIn: Vector, dataOut: Vector):
        # make sure all registers can be addressed
        assert address.length >= ceil(log2(size))
        



            

            

