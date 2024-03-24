# Library Origin:    https://github.com/tutRPi/Raspberry-Pi-Gas-Sensor-MQ/blob/master/mq.py
# Graph values from: https://github.com/farmaker47/Raspberry-to-assess-food-quality/blob/main/code/mq135.py

import time
import math
from lib.MCP3008 import MCP3008

class MQ135():

    ######################### Hardware Related Macros #########################
    MQ_PIN                       = 1        # define which analog input channel you are going to use (MCP3008)
    RL_VALUE                     = 5        # define the load resistance on the board, in kilo ohms
    RO_CLEAN_AIR_FACTOR          = 9.83     # RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO,
                                            # which is derived from the chart in datasheet
 
    ######################### Software Related Macros #########################
    CALIBARAION_SAMPLE_TIMES     = 50       # define how many samples you are going to take in the calibration phase
    CALIBRATION_SAMPLE_INTERVAL  = 500      # define the time interval(in milisecond) between each samples in the
                                            # cablibration phase
    READ_SAMPLE_INTERVAL         = 50       # define the time interval(in milisecond) between each samples in
    READ_SAMPLE_TIMES            = 5        # define how many samples you are going to take in normal operation 
                                            # normal operation
 
    ######################### Application Related Macros ######################
    GAS_ACETON                   = 0
    GAS_TOLUENO                  = 1
    GAS_ALCOHOL                  = 2
    GAS_CO2                      = 3
    GAS_NH4                      = 4
    GAS_CO                       = 5

    def __init__(self, Ro=10, analogPin=0):
        self.Ro = Ro        
        self.MQ_PIN = analogPin
        self.adc = MCP3008()
        
        self.ACETONCurve = [1.0,0.18,-0.32] # two points are taken from the curve. 
                                            # with these two points, a line is formed which is "approximately equivalent"
                                            # to the original curve. 
                                            # data format:{ x, y, slope}; point1: (lg10, 0.18), point2: (lg200, -0.24) 
        self.TOLUENOCurve = [1.0,0.2,-0.30] # two points are taken from the curve. 
                                            # with these two points, a line is formed which is "approximately equivalent" 
                                            # to the original curve.
                                            # data format:[ x, y, slope]; point1: (lg10, 0.2), point2: (lg200, -0.19)
        self.AlcoholCurve =[1.0,0.28,-0.32] # two points are taken from the curve. 
                                            # with these two points, a line is formed which is "approximately equivalent" 
                                            # to the original curve.
                                            # data format:[ x, y, slope]; point1: (lg10, 0.28), point2: (lg200, -0.14)
        self.CO2Curve =[1.0,0.38,-0.37]       # two points are taken from the curve. 
                                            # with these two points, a line is formed which is "approximately equivalent" 
                                            # to the original curve.
                                            # data format:[ x, y, slope]; point1: (lg10, 0.38), point2: (lg200, -0.10)
        self.NH4Curve =[1.0,0.42,-0.42]     # two points are taken from the curve. 
                                            # with these two points, a line is formed which is "approximately equivalent" 
                                            # to the original curve.
                                            # data format:[ x, y, slope]; point1: (lg10, 0.42), point2: (lg200, -0.12)
        self.COCurve =[1.0,0.45,-0.26]     # two points are taken from the curve. 
                                            # with these two points, a line is formed which is "approximately equivalent" 
                                            # to the original curve.
                                            # data format:[ x, y, slope]; point1: (lg10, 0.45), point2: (lg200,  0.11)
                
        print("Calibrating MQ-135...")
        self.Ro = self.MQCalibration(self.MQ_PIN)
        print("Calibration of MQ-135 is done...")
        print("MQ-135 Ro=%f kohm" % self.Ro)
        print("\n")
    
    def MQPercentage(self):
        val = {}
        read = self.MQRead(self.MQ_PIN)
        val["rs_ro_ratio"] = read/self.Ro
        val["ACETON"]   = self.MQGetGasPercentage(read/self.Ro, self.GAS_ACETON)
        val["TOLUENO"]  = self.MQGetGasPercentage(read/self.Ro, self.GAS_TOLUENO)
        val["ALCOHOL"]  = self.MQGetGasPercentage(read/self.Ro, self.GAS_ALCOHOL)
        val["CO2"]      = self.MQGetGasPercentage(read/self.Ro, self.GAS_CO2)
        val["NH4"]      = self.MQGetGasPercentage(read/self.Ro, self.GAS_NH4)
        val["CO"]       = self.MQGetGasPercentage(read/self.Ro, self.GAS_CO)
        return val
        
    ######################### MQResistanceCalculation #########################
    # Input:   raw_adc - raw value read from adc, which represents the voltage
    # Output:  the calculated sensor resistance
    # Remarks: The sensor and the load resistor forms a voltage divider. Given the voltage
    #          across the load resistor and its resistance, the resistance of the sensor
    #          could be derived.
    ############################################################################ 
    def MQResistanceCalculation(self, raw_adc):
        count = 0
        while (float(raw_adc) == 0 and count < 3):
            print("MQ135 wire loose...")
            time.sleep(1)
            count += 1
        if (count == 3):
            print("MQ135 wire loose timeout, try again later...")
            return 0.1;
        return float(self.RL_VALUE*(1023.0-raw_adc)/float(raw_adc));
     
     
    ######################### MQCalibration ####################################
    # Input:   mq_pin - analog channel
    # Output:  Ro of the sensor
    # Remarks: This function assumes that the sensor is in clean air. It use  
    #          MQResistanceCalculation to calculates the sensor resistance in clean air 
    #          and then divides it with RO_CLEAN_AIR_FACTOR. RO_CLEAN_AIR_FACTOR is about 
    #          10, which differs slightly between different sensors.
    ############################################################################ 
    def MQCalibration(self, mq_pin):
        val = 0.0
        for i in range(self.CALIBARAION_SAMPLE_TIMES):          # take multiple samples
            val += self.MQResistanceCalculation(self.adc.read(mq_pin))
            time.sleep(self.CALIBRATION_SAMPLE_INTERVAL/1000.0)
            
        val = val/self.CALIBARAION_SAMPLE_TIMES                 # calculate the average value

        val = val/self.RO_CLEAN_AIR_FACTOR                      # divided by RO_CLEAN_AIR_FACTOR yields the Ro 
                                                                # according to the chart in the datasheet 

        return val;
      
      
    #########################  MQRead ##########################################
    # Input:   mq_pin - analog channel
    # Output:  Rs of the sensor
    # Remarks: This function use MQResistanceCalculation to caculate the sensor resistenc (Rs).
    #          The Rs changes as the sensor is in the different consentration of the target
    #          gas. The sample times and the time interval between samples could be configured
    #          by changing the definition of the macros.
    ############################################################################ 
    def MQRead(self, mq_pin):
        rs = 0.0

        for i in range(self.READ_SAMPLE_TIMES):
            rs += self.MQResistanceCalculation(self.adc.read(mq_pin))
            time.sleep(self.READ_SAMPLE_INTERVAL/1000.0)

        rs = rs/self.READ_SAMPLE_TIMES

        return rs
     
    #########################  MQGetGasPercentage ##############################
    # Input:   rs_ro_ratio - Rs divided by Ro
    #          gas_id      - target gas type
    # Output:  ppm of the target gas
    # Remarks: This function passes different curves to the MQGetPercentage function which 
    #          calculates the ppm (parts per million) of the target gas.
    ############################################################################ 
    def MQGetGasPercentage(self, rs_ro_ratio, gas_id):
        if ( gas_id == self.GAS_ACETON ):
            return self.MQGetPercentage(rs_ro_ratio, self.ACETONCurve)
        elif ( gas_id == self.GAS_TOLUENO ):
            return self.MQGetPercentage(rs_ro_ratio, self.TOLUENOCurve)
        elif ( gas_id == self.GAS_ALCOHOL ):
            return self.MQGetPercentage(rs_ro_ratio, self.AlcoholCurve)
        elif ( gas_id == self.GAS_CO2 ):
            return self.MQGetPercentage(rs_ro_ratio, self.CO2Curve)
        elif ( gas_id == self.GAS_NH4 ):
            return self.MQGetPercentage(rs_ro_ratio, self.NH4Curve)
        elif ( gas_id == self.GAS_CO ):
            return self.MQGetPercentage(rs_ro_ratio, self.COCurve)
        return 0
    
    #########################  MQGetPercentage #################################
    # Input:   rs_ro_ratio - Rs divided by Ro
    #          pcurve      - pointer to the curve of the target gas
    # Output:  ppm of the target gas
    # Remarks: By using the slope and a point of the line. The x(logarithmic value of ppm) 
    #          of the line could be derived if y(rs_ro_ratio) is provided. As it is a 
    #          logarithmic coordinate, power of 10 is used to convert the result to non-logarithmic 
    #          value.
    ############################################################################ 
    def MQGetPercentage(self, rs_ro_ratio, pcurve):
        if (rs_ro_ratio <= 0):
            return 0;
        else:
            return (math.pow(10,( ((math.log(rs_ro_ratio)-pcurve[1])/ pcurve[2]) + pcurve[0])))
