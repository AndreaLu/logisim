
from .logisim import Net,NOT,BUFF

# ring oscillator
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


    


