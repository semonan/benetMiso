import clr   # needs the "pythonnet" package
import sys
import os
import time
import numpy
import cv2
from matplotlib import pyplot as plt
from collections import deque
from datetime import datetime
import threading

import platform
bits, name = platform.architecture()
if bits == "64bit":
    clr.AddReference("main/babyMonitoring/x64/LeptonUVC")
    clr.AddReference("main/babyMonitoring/x64/ManagedIR16Filters")
else:
    clr.AddReference("main/babyMonitoring/x86/LeptonUVC")
    clr.AddReference("main/babyMonitoring/x86/ManagedIR16Filters")
    
from Lepton import CCI
from IR16Filters import IR16Capture, NewIR16FrameEvent, NewBytesFrameEvent

WIDTH = 160
HEIGHT = 120

incoming_frames = deque(maxlen=10)
lepton = None
capture = None
currentCelsiusArr = None


def got_a_frame(short_array, width, height):
    global incoming_frames
    incoming_frames.append((height, width, short_array))


def getPureThermalDevice():
    for device in CCI.GetDevices():
        if device.Name.startswith("PureThermal"):
            return device  


def initCamera():
    global lepton
    global capture

    try:
        foundDevice = getPureThermalDevice()

        if not foundDevice:
            print("Couldn't find lepton device")
            return False
        else:
            lepton = foundDevice.Open()
            lepton.sys.RunFFCNormalization()

            shutterObj = lepton.sys.GetFfcShutterModeObj()
            shutterObj.shutterMode = CCI.Sys.FfcShutterMode.MANUAL
            lepton.sys.SetFfcShutterModeObj(shutterObj)

            lepton.sys.SetGainMode(CCI.Sys.GainMode.HIGH)
            capture = IR16Capture()
            capture.SetupGraphWithBytesCallback(NewBytesFrameEvent(got_a_frame))
            return True

    except ValueError as msg:
        print(msg)


def short_array_to_numpy(height, width, frame):
    return numpy.fromiter(frame, dtype="uint16").reshape(height, width)


def centikelvin_to_celsius(t):
    return (t - 27315.0) / 100.0


def getRawThermalArr():
    global incoming_frames

    if len(incoming_frames) == 0:
        return False

    height, width, net_array = incoming_frames[-1]
    return short_array_to_numpy(height, width, net_array)


def createDirectory(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print("Error: Failed to create the directory.")


def captureCelsiusArr():
    global currentCelsiusArr
    global WIDTH
    global HEIGHT
    rawImg = getRawThermalArr()
    currentCelsiusArr = centikelvin_to_celsius(rawImg)
    return rawImg


def getCurrentCelsiusArr():
    global currentCelsiusArr
    return currentCelsiusArr


def saveCapture(rawArr):
    img = cv2.normalize(rawArr, None, 0, 255, cv2.NORM_MINMAX)
    img = img.astype('uint8')
    img = cv2.applyColorMap(img, cv2.COLORMAP_PARULA)
    cv2.imwrite('./capture/currentCapture.png', img)


def saveTemperature(celcius):
    with open("./capture/temperature.csv", "a") as file:
        now = datetime.now()
        currTime = now.strftime('%Y%m%d_%H%M%S')
        file.write(currTime + ', ' + str(celcius) + "\n")
        file.close()

    
def getHighCelcius():
    arr = getCurrentCelsiusArr()
    if arr is None:
        return None

    flatArr = arr.flatten()
    ranks = flatArr.argsort()
    values = []
    N = 10
    for idx in ranks[::-1][:N]:
        values.append(flatArr[idx])

    return round(sum(values)/len(values), 1)        


def threadWorker():
    global lepton
    global capture
    global currentCelsiusArr

    createDirectory('capture')

    while(True):
        if not getPureThermalDevice():
            print('PureThermal device not found.')
            lepton = None
            capture = None
            currentCelsiusArr = None
            time.sleep(2)
            continue

        if (not lepton) and getPureThermalDevice():
            try:
                print('Camera is initializing.')
                initCamera()
                capture.RunGraph()
                time.sleep(2)
            except ValueError as msg:
                print('[ERR] ' + msg)
                continue

        rawArr = captureCelsiusArr()
        saveCapture(rawArr)

        celcius = getHighCelcius()
        if celcius is not None:
            saveTemperature(celcius)


        time.sleep(1)



captureThread = threading.Thread(target=threadWorker)
captureThread.start()




# def captureAndSave():
#     img = getThermalImg()
#     img = centikelvin_to_celsius_matrix(img)*10
#     img = img.astype('uint16')
#     #img = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)

#     now = datetime.now()
#     fname = now.strftime('%Y%m%d_%H%M%S') + '.png'

#     cv2.imwrite('./result/' + fname, img)

#     #plt.imshow(img, cmap='gray', vmin=0, vmax=255)
