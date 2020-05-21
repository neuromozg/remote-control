import time
import board
from adafruit_ina219 import ADCResolution, BusVoltageRange, INA219

i2c_bus = board.I2C()

ina219 = INA219(i2c_bus)

# optional : change configuration to use 32 samples averaging for both bus voltage and shunt voltage
ina219.bus_adc_resolution = ADCResolution.ADCRES_12BIT_32S
ina219.shunt_adc_resolution = ADCResolution.ADCRES_12BIT_32S
# optional : change voltage range to 16V
ina219.bus_voltage_range = BusVoltageRange.RANGE_16V

# measure and display loop
while True:
    bus_voltage = ina219.bus_voltage        # voltage on V- (load side)
    shunt_voltage = ina219.shunt_voltage    # voltage between V+ and V- across the shunt
    current = ina219.current                # current in mA

    print("Напряжение: %.2f" % bus_voltage)
    print("Ток: %.2f" % current*1000)
    time.sleep(2)