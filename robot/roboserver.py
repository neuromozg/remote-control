#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import sys
import time

import smbus

from robot import pigrabot

SELF_IP = "10.1.0.88"
SELF_PORT = 5005

protocolConfig = {
    "startBytes": b'',
    "checksum": "crc16",
    "formatChecksum": 'H',  # 2 байта
    "formatData": 'bbbb??'  # 4 байта + 2 байта bool
}

__packageFormat = '=' + protocolConfig["formatChecksum"] + protocolConfig["formatData"]


def crc16(data: bytes, poly=0x8408):
    """ CRC-16-CCITT Algorithm """
    data = bytearray(data)
    crc = 0xFFFF
    for b in data:
        cur_byte = 0xFF & b
        for _ in range(0, 8):
            if (crc & 0x0001) ^ (cur_byte & 0x0001):
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
            cur_byte >>= 1
    crc = (~crc & 0xFFFF)
    crc = (crc << 8) | ((crc >> 8) & 0xFF)
    return crc & 0xFFFF


class Agrobot:
    def __init__(self, bus, addr=0x27):
        self._bot = pigrabot.Pigrabot(bus, addr)
        self._servoMiddlePos = 125 // 2
        self._plowStates = [self._servoMiddlePos, 70]

    def move(self, speed):
        self._bot.setPwm0(int(speed * 2.55))  # [-100;100] -> [-255;255]
        self._bot.setPwm1(-int(speed * 2.55))  # [-100;100] -> [-255;255]

    def rotate(self, speed):
        self._bot.setPwm0(int(speed * 2.55))  # [-100;100] -> [-255;255]
        self._bot.setPwm1(int(speed * 2.55))  # [-100;100] -> [-255;255]

    def changePlowState(self, state):
        self._bot.setServo0(self._plowStates[int(state)])

    def activatePlant(self, activator):
        if activator:
            print("plant activated")

    def bucketPosition(self, position):
        print("bucket position:  ", position)

    def grabPosition(self, position):
        print("grab position:  ", position)

    def exit(self):
        self._bot.exit()


if __name__ == '__main__':
    try:
        bus = smbus.SMBus(1)
        robot = Agrobot(bus)
        previousStates = [None, None, None, None, None, None]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3.0)
        sock.bind((SELF_IP, SELF_PORT))
        while True:
            try:
                rawdata, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
                data = struct.unpack(__packageFormat, rawdata)
                crc = data[0]
                data = data[1:]
                if crc == crc16(rawdata[struct.calcsize(protocolConfig["formatChecksum"]):]):
                    if data[0] != previousStates[0]:
                        robot.move(data[0])
                    if data[1] != previousStates[1]:
                        robot.rotate(data[1])
                    if data[2] != previousStates[2]:
                        robot.bucketPosition(data[2])
                    if data[3] != previousStates[3]:
                        robot.grabPosition(data[3])
                    if data[4] != previousStates[4]:
                        robot.changePlowState(data[4])
                    if data[5] != previousStates[5]:
                        robot.activatePlant(data[5])

                    previousStates = data[:]
            except socket.timeout:
                time.sleep(1)
    except KeyboardInterrupt:
        robot.exit()
        time.sleep(1)
        sys.exit()
