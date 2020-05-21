#!/usr/bin/env python
from ina219 import INA219
from ina219 import DeviceRangeError
import time

SHUNT_OHMS = 0.01

ina = INA219(SHUNT_OHMS)
ina.configure()

# measure and display loop
while True:
    print("Напряжение: %.2f В" % ina.voltage())
    print("Ток: %.3f А" % (ina.current()/1000))
    print(" ")
    time.sleep(3)
