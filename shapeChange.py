import tkinter as tk
import numpy as np
import threading
import RPi.GPIO as GPIO
import addapy
import time
from adc_consts import *

# Issues
# multiple threads can start
# make sure if not running, output is zero
# call addapy library, needs sudo and not global

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

gain = ADS1256_GAIN['1']
rate = ADS1256_DRATE['10']
mode = ADS1256_SMODE['SINGLE_ENDED']
addapy.start_adda(gain, rate, mode)


stop_event = threading.Event()


def runValve(entries):
    sampleRate = 10  # sample rate in Hz
    Ts = 1/sampleRate
    # get the data from the text boxes
    t1 = float(entries['Ramp up, t1 (sec)'].get())
    t2 = float(entries['Hold up, t2 (sec)'].get())
    t3 = float(entries['Ramp down, t3 (sec)'].get())
    t4 = float(entries['Hold down, t4 (sec)'].get())
    p1 = float(entries['Low pressure, p1 (volt)'].get())
    p2 = float(entries['High pressure, p2 (volt)'].get())
    pres = [p1, p2]
    maxLc = np.where(pres == np.amax(pres))
    minLc = np.where(pres == np.amin(pres))
    pHigh = pres[maxLc[0][0]]
    pLow = pres[minLc[0][0]]
    pDiff = pHigh-pLow
    upSamples = np.arange(pLow, pHigh, pDiff / (t1/Ts))
    downSamples = np.flip(np.arange(pLow, pHigh, pDiff / (t3/Ts)))

    def callback():
        while True:
            for i in upSamples:
                print(i)
                addapy.write_volts(0, i)
                time.sleep(Ts)
                if stop_event.is_set():
                    break
            addapy.write_volts(0, p2)
            time.sleep(t2)
            for i in downSamples:
                print(i)
                addapy.write_volts(0, i)
                time.sleep(Ts)
                if stop_event.is_set():
                    break
            addapy.write_volts(0, p1)
            time.sleep(t4)
            if stop_event.is_set():
                stop_event.clear()
                break
    t = threading.Thread(target=callback)
    t.start()
    return(t)


def stopValve():
    print('stopping')
    stop_event.set()
    addapy.write_volts(0, 0)


def makeform(root, fields):
    entries = {}
    for field in fields:
        print(field)
        row = tk.Frame(root)
        lab = tk.Label(row, width=22, text=field+": ", anchor='w')
        ent = tk.Entry(row)
        ent.insert(0, "1")
        row.pack(side=tk.TOP,
                 fill=tk.X,
                 padx=5,
                 pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT,
                 expand=tk.YES,
                 fill=tk.X)
        entries[field] = ent
    return entries

fields = ('Ramp up, t1 (sec)', 'Hold up, t2 (sec)', 'Ramp down, t3 (sec)', 'Hold down, t4 (sec)', 'Low pressure, p1 (volt)', 'High pressure, p2 (volt)', 'number')


if __name__ == '__main__':
    root = tk.Tk()
    ents = makeform(root, fields)
    b1 = tk.Button(root, text='Run',
                   command=(lambda e=ents: runValve(e)))
    b1.pack(side=tk.LEFT, padx=5, pady=5)
    b2 = tk.Button(root, text='Stop',
                   command=(lambda e=ents: stopValve()))
    b2.pack(side=tk.LEFT, padx=5, pady=5)
    b3 = tk.Button(root, text='Quit', command=root.quit)
    b3.pack(side=tk.LEFT, padx=5, pady=5)
    root.mainloop()
