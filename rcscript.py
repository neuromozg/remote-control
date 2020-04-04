#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import pynput
import time

""" Для того, чтобы единожды задать ip и порт, расскоментируйте следующие строки и запишите в них
 правильные значения ip и порта """
#IP = "192.168.42.10"
#PORT = 5005

""" Управляющие клавиши """
controlKeyMap = {
    "moveForward": ["w", "W", 'ц', "Ц"],
    "moveBackward": ["s", "S", "ы", "Ы"],
    "rotateLeft": [""]

}


def checkHost(host):
    """ функция проверки введенных данных """
    try:
        socket.inet_aton(host[0])
        if len(host[0].split('.')) != 4:
            raise OSError
    except OSError:
        print("Не валидный ip адресс, попробуйте ввести данные снова. IP адресс представляет собой 4 бата,"
              " записанные через точку. Например:  192.168.42.10")
        return False

    try:
        int(host[1])
    except:
        print("Не валидный порт, попробуйте ввести данные снова.")
        return False

    return True


class RemoteRobot:
    """ Класс - обертка для работы с удаленным роботом """
    def __init__(self):
        self.__ip = None
        self.__port = None
        self.__isConnected = False

    def connect(self, ip, port):
        print("Пробую подключиться к роботу {host}".format(host=ip + ':' + port.__str__()))
        self.__ip = ip
        self.__port = port

        self.__isConnected = True

    def disconnect(self):
        self.__isConnected = False
        print("Произвожу отключение от робота {host}".format(host=self.__ip + ':' + self.__port.__str__()))

    @property
    def isConnected(self):
        return self.__isConnected


if __name__ == '__main__':
    robot = RemoteRobot()
    try:
        while True:
            if not robot.isConnected:
                try:
                    if ('IP' in globals()) and ('PORT' in globals()):
                        robot.connect(IP, PORT)
                    else:
                        print("Введите IP: ")
                        ip = input().replace(' ', '')
                        print("Введите порт: ")
                        port = input().replace(' ', '')
                        if checkHost((ip, port)) is False:
                            continue
                        robot.connect(ip, int(port))
                except Exception as e:
                    print("Произошла ошибка при подключении: ", str(e))
            time.sleep(1)
    except KeyboardInterrupt:
        if robot.isConnected:
            robot.disconnect()
        time.sleep(1)
        print("Работа программы успешно завершена")
        exit()
