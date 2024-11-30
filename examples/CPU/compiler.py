# Converts an assembly file to a machine code file ready to be loaded
# in the CPU instruction memory 

import re
from CPUDefs import *

msgErrorHeader = ""
# this variable is updated for each line analyzed by the compile routine
# and is set to a useful error message string with the line number and 
# contents for reference.
def error(msg):
    raise Exception(f"{msgErrorHeader}{msg}")

class ASM_TOKEN(AutoEnum):
    REG = auto()
    IM = auto() # IMMEDIATE
    RP = auto() # register pointer
    IP = auto() # immediate pointer
    LBL = auto() # label

class asmToken(str):
    def parse(self):
        global labels
        if re.fullmatch("\\$[a-d]",str(self.lower())):
            return (ASM_TOKEN.REG,self.lower()[1])
        elif re.fullmatch("#[a-d]",self.lower()):
            return (ASM_TOKEN.RP,str(self.lower()[1]))
        elif re.fullmatch("[0-9]+",self):
            immediate = int(str(self))
            if immediate >= 2**16:
                error(f"Invalid immediate {immediate} does not fit 16bits")
            return (ASM_TOKEN.IM, immediate)
        elif re.fullmatch("#[0-9]+",self):
            immediate = int(str(self)[1:])
            if immediate >= 2**16:
                error(f"Invalid immediate {immediate} does not fit 16bits")
            return (ASM_TOKEN.IP,immediate)
        elif str(self) in labels:
            return (ASM_TOKEN.LBL,labels[str(self)])
        error(f"Invalid token '{str(self)}'")


labels = {} 
class Line:
    fields : list[str]
    originalLineNo : int
    label : str
    address : int
    originalLine : str
    
    def __init__(self):
        self.label = ""
        self.address = 0

    def isLabel(self):
        return  len(self.fields) == 1 and \
            re.fullmatch("[A-Z_][A-Z0-9_]+:",self.fields[0])
    

def compile(srcCode:str) -> bytes:
    global msgErrorHeader, labels

    out = []
    currInstructionNo = 0

    def parseMOV(args : list[str]) -> bytes:
        args = args[1:]
        immediate = None

        # Parse DST -----------------------------------------------------------
        if len(args) == 0: raise Exception("MOV instruction without DST")
        DST = args[0].lower()
        accepted = ("\\$a","\\$b","\\$c","\\$d","#a","#b","#c","#d","#[0-9]+")
        found = False
        for pattern in accepted:
            if re.fullmatch(pattern,DST):
                found = True
                break
        if not found: raise Exception(f"MOV DST operand invalid! '{DST}'")
        if re.fullmatch("#[0-9]+",DST):
            immediate = int(DST[1:])
            if immediate >= 65536:
                raise Exception(f"Immediate {immediate} does not fit in 16bit words!")
        

        # Parse SRC -----------------------------------------------------------
        args = args[1:]
        if len(args) == 0: raise Exception("MOV instruction without SRC")
        SRC = args[0].lower()
        accepted = ("\\$a","\\$b","\\$c","\\$d","#a","#b","#c","#d","#[0-9]+","[0-9]+")
        found = False
        for pattern in accepted:
            if re.fullmatch(pattern,SRC):
                found = True
                break
        if SRC in ("#a","#b","#c","#d"):
            REGDST = ('a','b','c','d').index(SRC[1])
        elif DST in ("#a","#b","#c","#d"):
            REGDST = ('a','b','c','d').index(DST[1])
        else:
            REGDST = 0
        if not found: raise Exception(f"MOV SRC operand invalid! '{SRC}'")
        if re.fullmatch("#[0-9]+",SRC):
            if immediate is not None:
                raise Exception(f"Cannot have both SRC and DST immediate in MOV instruction")
            immediate = int(SRC[1:])
            if immediate >= 65536:
                raise Exception(f"Immediate {immediate} does not fit in 16bit words!")
        elif re.fullmatch("[0-9]+",SRC):
            if immediate is not None:
                raise Exception(f"Cannot have both SRC and DST immediate in MOV instruction")
            immediate = int(SRC)

        
                
        instruction = OPCODE.MOV
        if DST[0] == "$":
            instruction += (MOVOP.A,MOVOP.B,MOVOP.C,MOVOP.D)[('a','b','c','d').index(DST[1])] << 8
        elif DST in ("#a","#b","#c","#d"):
            instruction += MOVOP.REG2MEM << 8
        elif re.fullmatch("#[0-9]+",DST):
            instruction += MOVOP.IM2MEM << 8

        
        if SRC[0] == "$":
            instruction += (MOVOP.A,MOVOP.B,MOVOP.C,MOVOP.D)[('a','b','c','d').index(SRC[1])] << 11
        elif SRC in ("#a","#b","#c","#d"):
            instruction += MOVOP.REG2MEM << 11
        elif re.fullmatch("#[0-9]+",DST):
            instruction += MOVOP.IM2MEM << 11
        elif re.fullmatch("[0-9]+",SRC):
            instruction += MOVOP.IM << 11
        
        if immediate is not None:
            instruction += immediate << 14

        instruction += REGDST << 30
        return instruction
    def parseJMP(args : list[str]) -> bytes:
        # All jump instructions have only one argument
        if len(args) != 2:
            error("Instruction malformed")

        opcode = args[0]
        map = {"JMP":JMPCND.UNC,"JEQ":JMPCND.EQ,
        "JNE":JMPCND.NEQ,"JLW":JMPCND.LOW,
        "JGR":JMPCND.GRE,"JLE":JMPCND.LEQ,"JGE":JMPCND.GEQ}
        if opcode not in map:
            error(f"invalid opcode {opcode}")

        label = asmToken(args[1]).parse()
        if label[0] not in (ASM_TOKEN.LBL,ASM_TOKEN.IM,ASM_TOKEN.REG):
            error(f"Jump operand must be a label, register or immediate")
        if label[0] in (ASM_TOKEN.LBL,ASM_TOKEN.IM):
            immediate = label[1]
            reg = 4
        else:
            immediate = 0
            reg = {"a":0,"b":1,"c":2,"d":3}[label[1]]

        
        return OPCODE.JMP | (map[opcode] << 8) | (reg << 11) | (immediate << 14)
    def parseALU(args : list[str]) -> bytes:
        immediate = 0

        if args[0] in ("ADD","SUB","MUL","DIV","CMP"):
            opcode = {
                "ADD":OPCODE.ADD,
                "SUB":OPCODE.SUB,
                "MUL":OPCODE.MUL,
                "DIV":OPCODE.DIV,
                "CMP":OPCODE.CMP
            }[args[0]]
            # Parse A -----------------------------------------------------
            A = asmToken(args[1]).parse()
            if A[0] not in (ASM_TOKEN.IM,ASM_TOKEN.REG):
                error(f"Invalid operand A in ADD: '{args[1]}', " \
                    "must be either Immediate or Register!")
        
            if A[0] == ASM_TOKEN.REG:
                opa = (ADDOP.A,ADDOP.B,ADDOP.C,ADDOP.D)["abcd".index(A[1])]
            else:
                opa = ADDOP.IM
                immediate = A[1]
            
            # Parse B ---------------------------------------------------------
            B = asmToken(args[2]).parse()
            if B[0] not in (ASM_TOKEN.IM,ASM_TOKEN.REG):
                error(f"Invalid operand B in ADD: '{args[2]}', " \
                    "must be either Immediate or Register!")
            if B[0] == ASM_TOKEN.IM and A[0] == ASM_TOKEN.IM:
                error(f"Both operands in ADD instruction cannot be immediate!")
            
            if B[0] == ASM_TOKEN.REG:
                opb = (ADDOP.A,ADDOP.B,ADDOP.C,ADDOP.D)["abcd".index(B[1])]
            else:
                opb = ADDOP.IM
                immediate = B[1]
            if opcode != OPCODE.CMP:
                # Parse DST -----------------------------------------------
                DST = asmToken(args[3]).parse()
                if DST[0] != ASM_TOKEN.REG:
                    error(f"Invalid DST '{args[3]}' in ADD operation: DST must be a register!")
                dst = (MOVOP.A,MOVOP.B,MOVOP.C,MOVOP.D)["abcd".index(DST[1])]

                # Generate instruction
                return opcode | (opa << 8) | (opb << 11) | (immediate << 14) | (dst << 30)
            else:
                return opcode | (opa << 8) | (opb << 11) | (immediate << 14)
    def cleanupLine(line:str):
        # Some adaptation
        # remove comments and multiple whitespaces
        # split the string into a string field array
        if ';' in line: line = line.split(";")[0]
        line = line.replace("\t"," ").replace("\r","").replace("\n","")
        while "  " in line: line = line.replace("  "," ")
        while line.startswith(" "): line = line[1:]
        while line.endswith(" "): line = line[:-1]
        return line
        

    
    # lines : list[fields,originalLineNum,label,address,islabel]
    # fields are just the components of the instruction line 
    lines : list[ Line ]  = []
    # map labelName -> instruction address
    

    # ---------------------------------------------------------------------
    # STEP 1: cleanup the source code and populate lines
    lineNo = 0
    for line in srcCode.split("\n"):
        lineNo += 1
        cleanLine = cleanupLine(line)
        if len(cleanLine) == 0: continue
        fields = [l.upper() for l in cleanLine.split(" ")]
        if len(fields) == 0: continue
        newLine = Line()
        newLine.fields = fields
        newLine.originalLineNo = lineNo
        newLine.originalLine = line
        lines.append( newLine )
    
    # always add a final NOP
    newLine = Line()
    newLine.fields = ["NOP"]
    lines.append( newLine )

    # ---------------------------------------------------------------------
    # STEP 2: configure label and address of all the code lines
    # (a code line next a label inherits the label)
    # and remove the label lines from the listing
    i = -1
    while i < len(lines)-1:
        i += 1
        l : Line = lines[i]
        # check if this line is a label
        if l.isLabel():
            if lines[i+1].isLabel():
                raise Exception(f"Cannot have two subsequent labels (line {l.originalLineNo})")
            # set next instruction label and address
            label = l.fields[0][:-1]
            if label in labels:
                raise Exception(f"Label '{label}' already defined (line {l.originalLineNo})")
            lines[i+1].label = label # TODO: this parameter could be removed
            lines[i+1].address = 0 if i == 0 else lines[i-1].address + 1
            add = lines[i+1].address
            lines = lines[:i] + lines[i+1:]
            labels[label] = add
            i -= 1
            continue
        else:
            # this line is not a label, just set the address
            if i == 0: l.address = 0
            else: l.address = lines[i-1].address + 1

    
    # Remove the last line (NOP)
    lines = lines[:-1]

    # ---------------------------------------------------------------------
    # STEP 3: actually parse the instructions
    for line in lines:
        msgErrorHeader = f"Error at line number {line.originalLineNo},"\
            f"'{line.originalLine}':\n"

        opcode = line.fields[0]
        if opcode == "MOV":
            instruction = parseMOV(line.fields)
        elif opcode[0] == "J":
            # Jumps need to be analyzed at the
            instruction = parseJMP(line.fields)
        elif opcode in ("ADD","SUB","MUL","DIV","CMP"):
            instruction = parseALU(line.fields)
        else:   
            error(f"Unrecognized opcode '{opcode}'")

        out += bytes([
            (instruction) & 0xFF, (instruction >> 8) & 0xFF, (instruction >> 16) & 0xFF, (instruction >> 24) & 0xFF 
        ])
    return bytes(out)

if __name__ == "__main__":
    import sys, os
    a = asmToken("$c").parse()

    # Input argument checks
    if len( sys.argv ) < 3:
        print(f"Error. Program usage: compiler srcFname dstFname")
        exit(1)
    if not os.path.isfile( srcFname := sys.argv[1] ):
        print(f"The specified file '{srcFname}' does not exist!")
        exit(1)
    if os.path.exists( outFname := sys.argv[2] ):
        print(f"The specified output '{outFname}' already exists!")
        exit(1)
    if len(outdir := os.path.dirname(outFname)) > 0 and not os.path.isdir( outdir ):
        print(f"Output directory '{outdir}' does not exist!")
        exit(1)

    # Compile the source code
    data = compile( open(srcFname,"r").read() )
    open(outFname,"wb").write( data )
    