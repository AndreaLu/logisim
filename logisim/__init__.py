__version__ = '1.1.3'
from .logisim import *
# Changelog:
# 1.1.3
# - now VCD can contain an unlimited number of signals
# - Cell type introduced. Now logic blocks classes can inherit from this
#   type to let the library automatic VCD variable scan also recursively
#   scan such instances to extract nets for export into VCD database
# 1.1.2
# - Major improvement on basic gates as they can now be istantiated
#   in multiple ways, even in parallel with a single istantiation
# - Implemented XNOR
# - Implemented arith.EQUALS using the new gates instantiation technique
# 1.1.1
# - Implemented RAM standard cell
# 1.1.0
# - Improved MUX and DEMUX to allow sel to be of type Net for 2-way muxes
# - Optimization fo MUX and DEMUX to save logic gates on sel decoding
# - reorganized library in the modules seq, comb, arith instead of exporing
#   everything from the core. This also allows module test procedures
#   to be run independently without circular imports
# 1.0.2
# - implemented MUX standard cell
# - implemented DEMUX standard cell
# 1.0.1
# - implemented oscillator standard cell (inverter ring oscillator with
#   customizable period)
# 1.0.0
# - first release

