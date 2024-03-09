from mq2 import *
from mq135 import *
import sys, time

try:
    print("Press CTRL+C to abort.")
    
    mq2 = MQ2();
    mq135 = MQ135();
    while True:
        mq2_perc = mq2.MQPercentage()
        mq135_perc = mq135.MQPercentage()
        sys.stdout.write("\r")
        sys.stdout.write("\033[K")
        
        sys.stdout.write("------MQ2-----\n")
        sys.stdout.write("LPG: %g ppm, CO: %g ppm, Smoke: %g ppm\n" % (mq2_perc["GAS_LPG"], mq2_perc["CO"], mq2_perc["SMOKE"]))
        sys.stdout.write("PROPANE: %g ppm, H2: %g ppm, ALCOHOL: %g ppm\n" % (mq2_perc["PROPANE"], mq2_perc["H2"], mq2_perc["ALCOHOL"]))
        sys.stdout.write("CH4: %g ppm\n" % (mq2_perc["CH4"]))
        
        sys.stdout.write("------MQ135-----\n")
        sys.stdout.write("ACETON: %g ppm, TOLUENO: %g ppm, ALCOHOL: %g ppm\n" % (mq135_perc["ACETON"], mq135_perc["TOLUENO"], mq135_perc["ALCOHOL"]))
        sys.stdout.write("CO2: %g ppm, NH4: %g ppm, CO: %g ppm\n" % (mq135_perc["CO2"], mq135_perc["NH4"], mq135_perc["CO"]))
        sys.stdout.flush()
        time.sleep(0.1)

except Exception as e:
    print(e)
    print("\nAbort by user")
