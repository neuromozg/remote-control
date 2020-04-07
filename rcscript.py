#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import threading
from pynput import keyboard
import time

""" Для того, чтобы единожды задать ip и порт, расскоментируйте следующие строки и запишите в них
 правильные значения ip и порта """
# IP = "127.0.0.1"
# PORT = 5005

""" Управляющие клавиши """
controlKeyMap = {
    "moveForward": ["w", "W", 'ц', "Ц"],
    "moveBackward": ["s", "S", "ы", "Ы"],
    "rotateLeft": ["a", "A", "ф", "Ф"],
    "rotateRight": ["d", "D", "в", "В"],
    "addSpeed": ["X", "x", "ч", "Ч"],
    "subSpeed": ["Z", "z", "я", "Я"],
    "changePlowState": ["J", "j", "о", "О"],
    "changePlantStateFlag": ["H", "h", "р", "Р"],
    "bucketMoveUp": ["R", "r", "к", "К"],
    "bucketMoveDown": ["F", "f", "а", "А"],
    "grabClamp": ["I", "i", "ш", "Ш"],
    "grabLoose": ["U", "u", "г", "Г"]
}


def info():
    print("Для управления используйте следующие клавиши на клавиатуре:")
    print("\tW - двигаться вперед (удерживайте)")
    print("\tS - двигаться назад (удерживайте)")
    print("\tA - поворот влево (удерживайте)")
    print("\tD - поворот вправо (удерживайте)")
    print("\tJ - поднять/опустить плуг")
    print("\tH - посадить картошку")
    print("\tR - поднять ковш (удерживайте)")
    print("\tF - опустить ковш (удерживайте)")
    print("\tI - сжать схват (удерживайте)")
    print("\tU - отпустить схват (удерживайте)")


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
        self.__sock = None
        self.__packageFormat = "=bbbb??"  # формат отправляемых пакетов, порядок и расшифровка ниже
        #   || (b) int8 - move speed [-100,100]         || (b) int8 - rotate speed [-100, 100]    ||->
        # ->|| (b) int8 - bucket position [-100,100]    || (b) int8 - grab position [-100, 100]   ||->
        # ->|| (?) bool - plow state                    || (?) bool - plant state flag            ||
        self.__isConnected = False  # флаг подключения
        self.__speed = 50  # диапазон - [0, 100]
        self.__speedAddStep = 20  # шаг с которым может меняться скорость
        self.__moveDirection = 0  # Направление движения робота: -1, 0, 1
        self.__rotateDirection = 0  # Направление поворота робота: -1, 0, 1
        self.__plowState = False  # Состояние плуга: False - убран, True - опущен
        self.__plantStateFlag = False  # Флаг активации диспенсора при True - активируется, False - сброс флага
        self.__bucketPosition = 0  # Позиция ковша, диапазон - [-100, 100]
        self.__grabPosition = 0  # Позиция схвата, диапазон - [-100, 100]
        self.__positionChangeStep = 1  # Шаг изменения позиций при зажатии клавиш управения

    def connect(self, ip, port):
        print("Пробую подключиться к роботу {host}".format(host=ip + ':' + port.__str__()))
        self.__ip = ip
        self.__port = port
        self.__connectKeyboard()  # запускаем поток опроса клавиатуры
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # создаем сокет
        self.__sock.connect((self.__ip, self.__port))
        threading.Thread(target=self.__sendThread, daemon=True).start()  # запуск потока отправки
        print("Пакеты к {host} начали отправляться, проверьте состояние"
              " подключения через трансляцию".format(host=ip + ':' + port.__str__()))
        self.__isConnected = True

    def disconnect(self):
        self.__isConnected = False
        print("Произвожу отключение от робота {host}".format(host=self.__ip + ':' + self.__port.__str__()))
        self.__sock.close()

    @property
    def isConnected(self):
        return self.__isConnected

    def addToSpeed(self, value):
        self.__speed = min(max(0, self.__speed + value), 100)

    def __sendThread(self):
        """ поток переодической отправки пакетов """
        while True:
            if self.isConnected:
                package = b''  # стартовые байты
                moveSpeed = int(self.__moveDirection * self.__speed)  # пересчет скорости движения
                rotateSpeed = int(self.__rotateDirection * self.__speed)  # пересчет скорости поворота
                data = struct.pack(self.__packageFormat,
                                   moveSpeed, rotateSpeed,
                                   self.__bucketPosition, self.__grabPosition,
                                   self.__plowState, self.__plantStateFlag)  # упаковка параметров управления
                crc = struct.pack('=H', crc16(data))  # избыточный код
                package += crc + data  # объединение частей пакета
                self.__sock.send(package)  # отправка пакета
            time.sleep(0.1)

    def __connectKeyboard(self):
        """ привязка обработчиков кнопок клавиатуры """

        def onPress(key):
            global controlKeyMap
            try:
                if key.char in controlKeyMap["moveForward"]:
                    self.__moveDirection = 1
                elif key.char in controlKeyMap["moveBackward"]:
                    self.__moveDirection = -1
                elif key.char in controlKeyMap["rotateRight"]:
                    self.__rotateDirection = 1
                elif key.char in controlKeyMap["rotateLeft"]:
                    self.__rotateDirection = -1

                elif key.char in controlKeyMap["changePlantStateFlag"]:
                    self.__plantStateFlag = True  # при зажатой клавише всегда отправляется True

                elif key.char in controlKeyMap["bucketMoveUp"]:
                    self.__bucketPosition = min(max(-100, self.__bucketPosition + self.__positionChangeStep), 100)
                elif key.char in controlKeyMap["bucketMoveDown"]:
                    self.__bucketPosition = min(max(-100, self.__bucketPosition - self.__positionChangeStep), 100)

                elif key.char in controlKeyMap["grabClamp"]:
                    self.__grabPosition = min(max(-100, self.__grabPosition + self.__positionChangeStep), 100)
                elif key.char in controlKeyMap["grabLoose"]:
                    self.__grabPosition = min(max(-100, self.__grabPosition - self.__positionChangeStep), 100)

            except AttributeError:
                pass

        def onRelease(key):
            global controlKeyMap
            try:
                if (key.char in controlKeyMap["moveForward"]) or (key.char in controlKeyMap["moveBackward"]):
                    self.__moveDirection = 0
                elif (key.char in controlKeyMap["rotateRight"]) or (key.char in controlKeyMap["rotateLeft"]):
                    self.__rotateDirection = 0

                elif key.char in controlKeyMap["addSpeed"]:
                    self.addToSpeed(self.__speedAddStep)
                elif key.char in controlKeyMap["subSpeed"]:
                    self.addToSpeed(-self.__speedAddStep)

                elif key.char in controlKeyMap["changePlowState"]:
                    self.__plowState = not self.__plowState

                elif key.char in controlKeyMap["changePlantStateFlag"]:
                    self.__plantStateFlag = False

            except AttributeError:
                pass

        keyboard.Listener(
            on_press=onPress,
            on_release=onRelease,
            daemon=True).start()


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
                        info()
                except Exception as e:
                    print("Произошла ошибка при подключении: ", str(e))
            time.sleep(1)
    except KeyboardInterrupt:
        if robot.isConnected:
            robot.disconnect()
        time.sleep(1)
        print("Работа программы успешно завершена")
        exit()
