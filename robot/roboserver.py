#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import sys
import time
import config
import smbus

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


if __name__ == '__main__':
    try:
        previousStates = [None, None, None, None, None, None]
        config.initializeAll()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3.0)
        sock.bind((config.SELF_IP, config.SELF_PORT))
        while True:
            try:
                rawdata, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
                data = struct.unpack(__packageFormat, rawdata)
                crc = data[0]
                data = data[1:]
                if crc == crc16(rawdata[struct.calcsize(protocolConfig["formatChecksum"]):]):
                    if data[0] != previousStates[0]:
                        config.move(data[0])
                    if data[1] != previousStates[1]:
                        config.rotate(data[1])
                    if data[2] != previousStates[2]:
                        config.bucketPosition(data[2])
                    if data[3] != previousStates[3]:
                        config.grabPosition(data[3])
                    if data[4] != previousStates[4]:
                        config.changePlowState(data[4])
                    if data[5] != previousStates[5]:
                        config.activatePlant(data[5])

                    previousStates = data[:]
            except socket.timeout:
                time.sleep(1)
    except KeyboardInterrupt:
        config.release()
        time.sleep(1)
        sys.exit()
