import tkinter as tk  # library for simple graphical interfaces
from PIL import Image, ImageTk
#from tkinter import *
import numpy as np  # maths library
import threading # multi-tasking library
#import RPi.GPIO as GPI  # raspberry pi IO library
#import addapy # python wrapper for waveshare drivers 
import time  # library for timing
#from adc_consts import * # import the default constants for the adc

# Issues
# addapy library not in python path
# addapy slow
# addapy needs sudo

# set up the naming convention for raspberry pi IO pins
#GPIO.setwarnings(False)
#GPIO.setmode(GPIO.BOARD)

# settings for the ADC chip
#gain = ADS1256_GAIN['1']
#rate = ADS1256_DRATE['10']
#mode = ADS1256_SMODE['SINGLE_ENDED']

# send the settings to the adc chip
#addapy.start_adda(gain, rate, mode)

global running
running = False
stop_event = threading.Event()


def runValve(entries):
    sampleRate = 10  # sample rate in Hz
    Ts = 1/sampleRate
    # get the data from the text boxes
    t1 = abs(float(entries['Ramp up, t1 (sec)'].get()))
    t2 = abs(float(entries['Hold up, t2 (sec)'].get()))
    t3 = abs(float(entries['Ramp down, t3 (sec)'].get()))
    t4 = abs(float(entries['Hold down, t4 (sec)'].get()))
    p1 = abs(float(entries['Low pressure, p1 (volt)'].get()))
    p2 = abs(float(entries['High pressure, p2 (volt)'].get()))
    iterations = abs(int(entries['Number of Iterations'].get()))
    pres = [p1, p2]
    maxLc = np.where(pres == np.amax(pres))
    minLc = np.where(pres == np.amin(pres))
    pHigh = pres[maxLc[0][0]]
    pLow = pres[minLc[0][0]]
    pDiff = pHigh-pLow
    upSamples = np.arange(pLow, pHigh, pDiff / (t1/Ts))
    downSamples = np.flip(np.arange(pLow, pHigh, pDiff / (t3/Ts)))
    if running is False:
        def callback():
            print('output thread started')
            global running
            running = True
            for j in range(0, iterations): # loop through the number of iterations
                for i in upSamples:  # loop through the samples for ramp down 
                    if stop_event.is_set():  # stop if button pressed
                        break
                    print(f'output: {i:.3f}')
                    # addapy.write_volts(0, i)
                    time.sleep(Ts)
                if stop_event.is_set():  # stop if button pressed
                    # addapy.write_volts(0, 0)
                    stop_event.clear()
                    running = False
                    break
                print(f'output: {p2:.3f}')
                # addapy.write_volts(0, p2)
                time.sleep(t2)
                for i in downSamples: # loop through the samples for ramp down 
                    if stop_event.is_set():
                        break
                    print(f'output: {i:.3f}')
                    # addapy.write_volts(0, i)
                    time.sleep(Ts)

                if stop_event.is_set():
                    # addapy.write_volts(0, 0)
                    stop_event.clear()
                    running = False
                    break
                # addapy.write_volts(0, p1)
                time.sleep(t4)            
                print(f'output: {p1:.3f}')
                # addapy.write_volts(0, p1)
                print('end of iteration')
                running = False
        t = threading.Thread(target=callback)
        t.start()
        return(t)


def stopValve():
    stop_event.set()
    # addapy.write_volts(0, 0)


def quitButton():
    # function for quit button
    stop_event.set()  # send the stop signal
    root.quit  # quit the gui loop to end the programme


def makeform(root, fields, defaults):
    entries = {}
    for field in range(0, len(defaults)):
        print(fields[field])
        row = tk.Frame(root)
        lab = tk.Label(row, width=22, text=fields[field]+": ", anchor='w')
        ent = tk.Entry(row)
        ent.insert(0, str(defaults[field]))
        row.pack(side=tk.TOP,
                 fill=tk.X,
                 padx=5,
                 pady=5)
        lab.pack(side=tk.LEFT)
        ent.pack(side=tk.RIGHT,
                 expand=tk.YES,
                 fill=tk.X)
        entries[fields[field]] = ent
    return entries

fields = ('Ramp up, t1 (sec)', 'Hold up, t2 (sec)', 'Ramp down, t3 (sec)', 
          'Hold down, t4 (sec)', 'Low pressure, p1 (volt)', 
          'High pressure, p2 (volt)', 'Number of Iterations')

defaults = [5, 3, 0.5, 3, 0, 0.32, 5]

if __name__ == '__main__':
    root = tk.Tk()
    load = Image.open("./images/pressureProfile.tiff")
    render = ImageTk.PhotoImage(load)
    img = tk.Label(image=render)
    #img.image = render
    img.pack(side="top", fill="both", expand="no")
    ents = makeform(root, fields,defaults)
    b1 = tk.Button(root, text='Run',
                   command=(lambda e=ents: runValve(e)))
    b1.pack(side=tk.LEFT, padx=10, pady=8)
    b2 = tk.Button(root, text='Stop',
                   command=(lambda e=ents: stopValve()))
    b2.pack(side=tk.LEFT, padx=10, pady=8)
    b3 = tk.Button(root, text='Quit', command=root.quit)
    b3.pack(side=tk.LEFT, padx=10, pady=8)
    root.mainloop()
