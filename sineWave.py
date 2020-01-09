import numpy as np
import RPi.GPIO as GPIO
import addapy
from adc_consts import *

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

fs = 50.0
Ts = 1/fs
f = 0.5

PIN_DRDY = 11
GPIO.setup(PIN_DRDY, GPIO.IN)

gain = ADS1256_GAIN['1']
rate = ADS1256_DRATE['10']
mode = ADS1256_SMODE['SINGLE_ENDED']
addapy.start_adda(gain, rate, mode)

while true:
    output = np.sin(2*np.pi*f*t)
    t = t+Ts
    addapy.write_volts(0, output)