from .logisim import NAND,Net,Vector,BUFF,NOT,AND,Gate,gates
from .comb import MUX
from math import log2,ceil

# ring oscillator
# Produces an output waveform oscillating between 0 and 1 with the given
# period. For odd half periods, it is built by a cascade of NOT gates.
# For even half period, a BUFF gate is added.
class OSCILLATOR:
    def __init__(self,halfPeriod:int,OUT:Net):
        
        # ring oscillators made by only inverters can only have an odd
        # number of stages. In case of even halfperiod we need to add a
        # a buffer at the beginning
        addBuffer = ((halfPeriod & 1) == 0)

        nets = []
        for i in range(halfPeriod-1):
            nets.append(Net())
        nets.append(OUT)

        l = len(nets)
        for i in range(l):
            if i == l-1 and addBuffer:
                nets[l-1-i].set( (i-1) & 1 )
                continue
            nets[l-1-i].set( (i) & 1  )


        for i in range(halfPeriod):
            if i == 0 and addBuffer:
                BUFF((nets[0],),nets[1] )
                continue
            NOT((nets[i],),nets[ (i+1) % halfPeriod ])

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

# Array of DFF. The size is the same as the input/output vectors
class REG:
    def __init__(self, D : Vector, clock: Net, Q:Vector, Vinit=0):
        self.length = D.length
        assert D.length == Q.length

        for i in range(self.length):
            DFF(D.nets[i],clock,Q.nets[i], (Vinit >> i) & 1 )

# Write Enable register
# when WE=0, the data is retained
# otherwise, D is stored on the positive clock edge
class WEREG:
    def __init__(self, D:Vector, Q: Vector, WE:Net, CLK: Net, Qinit=0):
        assert (wordLen:= D.length) == Q.length
        
        Dint = Vector(wordLen)
        REG(Dint,CLK,Q,Qinit)
        MUX((Q,D),Dint,WE)

# Register file
# upon a positive clock edge enabled by write enable, dataIn is registered
# at the given address. On a positive clock edge is enabled by read enable,
# the contents at the given address are copied into an output register that
# holds the value untill next read.
class REGFILE:
    def __init__(self, size:int, address:Vector, clock: Net, we: Net, re: Net, dataIn: Vector, dataOut: Vector):
        # make sure all registers can be addressed
        addressSize = ceil(log2(size))
        assert address.length >= addressSize
        wordLen = dataIn.length
        assert dataOut.length == wordLen
        

        C = Vector(wordLen)
        D = Vector(wordLen)
        RE = Vector(1)
        BUFF( (re,), RE.nets[0])
        A = []
        B = []

        for index in range(size):
            A.append( Vector(wordLen) )
            B.append( Vector(wordLen) )
            addrNets = [we] # list nof Nets to and to create the selector
            selector = Vector(1)
            for i in range(addressSize):
                if (index >> i) & 1 == 1:
                    addrNets.append( address.nets[i] )
                else:
                    newNet = Net()
                    NOT( (address.nets[i],),newNet)
                    addrNets.append( newNet )
            AND( addrNets, selector.nets[0] )
            MUX((B[-1],dataIn),A[-1],selector)
            REG(A[-1],clock,B[-1])

        MUX(B,C,address)
        MUX((dataOut,C),D, RE)
        REG(D,clock,dataOut)

# Similar to a register file, but much faster to simulate
# for big sizes
class RAM(Gate):
    def __init__(self, size:int, address:Vector, clock: Net, we: Net, re: Net, dataIn: Vector, dataOut: Vector):
        gates.append(self)
        self.we = we
        self.address = address
        self.ram = [0]*size
        self.clock = clock
        self.dataIn = dataIn
        assert (wordLen := dataIn.length) == wordLen
        D = Vector(wordLen)
        self.Dint = Vector(wordLen)

        REG( D=D, clock=clock, Q=dataOut )
        MUX(Inputs=(dataOut,self.Dint),Output=D,Sel=re)
    
    def Eval(self):
        self.Dint.set(
            self.ram[self.address.get()]
        )
        if self.clock.value[-2] == 1 and self.clock.value[-3] == 0 and self.we.value[-2] == 1:
            self.ram[self.address.get()] = self.dataIn.get()
    
    def loadFile(self,fname:str):
        self.loadBytes( open(fname,"rb").read() )
    
    def loadBytes(self,data:bytes):
        data = list(data)
        i = 0
        j = 0
        while( len(data)-j >= 4 ):
            self.ram[i] = int(data[j]) + (int(data[j+1]) << 8) + (int(data[j+2]) << 16) + (int(data[j+3]) << 24)
            j += 4
            i += 1

def pulse(t,min,max):
    return 1 if t >= min and t <= max else 0

if __name__ == "__main__":
    from .logisim import simulateTimeUnit, writeVCD
    # Test the ram
    clk = Net()
    address = Vector(16)
    we = Net()
    re = Net()
    din = Vector(8)
    do = Vector(8)


    OSCILLATOR(10,clk)
    ram = RAM(65536,address,clk,we,re,din,do)

    address.set(10)
    din.set(18)

    for t in range(1000):
        address.set(   10*pulse(t,0,100) + 32*pulse(t,101,200) + 84*pulse(t,201,300) + 10*pulse(t,400,500) )
        we.set( pulse(t,45,60)  +  pulse(t,145,160)  + pulse(t, 245,260) )
        re.set( pulse(t,345,360) + pulse(t,445,460) )
        simulateTimeUnit(1)
    
    writeVCD("ram.vcd")





            

