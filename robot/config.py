#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import smbus
import pigrabot
import threading

SELF_HOST = "10.1.0.86:5008"
# KEY = 6006    # если закомментировано - генерируется автоматически
# INFO = "КУБОК РТК"

bus = None
robot = None
display = pigrabot.display

servoPosLen = 125
middleServoPos = servoPosLen // 2

# plowStates = [middleServoPos, 70]
plantStates = [60, 115]
grabLimits = [20, 80]
bucketLimits = [0, 100]

plantActivateFlag = False  # флаг - активирована ли посадка

logger = None


def log(msg):
    global logger
    if logger is not None:
        logger.debug_1(msg)


def err(msg):
    global logger
    if logger is not None:
        logger.error(msg)


def move(speed):
    try:
        robot.setPwm0(-int(speed * 2.55))  # [-100;100] -> [-255;255]
        robot.setPwm1(int(speed * 2.55))  # [-100;100] -> [-255;255]
        log("command: move({speed})".format(speed=speed))
    except Exception as e:
        err("Ошибка управления: command: move(): {e}".format(e=e))


def rotate(speed):
    try:
        robot.setPwm0(int(speed * 2.55))  # [-100;100] -> [-255;255]
        robot.setPwm1(int(speed * 2.55))  # [-100;100] -> [-255;255]
        log("command: rotate({speed})".format(speed=speed))
    except Exception as e:
        err("Ошибка управления: command: rotate(): {e}".format(e=e))


def changePlowState(state):
    try:
        # robot.setServo1(plowStates[int(state)])
        pass
        log("command: changePlowState({state})".format(state=state))
    except Exception as e:
        err("Ошибка управления: command: changePlowState(): {e}".format(e=e))


def activatePlant(activator):
    global plantActivateFlag

    def _actPlant():
        global plantActivateFlag
        try:
            robot.setServo0(plantStates[1])
            time.sleep(2)
            robot.setServo0(plantStates[0])
            time.sleep(1)
            plantActivateFlag = False
            log("Посадка деактивирована")
        except Exception as e:
            plantActivateFlag = False
            err("Ошибка активации посадки: {e}".format(e=e))

    try:
        log("command: activatePlant({activator})".format(activator=activator))
        if activator and not plantActivateFlag:
            threading.Thread(target=_actPlant, daemon=True).start()
            plantActivateFlag = True
            log("Посадка активирована")
    except Exception as e:
        err("Ошибка управления: command: activatePlant(): {e}".format(e=e))


def bucketPosition(position):
    try:
        position = -position
        position = int((position / 100) * (servoPosLen // 2) + middleServoPos)  # [-100, 100] -> [-62, 62] -> [0...62...124]
        position = min(max(bucketLimits[0], position), bucketLimits[1])
        robot.setServo2(position)
        log("command: bucketPosition({position})".format(position=position))
    except Exception as e:
        err("Ошибка управления: command: bucketPosition(): {e}".format(e=e))


def grabPosition(position):
    try:
        position = -position
        position = int((position / 100) * (servoPosLen // 2) + middleServoPos)  # [-100, 100] -> [-62, 62] -> [0...62...124]
        position = min(max(grabLimits[0], position), grabLimits[1])
        robot.setServo3(position)
        log("command: grabPosition({position})".format(position=position))
    except Exception as e:
        err("Ошибка управления: command: grabPosition(): {e}".format(e=e))


def initializeAll():
    try:
        global robot
        global bus
        global display
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
        try:
            if display is not None:
                display.begin()
                display.clear()
                display.display()
            else:
                err("Дисплей робота не инициализирован")
        except:
            display = None
            err("Дисплей робота не инициализирован: ошибка инициализации дисплея")
    except Exception as e:
        err("Ошибка инициализации робота: {e}".format(e=e))
        raise Exception("Ошибка инициализации робота: {e}".format(e=e))


def release():
    try:
        robot.exit()
        bus.close()
    except Exception as e:
        err("Ошибка деинициализации робота: {e}".format(e=e))
        raise Exception("Ошибка деинициализации робота: {e}".format(e=e))
