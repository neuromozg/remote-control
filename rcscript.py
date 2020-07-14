#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import threading
from pynput import keyboard
from pynput.keyboard import Key
import time
""" Для того, чтобы единожды задать ip и порт, расскоментируйте следующие строки и запишите в них
 правильные значения ip и порта """
IP = "188.68.186.139"
# IP = "127.0.0.1"
# PORT = 5005

""" Управляющие клавиши """
controlKeyMap = {
    "moveForward": ["w", "W", 'ц', "Ц"],
    "moveBackward": ["s", "S", "ы", "Ы"],
    "rotateLeft": ["a", "A", "ф", "Ф"],
    "rotateRight": ["d", "D", "в", "В"],
    "addSpeed": ["+", "=", "]", "}", "Ъ", "ъ"],
    "subSpeed": ["_", "-", "[", "{", "Х", "х"],
    "changeGunStateFlag": [Key.enter],
    "changePlantStateFlag": [Key.space],
    "bucketMoveUp": ["P", "p", "з", "З"],
    "bucketMoveDown": ["L", "l", "д", "Д"],
    "grabLoose": ["O", "o", "щ", "Щ"],
    "grabClamp": ["K", "k", "л", "Л"]
}


def info():
    print("Use the following keys on the keyboard to control:")
    print("\tW - move forward (hold on)")
    print("\tS - move backward (hold on)")
    print("\tA - left turn (hold on)")
    print("\tD - turn right (hold on)")
    print("\t- - slow down speed")
    print("\t+ - speed up")
    print("\tSpace - plant potatoes")
    print("\tEnter - shot")
    print("\tP - bucket move up (hold on)")
    print("\tL - bucket move down (hold on)")
    print("\tK - grip a grab  (hold on)")
    print("\tO - release a grab (hold on)")


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
        print("Invalid ip address, try entering the data again. IP address is 4 bytes,"
              " written through a dot. For example: 192.168.42.10")
        return False
    try:
        int(host[1])
    except:
        print("Invalid port, try entering the data again")
        return False
    return True


class RemoteRobot:
    """ Класс - обертка для работы с удаленным роботом """

    def __init__(self):
        self.__ip = None
        self.__port = None
        self.__sock = None
        self.__key = None
        self.__packageFormat = "=Hbbbb??H"  # формат отправляемых пакетов, порядок и расшифровка ниже
        #   || (H) uint16 - package number [0, 0xFFFF]  ||->
        # ->|| (b) int8 - move speed [-100,100]         || (b) int8 - rotate speed [-100, 100]    ||->
        # ->|| (b) int8 - bucket position [-100,100]    || (b) int8 - grab position [-100, 100]   ||->
        # ->|| (?) bool - gun state flag                || (?) bool - plant state flag            ||->
        # ->|| (H) uint8 - display abs speed flag       ||
        self.__isConnected = False  # флаг подключения
        self.__speed = 80  # диапазон - [60, 100]
        self.__speedAddStep = 10  # шаг с которым может меняться скорость
        self.__moveDirection = 0  # Направление движения робота: -1, 0, 1
        self.__rotateDirection = 0  # Направление поворота робота: -1, 0, 1
        self.__gunStateFlag = False  # Флаг активации стрелялки при True - активируется, False - сброс флага
        self.__plantStateFlag = False  # Флаг активации диспенсора при True - активируется, False - сброс флага
        self.__bucketPosition = 0  # Позиция ковша, диапазон - [-100, 100]
        self.__grabPosition = 0  # Позиция схвата, диапазон - [-100, 100]
        self.__positionChangeStep = 3  # Шаг изменения позиций при зажатии клавиш управения
        self.__changeSpeedFlag = False  # Флаг изменения скорости

    def connect(self, ip, port, key):
        print("Try to connect to the robot {host}".format(host=ip + ':' + port.__str__()))
        self.__ip = ip
        self.__port = port
        self.__key = key
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # создаем сокет
        self.__sock.connect((self.__ip, self.__port))
        self.__connectKeyboard()  # запускаем поток опроса клавиатуры
        threading.Thread(target=self.__sendThread, daemon=True).start()  # запуск потока отправки
        print("Packets to {host} started sending, check the connection status"
              " through video stream".format(host=ip + ':' + port.__str__()))
        self.__isConnected = True

    def disconnect(self):
        self.__isConnected = False
        print("Disconnecting from the robot {host}".format(host=self.__ip + ':' + self.__port.__str__()))
        self.__sock.close()

    @property
    def isConnected(self):
        return self.__isConnected

    def addToSpeed(self, value):
        self.__speed = min(max(60, self.__speed + value), 100)
        self.__changeSpeedFlag = True

    def __sendThread(self):
        """ поток переодической отправки пакетов """
        packageNum = 0
        try:
            while True:
                if self.isConnected:
                    package = b''  # стартовые байты
                    moveSpeed = int(self.__moveDirection * self.__speed)  # пересчет скорости движения
                    rotateSpeed = int(self.__rotateDirection * self.__speed)  # пересчет скорости поворота
                    speedFlag = self.__speed | (int(self.__changeSpeedFlag) << 7)
                    self.__changeSpeedFlag = False
                    data = struct.pack(self.__packageFormat,
                                       packageNum,
                                       moveSpeed, rotateSpeed,
                                       self.__bucketPosition, self.__grabPosition,
                                       self.__gunStateFlag, self.__plantStateFlag,
                                       speedFlag)  # упаковка параметров управления
                    crc = struct.pack('=H', crc16(data))  # избыточный код
                    key = struct.pack('=H', self.__key)
                    package += crc + key + data  # объединение частей пакета
                    packageNum += 1
                    if packageNum > 0xFFFF:
                        packageNum = 0
                    self.__sock.send(package)  # отправка пакета
                time.sleep(0.1)
        except ConnectionRefusedError:
            print("Connection refused, try restarting the program and entering right data")
            print("The program has shut down")
            time.sleep(5)
            exit()
        except Exception as e:
            print("Internal error: ", str(e))

    def __connectKeyboard(self):
        """ привязка обработчиков кнопок клавиатуры """

        def onPress(key):
            global controlKeyMap
            try:
                key = key.char
            except AttributeError:
                pass
            try:
                if key in controlKeyMap["moveForward"]:
                    self.__moveDirection = 1
                elif key in controlKeyMap["moveBackward"]:
                    self.__moveDirection = -1
                elif key in controlKeyMap["rotateRight"]:
                    self.__rotateDirection = 1
                elif key in controlKeyMap["rotateLeft"]:
                    self.__rotateDirection = -1

                elif key in controlKeyMap["changePlantStateFlag"]:
                    self.__plantStateFlag = True  # при зажатой клавише всегда отправляется True
                elif key in controlKeyMap["changeGunStateFlag"]:
                    self.__gunStateFlag = True  # при зажатой клавише всегда отправляется True

                elif key in controlKeyMap["bucketMoveUp"]:
                    self.__bucketPosition = min(max(-100, self.__bucketPosition + self.__positionChangeStep), 100)
                elif key in controlKeyMap["bucketMoveDown"]:
                    self.__bucketPosition = min(max(-100, self.__bucketPosition - self.__positionChangeStep), 100)

                elif key in controlKeyMap["grabClamp"]:
                    self.__grabPosition = min(max(-100, self.__grabPosition + self.__positionChangeStep), 100)
                elif key in controlKeyMap["grabLoose"]:
                    self.__grabPosition = min(max(-100, self.__grabPosition - self.__positionChangeStep), 100)

            except:
                pass

        def onRelease(key):
            global controlKeyMap
            try:
                key = key.char
            except AttributeError:
                pass
            try:
                if (key in controlKeyMap["moveForward"]) or (key in controlKeyMap["moveBackward"]):
                    self.__moveDirection = 0
                elif (key in controlKeyMap["rotateRight"]) or (key in controlKeyMap["rotateLeft"]):
                    self.__rotateDirection = 0

                elif key in controlKeyMap["addSpeed"]:
                    self.addToSpeed(self.__speedAddStep)
                elif key in controlKeyMap["subSpeed"]:
                    self.addToSpeed(-self.__speedAddStep)

                elif key in controlKeyMap["changePlantStateFlag"]:
                    self.__plantStateFlag = False
                elif key in controlKeyMap["changeGunStateFlag"]:
                    self.__gunStateFlag = False

            except:
                pass

        keyboard.Listener(
            on_press=onPress,
            on_release=onRelease,
            daemon=True).start()


if __name__ == '__main__':
    print("Online-Cup remote control v1.1b")
    robot = RemoteRobot()
    try:
        while True:
            if not robot.isConnected:
                try:
                    if 'IP' in globals():
                        ip = IP
                    else:
                        print("Enter the ip address: ")
                        ip = input().replace(' ', '')

                    if 'PORT' in globals():
                        port = PORT
                    else:
                        print("Enter the port: ")
                        port = input().replace(' ', '')

                    if checkHost((ip, port)) is False:
                        continue

                    print("Enter the key: ")
                    key = int(input().replace(' ', ''))
                    if (key > 0xFFFF) or (key < 0):
                        raise ValueError("Invalid key format")

                    robot.connect(ip, int(port), key)
                    info()
                except Exception as e:
                    print("Connection failed: ", str(e))
            time.sleep(1)
    except KeyboardInterrupt:
        if robot.isConnected:
            robot.disconnect()
        time.sleep(1)
        print("The program has successfully shut down")
        exit()
