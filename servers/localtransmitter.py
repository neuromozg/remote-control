#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import sys
import time
import serial

SELF_IP = "127.0.0.1"
SELF_PORT = 5005


class SerialAdapter:
    def __init__(self, port, baudrate):
        self.__port = port
        self.__baudrate = baudrate
        self.__ser = serial.Serial(port=port, baudrate=baudrate)
        self.__startBytes = b'\xaa\xaa'

    def send(self, buffer):
        print(self.__startBytes + buffer)
        self.__ser.write(self.__startBytes + buffer)

    def close(self):
        self.__ser.close()


if __name__ == '__main__':
    try:
        adapter = SerialAdapter("/dev/ttyUSB0", 9600)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3.0)
        sock.bind((SELF_IP, SELF_PORT))
        print("Сервер-адаптер запущен: {ip}:{port}".format(ip=SELF_IP, port=SELF_PORT))
        while True:
            try:
                rawdata, _ = sock.recvfrom(1024)
                adapter.send(rawdata)
            except socket.timeout:
                time.sleep(1)
    except KeyboardInterrupt:
        sock.close()
        adapter.close()
        time.sleep(1)
        sys.exit(0)
