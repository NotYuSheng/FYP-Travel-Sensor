# This script is used to test each individual pins of the MCP3008 with the RPI for analog read
# The script is derived but modified with reference to:
# https://randomnerdtutorials.com/raspberry-pi-analog-inputs-python-mcp3008/

from gpiozero import MCP3008
from time import sleep

#create an object called pot that refers to MCP3008 channel 0
pot0 = MCP3008(0)
pot1 = MCP3008(1)
pot2 = MCP3008(2)
pot3 = MCP3008(3)
pot4 = MCP3008(4)
pot5 = MCP3008(5)
pot6 = MCP3008(6)
pot7 = MCP3008(7)

while True:
    print("\r")
    print(f'pot0: {round(pot0.value, 3)}')
    print(f'pot1: {round(pot1.value, 3)}')
    print(f'pot2: {round(pot2.value, 3)}')
    print(f'pot3: {round(pot3.value, 3)}')
    print(f'pot4: {round(pot4.value, 3)}')
    print(f'pot5: {round(pot5.value, 3)}')
    print(f'pot6: {round(pot6.value, 3)}')
    print(f'pot7: {round(pot7.value, 3)}')
    sleep(0.1)
