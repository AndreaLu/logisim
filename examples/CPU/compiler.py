# Converts an assembly file to a machine code file ready to be loaded
# in the CPU instruction memory 

import re
from CPUDefs import *



def compile(srcCode:str) -> bytes:

    lineNo = 0
    out = []
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
        #instruction = OPCODE.MOV  |  (MOVOP.IM2MEM << 8) |  (MOVOP.C << 11) | (100 << 14) | (MOVOP.C << 30)
        return bytes([
            (instruction) & 0xFF, (instruction >> 8) & 0xFF, (instruction >> 16) & 0xFF, (instruction >> 24) & 0xFF 
        ])
    def parseJMP(args : list[str]) -> bytes:
        pass
    def parseALU(args : list[str]) -> bytes:
        pass


    for line in srcCode.split("\n"):
        
        # -----------------------------------------------------------------
        # Some adaptation
        # remove comments and multiple whitespaces
        # split the string into a string field array
        originalLine = line
        lineNo += 1
        if ';' in line: line = line.split(";")[0]
        line : str = line.replace("\t"," ").replace("\r","").replace("\n","")
        while "  " in line: line = line.replace("  "," ")
        while line.startswith(" "): line = line[1:]
        while line.endswith(" "): line = line[:-1]
        if len(line) == 0: continue
        fields = line.split(" ")
        if len(fields) < 1:
            continue

        # -----------------------------------------------------------------
        # Parse the fields to generate the instructions
        print(f"parsing {fields}")
        opcode = fields[0].upper()
        
        if opcode == "MOV":
            instruction = parseMOV(fields)
        elif opcode in ("JE","JNE","JGR","JLO"):
            instruction = parseJMP(fields)
        elif opcode == ("ADD","SUB","CMP"):
            instruction = parseALU(fields)
        else:   
            raise Exception(f"Unrecognized opcode '{opcode}' in line {lineNo}:'{originalLine}'")

        out += instruction
        
    return bytes(out)

if __name__ == "__main__":
    import sys, os

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
    open(outFname,"wb").write( compile( open(srcFname,"r").read() ) )
    