gates = []   # All existing logic gates
nets = []    # All existing nets
vectors = [] # All existing vectors


class Net:
    def __init__(self):
        nets.append(self)
        self.value = [0]
        self.name = ""
        self.isVector = False
        self.id = None
        self.event = False
        self.alreadySet = False
        
    def set(self,val):
        assert self.alreadySet == False
        self.value[-1] = val
        if len(self.value) == 1: self.event = False
        elif val != self.value[-2]:
            self.event = True

    def get(self):
        return self.value[-2]
        
    def advanceTime(self):
        self.alreadySet = False
        self.value.append(self.value[-1])

    def markForVCD(self,name):
        self.name = name

# Collection of nets
class Vector:
    def __init__(self,length):
        assert length > 0
        self.nets = []
        self.length = length
        for i in range(length):
            newnet = Net()
            newnet.isVector = True
            self.nets.append(newnet)
        vectors.append(self)
        self.name = ""
        self.id = None

    def set(self,word):
        for j in range(self.length):
            self.nets[j].set( (word >> j) & 1 )
    
    def get(self):
        word = 0
        for j in range(self.length):
            word += self.nets[j].get() << j
        return word


    def valueAtBinary(self,t):
        word = "b" 
        for j in range(self.length):
            word += str(self.nets[self.length-j-1].value[t])
        return word

    def markForVCD(self,name):
        self.name = name



# Definition of all the basic logic gates
# all logic gates can have a variable number of inputs and one output
# with the exception of NOT gate, which has only one input and one output
# Possibilities:
# case0 inputs: collection(Vector(N)), outputs: Vector(N)
# case1 inputs: collection(Net), output: Net
# case2 inputs: Vector(N), output: Net
class Gate:
    def __init__(self, inputs : tuple[Net|Vector]|Vector, output : Net|Vector):
        

        if type(inputs) is list or type(inputs) is tuple:
            # at least one input
            assert len(inputs) > 0 
            # all inputs of the same type
            for input in inputs:
                assert type(inputs[0]) == type(input)
            assert type(output) == type(inputs[0])

            if type(inputs[0]) is Vector:
                # case 0) collection(vector), vector
                assert type(output) is Vector
                wordLen = output.length
                for input in inputs:
                    assert input.length == wordLen
                for i in range(wordLen):
                    type(self)([input.nets[i] for input in inputs],output.nets[i])
                return
            else:
                # case 1) collection(net),net
                pass
            
        else:
            # case 3) Vector,net
            assert type(output) is Net
            assert type(inputs) is Vector
            inputs = inputs.nets
            # get back to case 1) collection(net),net

        
        # case 1) collection(net),net
        self.inputs = inputs
        self.output = output
        gates.append(self)
        return output

class AND(Gate):
    def Eval(self):
        self.output.set(0 if 0 in [input.get() for input in self.inputs] else 1)
class OR(Gate):
    def Eval(self):
        self.output.set(1 if 1 in [input.get() for input in self.inputs] else 0)
class NOT(Gate):
    def Eval(self):
        self.output.set(1 - self.inputs[0].get())
class NAND(Gate):
    def Eval(self):
        self.output.set(1 if 0 in [input.get() for input in self.inputs] else 0)
class NOR(OR):
    def Eval(self):
        self.output.set(0 if 1 in [input.get() for input in self.inputs] else 1)

class XOR(Gate):
    def Eval(self):
        self.output.set(1 if sum([input.get() for input in self.inputs]) == 1 else 0)
class XNOR(Gate):
    def Eval(self):
        self.output.set(0 if sum([input.get() for input in self.inputs]) == 1 else 1)
class BUFF(Gate):
    def Eval(self):
        self.output.set(self.inputs[0].get())

# Basic type used to mark a class as suitable for automatic detection
# for the generation of the VCD database
class Cell:
    def __init__(self):
        pass

def simulateTimeUnit(units=1):
    for i in range(units):
        for net in nets:
            net.advanceTime()
        for gate in gates:
            gate.Eval()


GND = Net()
VDD = Net()
GND.set(0)
VDD.set(1)


# Generate the VCD file with the nets/vectors that have been marked for VCD
def writeVCD(fname):
    import inspect  # needed to automatically assign a name to nets
                    # using their respective variable names
    ids = []

    def generateNewID():
        alphabet = "abcdefghijklmnopqrstuvwxyz"

        if generateNewID.lastID == "":
            generateNewID.lastID = alphabet[0]
            return alphabet[0]
        
        
        lid = generateNewID.lastID
        if lid[-1] == alphabet[-1]:
            lid += alphabet[0]
            generateNewID.lastID = lid
            return lid
        
        lid = lid[:-1] + alphabet[ alphabet.index(lid[-1])+1 ]
        generateNewID.lastID = lid
        return lid
    generateNewID.lastID = ""
    

    retv = "$timescale 1ns $end\n"
    retv += "$scope module logic $end\n"


    netsUpdate = [] 
    vectorsUpdate = []
    
    frame = inspect.currentframe().f_back
    
    def scanVarList(varList,prefix=""):
        for var_name,var_val in varList:
            if isinstance( var_val, Cell ):
                _dict = {key: value for key, value in vars(var_val).items() if not callable(value)}
                scanVarList( [ (key,_dict[key]) for key in _dict.keys()], prefix=(var_name + "."))
            else:
                if type(var_val) is list or type(var_val) is tuple:
                    allNets = True
                    for child in var_val:
                        if type(child) not in (Vector,Net):
                            allNets = False
                            break
                    if allNets:
                        i = -1
                        for child in var_val:
                            i += 1
                            child.markForVCD(f"{prefix}{var_name}.net[{i}]")
                if type(var_val) in (Net,Vector):
                    var_val.markForVCD(f"{prefix}{var_name}")
    
    # scan all the local variables where writeVCD is called and mark
    # for inertion in the VCD all variables of time Net or Vector
    # Recursively enter instances inheriting from Cell type
    scanVarList(frame.f_locals.items())


    # Generate the VCD IDs for the nets/vectors with a name
    for net in nets:
        if net.name == "": continue
        if net.isVector: continue
        net.id = generateNewID()
        if net.id is None:
            raise Exception("too many signals!")
        retv += f"$var wire 1 {net.id} {net.name} $end\n"
    for vector in vectors:
        if vector.name == "": continue
        vector.id = generateNewID()
        if vector.id is None: raise Exception("too many signals!")
        retv += f"$var wire {vector.length} {vector.id} {vector.name} $end\n"
    retv += "$enddefinitions $end\n"



    for t in range(len(nets[0].value)):
        netsUpdate.clear()
        vectorsUpdate.clear()
        # populate netsUpdate and vectorsUpdate with all the nets and vectors
        # that did change value on this time unit
        if t == 0:
            for net in nets:
                if net.id is not None: netsUpdate.append(net)
            for vector in vectors:
                if vector.id is not None: vectorsUpdate.append(vector)
        else:
            for net in nets:
                if net.value[t] != net.value[t-1]:
                    netsUpdate.append(net)
            for vector in vectors:
                for net in vector.nets:
                    if net.value[t-1] != net.value[t]:
                        vectorsUpdate.append(vector)
                        break
        
        # add to the VCD file only the nets that were updated
        if len(netsUpdate) + len(vectorsUpdate) > 0:
            retv += f"#{t}\n"
            for net in netsUpdate:
                if net.id is None: continue
                retv += f"{net.value[t]}{net.id}\n"
            for vector in vectorsUpdate:
                if vector.id is None: continue
                retv += f"{vector.valueAtBinary(t)} {vector.id}\n"

    with open(fname,"w") as f:    
        f.write(retv)
    print(f"Generated database file '{fname}'.\nOpen it up with a VCD viewer to browse the waveforms!")


