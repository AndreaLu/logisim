gates = [] # Elenco delle porte esistenti
nets = [] # Elenco dei nodi esistenti
vectors = []


class Net:
    def __init__(self):
        nets.append(self)
        self.value = [0]
        self.updated = [False]
        self.name = ""
        self.isVector = False
        self.id = None
        
    def set(self,val):
        global netsUpdated
        self.updated[-1] = True
        self.value[-1] = val
    def get(self):
        return self.value[-2]
        
    def advanceTime(self):
        self.value.append(self.value[-1])
        self.updated.append(False)

    def VCDName(self,name):
        self.name = name

# Collection of nets
class Vector:
    def __init__(self,length):
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


    def valueAtBinary(self,t):
        word = "b" 
        for j in range(self.length):
            word += str(self.nets[self.length-j-1].value[t])
        return word

    def VCDName(self,name):
        self.name = name



# Definition of all the basic logic gates
# all logic gates can have a variable number of inputs and one output
# with the exception of NOT gate, which has only one input and one output
class Gate:
    def __init__(self, inputs : tuple[Net], output : Net):
        self.inputs = inputs
        self.output = output
        gates.append(self)


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

def simulateTimeUnit():
    for net in nets:
        net.advanceTime()
    for gate in gates:
        gate.Eval()


GND = Net()
VDD = Net()
GND.set(0)
VDD.set(1)


# Genera il file VCD per guardare le forme d'onda con un programma esterno
def generateVCD(fname):
    
    ids = []
    def getID():
        id = ""
        for c in "abcdefghijklmnopqrstuvwxyz":
            if id + c not in ids:
                ids.append(id+c)
                return id + c
        return None

    retv = "$timescale 1ns $end\n"
    retv += "$scope module logic $end\n"


    netsUpdate = [] # lista dei nodi / vettori che cambiano
    vectorsUpdate = []
    
    # Esporta tutti i nodi con un nonme assegnato in un file VCD
    for net in nets:
        if net.name == "": continue
        if net.isVector: continue
        net.id = getID()
        if net.id is None:
            raise Exception("too many signals!")
        retv += f"$var wire 1 {net.id} {net.name} $end\n"
    for vector in vectors:
        if vector.name == "": continue
        vector.id = getID()
        if vector.id is None: raise Exception("too many signals!")
        retv += f"$var wire {vector.length} {vector.id} {vector.name} $end\n"
    retv += "$enddefinitions $end\n"



    for t in range(len(nets[0].value)):
        netsUpdate.clear()
        vectorsUpdate.clear()
        # Trova tutti i nodi cambiati
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


