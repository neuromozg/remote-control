#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import smbus
import pigrabot
import threading

SELF_IP = "10.1.0.86"
SELF_PORT = 5008
# KEY = 6006    # если закомментировано - генерируется автоматически

bus = None
robot = None

servoPosLen = 125
middleServoPos = servoPosLen // 2

#plowStates = [middleServoPos, 70]
plantStates = [middleServoPos, middleServoPos]
grabLimits = [25, 80]
bucketLimits = [0, 100]

plantActivateFlag = False  # флаг - активирована ли посадка


def move(speed):
    robot.setPwm0(-int(speed * 2.55))  # [-100;100] -> [-255;255]
    robot.setPwm1(int(speed * 2.55))  # [-100;100] -> [-255;255]


def rotate(speed):
    robot.setPwm0(int(speed * 2.55))  # [-100;100] -> [-255;255]
    robot.setPwm1(int(speed * 2.55))  # [-100;100] -> [-255;255]


def changePlowState(state):
    pass
    #robot.setServo1(plowStates[int(state)])


def activatePlant(activator):
    global plantActivateFlag

    def _actPlant():
        global plantActivateFlag
        a, b = plantStates
        for pos in range(a, b, int(a < b) * 2 - 1):
            robot.setPwm0(pos)
            time.sleep(0.05)
        plantActivateFlag = False

    if activator and not plantActivateFlag:
        threading.Thread(target=_actPlant, daemon=True).start()
        plantActivateFlag = True


def bucketPosition(position):
    position = -position
    position = int((position / 100) * (servoPosLen // 2) + middleServoPos)  # [-100, 100] -> [-62, 62] -> [0...62...124]
    position = min(max(bucketLimits[0], position), bucketLimits[1])
    robot.setServo2(position)


def grabPosition(position):
    position = -position
    position = int((position / 100) * (servoPosLen // 2) + middleServoPos)  # [-100, 100] -> [-62, 62] -> [0...62...124]
    position = min(max(grabLimits[0], position), grabLimits[1])
    robot.setServo3(position)


def initializeAll():
    global robot
    global bus
    bus = smbus.SMBus(1)
    robot = pigrabot.Pigrabot(bus)
    robot.online = True
    robot.start()
    robot.setPwm0(0)
    robot.setPwm1(0)
    robot.setServo0(int(middleServoPos))
    robot.setServo1(int(middleServoPos))
    robot.setServo2(int(middleServoPos))
    robot.setServo3(int(middleServoPos))


def release():
    robot.exit()
    bus.close()
