import logisim
from logisim import Vector,Net
from logisim.adder import ADDER
from logisim.mem import REG


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
ADDER(cnt,cnt,A)    # 8 full adder = 40 logic gates
ADDER(A,one,B)      # 40 logic gates
REG(B,clock,cnt,0)  # 8 DFF-pet = 48 NAND gates
# 128 logic gates total

# Initial values
one.set(1)

for t in range(500):
    # Create a 16 time units clock period to give enough time
    # for the combinational logic to settle
    clock.set( (t >> 3) & 1 )  
    logisim.simulateTimeUnit()


clock.VCDName("clk")
cnt.VCDName("counter")
logisim.generateVCD("adder.vcd")