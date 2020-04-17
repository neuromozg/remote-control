#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import sys
import time

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


class Robot:
    def __init__(self):
        pass

    def move(self, speed):
        print("move: ", speed)

    def rotate(self, speed):
        print("rotate: ", speed)

    def changePlowState(self, state):
        print("plow state: ", state)

    def activatePlant(self, activator):
        if activator:
            print("plant activated")

    def bucketPosition(self, position):
        print("bucket position:  ", position)

    def grabPosition(self, position):
        print("grab position:  ", position)


if __name__ == '__main__':
    try:
        robot = Robot()
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
        sys.exit()
