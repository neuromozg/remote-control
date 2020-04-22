#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import sys
import time
import config
import robologger
import argparse

protocolConfig = {
    "startBytes": b'',
    "checksum": "crc16",
    "formatChecksum": 'H',  # 2 байта
    "formatKey": 'H',
    "formatData": 'Hbbbb??'  # 2 байта + 4 байта + 2 байта bool
}

__headFormat = '=' + protocolConfig["formatChecksum"] + protocolConfig["formatKey"]
__packageFormat = __headFormat + protocolConfig["formatData"]


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
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", help="Уровень вывода логов", type=int, choices=[0, 1, 2])
    parser.add_argument("-k", help="Ручной ввод ключа", type=int)
    parser.add_argument("--host", help="Ручной ввод хоста. Формат ввода ip:port", type=str)
    args = parser.parse_args()
    logger = robologger.robologger
    level = robologger.logging.INFO
    if args.v == 0:
        level = robologger.logging.DEBUG_0
    elif args.v == 1:
        level = robologger.logging.DEBUG_1
    elif args.v == 2:
        level = robologger.logging.DEBUG_2
    logger.setLevel(level)

    try:
        if args.k is not None:
            key = args.k
            logger.debug_0("Ключ подключения введен через модификатор: {key}".format(key=key))
        elif config.__dict__.get("KEY") is not None:
            key = config.KEY
            logger.debug_0("Ключ подключения взят из файла настроек config.py: {key}".format(key=key))
        else:
            import random
            key = random.randint(0, 0xFFFF)
            logger.debug_0("Ключ подключения сгенерирован случайно: {key}".format(key=key))

        if (key > 0xFFFF) or (key < 0):
            logger.error("Ошибка генерации ключа: выход из диапазона")
            raise ValueError("Ключ может быть взят только из диапазона [0, 65535]")

        if args.host is not None:
            try:
                ip, port = args.host.replace(' ', '').split(':')
                port = int(port)
                logger.debug_0("Хост введен через модификатор: {host}".format(host=args.host))
            except Exception as e:
                logger.error("Неверный формат введенного хоста: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенного хоста: {e}".format(e=e.__str__()))
        elif config.__dict__.get("SELF_HOST") is not None:
            try:
                ip, port = config.SELF_HOST.replace(' ', '').split(':')
                port = int(port)
                logger.debug_0("Хост взят из файла настроек config.py: {host}".format(host=config.SELF_HOST))
            except Exception as e:
                logger.error("Неверный формат хоста: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат хоста: {e}".format(e=e.__str__()))
        else:
            logger.error("Хост не задан, введите хост через модификатор [--host] или через файл настроек config.py")
            raise ValueError("Хост не задан")

        config.logger = logger

        try:
            logger.debug_0("Попытка инициализации робота")
            config.initializeAll()
            logger.debug_0("Попытка инициализации робота прошла успешно")
        except:
            sys.exit(1)

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3.0)
            sock.bind((ip, port))
        except Exception as e:
            logger.error("Ошибка инициализации сервера: {e}".format(e=e))
            sys.exit(1)

        logger.info("Сервер на роботе запущен: {ip}:{port}".format(ip=ip, port=port))
        logger.info("Ключ подключения: {key}".format(key=key))

        previousStates = [None, None, None, None, None, None]
        actualPackageNum = -1
        while True:
            try:
                rawdata, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
                data = struct.unpack(__packageFormat, rawdata)
                logger.debug_2("Package: crc: {0}, key: {1}, number: {2}, data: {3}".format(*data[:3], data[3:]))
                crc = data[0]
                nkey = data[1]
                if nkey == key:
                    if crc == crc16(rawdata[struct.calcsize(__headFormat):]):
                        packageNum = data[2]
                        if packageNum > actualPackageNum:
                            actualPackageNum = packageNum
                        else:
                            logger.warning("Старый пакет: " + "Package: crc: {0}, key: {1}, number: {2}, data: {3}. Актуальный номер пакета: {4}".format(*data[:3], data[3:], actualPackageNum))

                        data = data[3:]
                        config.robot.online = True
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
                    else:
                        logger.debug_1("Неверная crc-сумма пакета: {ncrc}/{vcrc}".format(ncrc=crc, vcrc=crc16(rawdata[struct.calcsize(__headFormat):])))
                else:
                    logger.debug_1("Неверный ключ пакета: {nkey}/{vkey}".format(nkey=nkey, vkey=key))
            except socket.timeout:
                logger.debug_0("Тайм-аут приема пакета, ожидание новых пакетов, снятие онлайн метки")
                config.robot.online = False
                time.sleep(1)
            except Exception as e:
                logger.error("Ошибка при приеме пакета: {e}".format(e=e))
    except KeyboardInterrupt:
        config.release()
        time.sleep(1)
        sys.exit()
