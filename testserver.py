#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import threading
from pynput import keyboard
import time

protocolConfig = {
    "startBytes": b'',
    "checksum": "crc16",
    "formatChecksum": 'H',  # 2 байта
    "formatData": 'bb'  # 1 + 1 байт
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
        print("move", speed)

    def rotate(self, speed):
        print("rotate", speed)


if __name__ == '__main__':
    robot = Robot()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 5005))
    while True:
        rawdata, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
        data = struct.unpack(__packageFormat, rawdata)
        if data[0] == crc16(rawdata[struct.calcsize(protocolConfig["formatChecksum"]):]):
            robot.move(data[1])
            robot.rotate(data[2])
