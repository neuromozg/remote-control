#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import smbus
import pigrabot

SELF_IP = "10.1.0.86"
SELF_PORT = 5008
# KEY = 6006    # если закомментировано - генерируется автоматически

bus = None
robot = None

servoPosLen = 125
middleServoPos = servoPosLen // 2

plowStates = [middleServoPos, 70]


def move(speed):
    robot.setPwm0(-int(speed * 2.55))  # [-100;100] -> [-255;255]
    robot.setPwm1(int(speed * 2.55))  # [-100;100] -> [-255;255]


def rotate(speed):
    robot.setPwm0(int(speed * 2.55))  # [-100;100] -> [-255;255]
    robot.setPwm1(int(speed * 2.55))  # [-100;100] -> [-255;255]


def changePlowState(state):
    robot.setServo0(plowStates[int(state)])


def activatePlant(activator):
    if activator:
        print("plant activated")


def bucketPosition(position):
    print("bucket position:  ", position)


def grabPosition(position):
    print("grab position:  ", position)


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
