from logisim import Vector,Net,simulateTimeUnit,writeVCD
from logisim.arith import ADDER
from logisim.seq import OSCILLATOR,REG


# example circuit, cnt <= cnt*2 + 1
#   _________________________________
#  /       __                        \
# |   --->|  \                       |
# |  |     \  \  A   __              |
# \__|      |  |--->|  \             |
#    |     /  /      \  \  B  ____   |
#     --->|__/        |  |-->|D  Q|__/
#                    /  /    |    |
#             1 --->|__/  -->|>   |
#                         |  |____|
#                        clk
#

# Define the circuit nodes
A       = Vector(8) # net A in the picture
B       = Vector(8) # net B in the picture
cnt     = Vector(8) # register output in the picture
one     = Vector(8) # constant, value 1
clock   = Net()

# Define the circuit cells
ADDER(cnt,cnt,A)     # 8 full adder = 40 logic gates
ADDER(A,one,B)       # 40 logic gates
OSCILLATOR(7,clock)  # 7 logic gates ring oscillator
REG(B,clock,cnt,0)   # 8 DFF-pet = 48 NAND gates
# 135 logic gates total

# Initial values
one.set(1)

# Simulate for 500 steps
simulateTimeUnit(500)

writeVCD("counter.vcd")