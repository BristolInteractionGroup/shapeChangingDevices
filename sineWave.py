import numpy as np
import RPi.GPIO as GPIO
import addapy
import time
from adc_consts import *
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# issues:
# add time rollover to avoid upper limit for time
# background processes affecting timing
# add options for starting script
# add ramp control

# settings for a sinewave
fs = 50  # sample frequncy (Hz)
f = 0.5  # signal frequency (Hz)
t = 0.0  # current time (sec)
amp = 0.2  # sinewave amplitude (volts)

Ts = 1/fs # time period (sec)
PIN_DRDY = 11
GPIO.setup(PIN_DRDY, GPIO.IN)

gain = ADS1256_GAIN['1']
rate = ADS1256_DRATE['10']
mode = ADS1256_SMODE['SINGLE_ENDED']
addapy.start_adda(gain, rate, mode)

while True:
    # addapy.read_adc() --- very slow function
    output = np.abs(amp + amp*np.sin(2*np.pi*f*t))  # generate a sinewave with minimum at zero volts
    t = t+Ts
    addapy.write_volts(0, output)
    time.sleep(Ts)
    #print(output, end="\r", flush=True)