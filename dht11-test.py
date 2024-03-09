#!/usr/bin/python
import sys
from time import sleep
import board
import adafruit_dht

# DHT11 Sensor data pin is connected to GPIO 17
dht11 = adafruit_dht.DHT11(board.D17)

while True:
    try:
        # Print the values to the serial port
        temperature_c = dht11.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dht11.humidity
        print("Temp={0:0.1f}ºC, Temp={1:0.1f}ºF, Humidity={2:0.1f}%".format(temperature_c, temperature_f, humidity))

    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        print(error.args[0])
        sleep(2.0)
        continue
    except Exception as error:
        dht11.exit()
        raise error

    sleep(1)
