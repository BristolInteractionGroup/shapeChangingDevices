import tkinter as tk  # library for simple graphical interfaces
from PIL import Image, ImageTk
import numpy as np  # maths library
import threading  # multi-tasking library
import time  # library for timing
import RPi.GPIO as GPIO  # raspberry pi IO library
import addapy  # python wrapper for waveshare drivers 
from adc_consts import *  # import the default constants for the adc


# Issues
# addapy library not in python path
# addapy slow
# addapy needs sudo

# set up the naming convention for raspberry pi IO pins
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

# settings for the ADC chip
gain = ADS1256_GAIN['1']
rate = ADS1256_DRATE['10']
mode = ADS1256_SMODE['SINGLE_ENDED']
addapy.start_adda(gain, rate, mode)  # send the settings to the adc chip

# limiting values to prevent high pressure being sent to device
pMin = 0.0
pMax = 0.5
fields = ('Ramp up, t1 (sec)', 'Hold up, t2 (sec)', 'Ramp down, t3 (sec)', 
          'Hold down, t4 (sec)', 'Low pressure, p1 (volt)',
          'High pressure, p2 (volt)', 'Number of Iterations')
defaults = [5, 3, 0.5, 3, 0, 0.32, 5]  # default value for fields

global threadRunning  # define a global variable used to stop multiple output threads from threadRunning
threadRunning = False  # as the thread isn't threadRunning setting to false
stop_event = threading.Event()  # create an event which stops the threads


def runValve(entries):
    sampleRate = 10  # sample rate in Hz
    Ts = 1/sampleRate  # calculate the sample period in seconds
    # get the data from the text boxes
    t1 = abs(float(entries['Ramp up, t1 (sec)'].get()))
    t2 = abs(float(entries['Hold up, t2 (sec)'].get()))
    t3 = abs(float(entries['Ramp down, t3 (sec)'].get()))
    t4 = abs(float(entries['Hold down, t4 (sec)'].get()))
    p1 = abs(float(entries['Low pressure, p1 (volt)'].get()))
    p2 = abs(float(entries['High pressure, p2 (volt)'].get()))

    p1 = np.clip(p1,pMin,pMax)  # clip the pressure to a safe range    
    p2 = np.clip(p2,pMin,pMax)  # clip the pressure to a safe range

    entries['Low pressure, p1 (volt)'].delete(0,'end')
    entries['High pressure, p2 (volt)'].delete(0,'end')
    entries['Low pressure, p1 (volt)'].insert(0,str(p1))
    entries['High pressure, p2 (volt)'].insert(0,str(p2))
    
    noOfIterations = abs(int(entries['Number of Iterations'].get()))
    # create the pressure time series
    pressureSamples = generateSamples(t1, t2, t3, t4, p1, p2, Ts)  
    if threadRunning is False:  # start a thread if there isn't one running
        def callback():  # create a callback function for the thread
            print('output thread started')
            global threadRunning
            threadRunning = True  # set threadthreadRunning to true
            # loop through iterations
            for iteration in range(0, noOfIterations):
                # loop through each pressure samples
                for pressure in pressureSamples:
                    # if stop button is pressed, break the loop
                    if stop_event.is_set():
                        break
                    addapy.write_volts(0, pressure)  # send the voltage
                    print(f'output: {pressure:.3f}')
                    time.sleep(Ts)  # wait until next sample
                if stop_event.is_set():  # if stop button break loop and reset event

                    break
                print('end of iteration')
            print('output ended')
            addapy.write_volts(0, 0)
            stop_event.clear()
            threadRunning = False  # last line so thread is closing
        t = threading.Thread(target=callback)
        t.start()
        return(t)


# function to create time series of pressure samples
def generateSamples(t1, t2, t3, t4, p1, p2, Ts):
    rampUp = np.linspace(p1, p2, int(t1/Ts))  # samples for ramp up phase
    holdUp = p2 * np.ones(int(t2/Ts))  # samples for hold up
    rampDown = np.linspace(p2, p1, int(t3/Ts))  # samples for ramp down phase
    holdDown = p1 * np.ones(int(t4/Ts))  # samples for hold down
    if invertPolarity.get() is True:
        # combines the arrays we made
        pressureSamples = np.concatenate((rampDown, holdDown, rampUp, holdUp))
    else:
        # combines the arrays we made in inverted order
        pressureSamples = np.concatenate((rampUp, holdUp, rampDown, holdDown))
    return (pressureSamples)


def stopValve():
    stop_event.set()
    addapy.write_volts(0, 0)
    print('output: 0.000')
    print('output stopped')


def changePolarity():
    #  changes holding voltage between p1 and p2
    if invertPolarity.get() is True:
        print('invert enabled')
        addapy.write_volts(0, p2)
    else:
        addapy.write_volts(0, 0)
        print('invert disabled')
    return


def quitButton():
    # function for quit button
    stopValve()  # stop any threads which are still running
    root.quit  # quit the gui loop to end the programme


def makeform(root, fields, defaults):  # this adds the text fields to the UI
    entries = {}


    for field in range(0, len(defaults)):
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


# create the user interface (UI) and create the image and buttons.
# Also starts a loop which handles user functions
if __name__ == '__main__':
    root = tk.Tk()
    load = Image.open("./images/pressureProfile.tiff")
    render = ImageTk.PhotoImage(load)
    img = tk.Label(image=render)
    img.pack(side="top", fill="both", expand="no")
    ents = makeform(root, fields, defaults)
    invertPolarity = tk.BooleanVar()
    row = tk.Frame(root)
    chkInvert = tk.Checkbutton(root,
                   text='invert polarity (hold at p2 and start with ramp down)',
                   var=invertPolarity,
                   command=changePolarity)
    chkInvert.pack(side='top')
    b1 = tk.Button(root,
                   text='Run',
                   command=(lambda e=ents: runValve(e)))
    b1.pack(side=tk.LEFT, padx=10, pady=8)
    b2 = tk.Button(root,
                   text='Stop',
                   command=(lambda e=ents: stopValve()))
    b2.pack(side=tk.LEFT, padx=10, pady=8)
    b3 = tk.Button(root,
                   text='Quit',
                   command=root.quit)
    b3.pack(side=tk.LEFT, padx=10, pady=8)
    root.mainloop()
