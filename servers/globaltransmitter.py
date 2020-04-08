#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import sys
import time

SELF_IP = "127.0.0.2"
#SELF_PORT = 5007     # Раскомментируйте, если не нужно его часто менять

LOCAL_SERVER_IP = "127.0.0.1"
LOCAL_SERVER_PORT = 5005


if __name__ == '__main__':
    try:
        sendSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sendSock.connect((LOCAL_SERVER_IP, LOCAL_SERVER_PORT))

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3.0)
        try:
            if 'SELF_PORT' not in globals():
                print("Введите открытый в интернет порт: ")
                try:
                    port = int(input().replace(' ', ''))
                    SELF_PORT = port
                except:
                    print("Не валидный порт, попробуйте ввести данные снова.")
                    sys.exit(1)
            sock.bind((SELF_IP, SELF_PORT))
        except Exception as e:
            print("Произошла ошибка при подключении: ", str(e))
        print("Промежуточный сервер запущен: ")
        print("Собственный хост: {ip}:{port}".format(ip=SELF_IP, port=SELF_PORT))
        print("Отправка пакетов на сервер: {ip}:{port}".format(ip=LOCAL_SERVER_IP, port=LOCAL_SERVER_PORT))
        while True:
            try:
                data = sock.recvfrom(1024)
                sendSock.send(data[0])
            except socket.timeout:
                time.sleep(1)
    except KeyboardInterrupt:
        sendSock.close()
        time.sleep(1)
        sys.exit(0)
