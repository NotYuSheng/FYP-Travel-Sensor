import sys, time, os
from lib.mq2 import *
from lib.mq135 import *

#try:
mq2 = MQ2();
mq135 = MQ135();
print("Press CTRL+C to abort.")

while True:
    percMQ2 = mq2.MQPercentage()
    percMQ135 = mq135.MQPercentage()

    lpgPPM = round(percMQ2["LPG"], 2)
    coPPM = round(percMQ2["CO"], 2)
    smokePPM = round(percMQ2["SMOKE"], 2)
    propanePPM = round(percMQ2["PROPANE"], 2)
    h2PPM = round(percMQ2["H2"], 2) # Hydrogen
    alcoholPPM = round(percMQ2["ALCOHOL"], 2)
    ch4PPM = round(percMQ2["CH4"], 2) # Methane

    acetonPPM = round(percMQ135["ACETON"], 2)
    toluenoPPM = round(percMQ135["TOLUENO"], 2)
    alcoholPPM = round(percMQ135["ALCOHOL"], 2)
    co2PPM = round(percMQ135["CO2"], 2)
    nh4PPM = round(percMQ135["NH4"], 2)
    coPPM = round(percMQ135["CO"], 2)
    
    os.system("clear")
    print("----------MQ2----------")
    print("LPG: %g ppm, CO: %g ppm, Smoke %g ppm, Propane %g ppm, H2 %g ppm, Alcohol: %g ppm, CH4: %g ppm" % (lpgPPM, coPPM, smokePPM, propanePPM, h2PPM, alcoholPPM, ch4PPM))
    print(f"rs_ro_ratio: {round(percMQ2['rs_ro_ratio'], 2)}")
    
    print("---------MQ135---------")
    print("ACETON: %g ppm, TOLUENO: %g ppm, ALCOHOL: %g ppm, CO2: %g ppm, NH4: %g ppm, CO: %g ppm" % (acetonPPM, toluenoPPM, alcoholPPM, co2PPM, nh4PPM, coPPM))
    
    time.sleep(0.1)
"""
except Exception as e:
    print(e)
    print("\nAbort by user")
"""
