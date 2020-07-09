#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import struct
import sys
import threading
import time
import config
import robologger
import argparse

try:
    from PIL import Image
    from PIL import ImageFont
    from PIL import ImageDraw

    INFO_DISPLAY_OK = True  # флаг, показывающий, что инициализация всех состовляющих для вывода информации в норме
except ImportError:
    INFO_DISPLAY_OK = False

protocolConfig = {
    "startBytes": b'',
    "checksum": "crc16",
    "formatChecksum": 'H',  # 2 байта
    "formatKey": 'H',
    "formatData": 'Hbbbb??H'  # 2 байта + 4 байта + 2 байта bool + 1 байт
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


class DisplayStates:
    NONE = 0    # дисплей не отрисовывает ничего
    PRE_TIMER = 1   # дисплей отрисовывает таймер до начала подключения
    PRE_ANIMATION = 2   # дисплей отрисовывает анимацию до начала подключения
    SPEED = 3   # дисплей отрисовывает скорость
    TIMER = 4   # дисплей отрисовывает основной таймер
    ANIMATION = 5   # дисплей отрисовывает основную анимацию
    EXIT = 6    # дисплей отрисовывает окончание попытки


if __name__ == '__main__':
    global timer
    global connected
    connected = False  # метка первого подключения
    timer = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument("-v", help="Уровень дебага", type=int, choices=[0, 1, 2])
    parser.add_argument("-k", help="Ручной ввод ключа", type=int)
    parser.add_argument("--host", help="Ручной ввод хоста. Формат ввода ip:port", type=str)
    parser.add_argument("--info", help="Информационная строка вывода на дисплей", type=str)
    parser.add_argument("-t", help="Время попытки в минутах", type=int)
    parser.add_argument("-p", help="Время на подготовку в минутах", type=int)
    parser.add_argument("--preinfo", help="Информационная строка вывода на дисплей перед подключением", type=str)
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
                if port == "random":
                    import random

                    port = random.randint(5000, 5999)
                    logger.debug_0("Порт сгенерирован случайно: {port}".format(port=port))
                else:
                    port = int(port)
                logger.debug_0("Хост введен через модификатор: {host}".format(host=args.host))
            except Exception as e:
                logger.error("Неверный формат введенного хоста: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенного хоста: {e}".format(e=e.__str__()))
        elif config.__dict__.get("SELF_HOST") is not None:
            try:
                ip, port = config.SELF_HOST.replace(' ', '').split(':')
                if port == "random":
                    import random

                    port = random.randint(5000, 5999)
                    logger.debug_0("Порт сгенерирован случайно: {port}".format(port=port))
                else:
                    port = int(port)
                logger.debug_0("Хост взят из файла настроек config.py: {host}".format(host=config.SELF_HOST))
            except Exception as e:
                logger.error("Неверный формат хоста: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат хоста: {e}".format(e=e.__str__()))
        else:
            logger.error("Хост не задан, введите хост через модификатор [--host] или через файл настроек config.py")
            raise ValueError("Хост не задан")

        global info
        if args.info is not None:
            try:
                info = args.info
                logger.debug_0("Строка информации введена через модификатор: {info}".format(info=args.info))
            except Exception as e:
                logger.error("Неверный формат введенной строки информации: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенной строки информации: {e}".format(e=e.__str__()))
        elif config.__dict__.get("INFO") is not None:
            try:
                info = config.INFO
                logger.debug_0("Строка информации взята из файла настроек config.py: {info}".format(info=config.INFO))
            except Exception as e:
                logger.error("Неверный формат введенной строки информации: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенной строки информации: {e}".format(e=e.__str__()))
        else:
            info = None
            logger.debug_0("Строка информации не задана")

        global preinfo
        if args.preinfo is not None:
            try:
                preinfo = args.preinfo
                logger.debug_0("Строка информации (перед подключением) введена через модификатор: {preinfo}".format(preinfo=args.preinfo))
            except Exception as e:
                logger.error("Неверный формат введенной строки информации (перед подключением): {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенной строки информации (перед подключением): {e}".format(e=e.__str__()))
        elif config.__dict__.get("PREINFO") is not None:
            try:
                preinfo = config.PREINFO
                logger.debug_0("Строка информации (перед подключением) взята из файла настроек config.py: {preinfo}".format(preinfo=config.PREINFO))
            except Exception as e:
                logger.error("Неверный формат введенной строки информации (перед подключением): {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенной строки информации (перед подключением): {e}".format(e=e.__str__()))
        else:
            preinfo = None
            logger.debug_0("Строка информации (перед подключением) не задана")

        global attemptTime
        if args.t is not None:
            try:
                attemptTime = args.t
                if (attemptTime < 0) or (attemptTime > 60):
                    raise ValueError("Время попытки должно быть в диапазоне 0-60 минут")
                logger.debug_0("Время попытки введено через модификатор: {t}".format(t=attemptTime))
            except Exception as e:
                logger.error("Неверный формат введенной времени попытки: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенной времени попытки: {e}".format(e=e.__str__()))
        elif config.__dict__.get("ATTEMPT_TIME") is not None:
            try:
                attemptTime = config.ATTEMPT_TIME
                if (attemptTime < 0) or (attemptTime > 60):
                    raise ValueError("Время попытки должно быть в диапазоне 0-60 минут")
                logger.debug_0("Время попытки взято из файла настроек config.py: {t}".format(t=attemptTime))
            except Exception as e:
                logger.error("Неверный формат введенной времени попытки: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенной времени попытки: {e}".format(e=e.__str__()))
        else:
            logger.error("Время попытки не задано, введите его через модификатор [-t] или через файл настроек config.py")
            raise ValueError("Время попытки не задано")

        global preparationTime
        if args.p is not None:
            try:
                preparationTime = args.p
                if (preparationTime < 0) or (preparationTime > 60):
                    raise ValueError("Время для подготовки должно быть в диапазоне 0-60 минут")
                logger.debug_0("Время для подготовки введено через модификатор: {p}".format(p=preparationTime))
            except Exception as e:
                logger.error("Неверный формат введенной времени для подготовки: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенной времени для подготовки: {e}".format(e=e.__str__()))
        elif config.__dict__.get("PREPARATION_TIME") is not None:
            try:
                preparationTime = config.ATTEMPT_TIME
                if (preparationTime < 0) or (preparationTime > 60):
                    raise ValueError("Время для подготовки должно быть в диапазоне 0-60 минут")
                logger.debug_0("Время для подготовки взято из файла настроек config.py: {p}".format(p=preparationTime))
            except Exception as e:
                logger.error("Неверный формат введенной времени для подготовки: {e}".format(e=e.__str__()))
                raise ValueError("Неверный формат введенной времени для подготовки: {e}".format(e=e.__str__()))
        else:
            logger.error("Время для подготовки не задано, введите его через модификатор [-p] или через файл настроек config.py")
            raise ValueError("Время для подготовки не задано")

        config.logger = logger

        try:
            logger.debug_0("Попытка инициализации робота")
            config.initializeAll()
            logger.debug_0("Попытка инициализации робота прошла успешно")
        except:
            sys.exit(1)

        if not INFO_DISPLAY_OK:
            logger.error("Ошибка импорта библиотеки PIL, вывод информации на дисплей не возможен")
        elif config.display is None:
            INFO_DISPLAY_OK = False
            logger.error("Ошибка инициализации дисплея, вывод информации на дисплей не возможен")

        global exitFlag
        global referenceSpeed, referenceSpeedFlag
        global displayState
        exitFlag = False
        referenceSpeed = 0  # справочная скорость, для вывода на дисплей
        referenceSpeedFlag = False
        displayState = DisplayStates.NONE

        def animate():
            """ Функция анимации текста и таймера """
            global timer, exitFlag, info, preinfo, attemptTime, displayState, referenceSpeedFlag, referenceSpeed, connected
            display = config.display
            width, height = display.width, display.height
            image = Image.new('1', (width, height))
            animationFont = ImageFont.truetype("arial.ttf", 52)
            speedTexrFont = ImageFont.truetype("arial.ttf", 24)
            speedFont = ImageFont.truetype("arial.ttf", 35)
            gameOverFont = ImageFont.truetype("arial.ttf", 32)
            draw = ImageDraw.Draw(image)
            draw.rectangle((0, 0, width, height), outline=0, fill=0)
            animationText = info
            preanimationText = preinfo
            if animationText is not None:
                animationMaxWidth, _ = draw.textsize(animationText, font=animationFont)
            if preanimationText is not None:
                preanimationMaxWidth, _ = draw.textsize(preanimationText, font=animationFont)

            changeTextToTimeFlag = False  # флаг переключения анимации текста на время
            animationTimer = 0  # таймер
            timetochange = 25  # время, которое должно пройти для смены режима анимации, в сек.
            timecounter = 0  # вспомогательная переменная, которая переключает режимы анимации
            lastcount = 0  # вспомогатеьная переменная для timecounter
            lastDrawnSecond = 0  # последняя отрисованная секунда, для оптимизации отрисовки времени
            preparationTimeSec = preparationTime * 60
            attemptTimeSec = attemptTime * 60

            speedCount = 0  # вспомогательная переменная для вывода скорости
            offset = 0  # настройка анимации
            velocity = -15
            startpos = width
            pos = startpos

            while True:
                animationTimer = time.time() - timer
                timecounter = animationTimer - lastcount

                if timecounter > timetochange:
                    changeTextToTimeFlag = not changeTextToTimeFlag
                    timecounter = 0
                    lastcount = animationTimer
                    pos = startpos

                if exitFlag:
                    displayState = DisplayStates.EXIT
                elif referenceSpeedFlag and connected and (attemptTimeSec - animationTimer) > 7:
                    speedCount = 0
                    referenceSpeedFlag = False
                    displayState = DisplayStates.SPEED
                elif not connected and not changeTextToTimeFlag:
                    displayState = DisplayStates.PRE_ANIMATION
                elif not connected and changeTextToTimeFlag:
                    displayState = DisplayStates.PRE_TIMER
                elif connected and not changeTextToTimeFlag:
                    displayState = DisplayStates.ANIMATION
                elif connected and changeTextToTimeFlag:
                    displayState = DisplayStates.TIMER
                else:
                    displayState = DisplayStates.NONE

                if displayState == DisplayStates.NONE:
                    time.sleep(0.25)
                    continue

                elif displayState == DisplayStates.PRE_TIMER:
                    if int(animationTimer) != lastDrawnSecond:
                        draw.rectangle((0, 0, width, height), outline=0, fill=0)
                        invtime = preparationTimeSec - animationTimer
                        if invtime < 0:
                            invtime = 0
                        draw.text((0, 0), "%02d:%02d" % (int(invtime // 60), int(invtime % 60)), font=animationFont, fill=255)
                        lastDrawnSecond = int(animationTimer)

                elif displayState == DisplayStates.PRE_ANIMATION:
                    if (preanimationText is None) or (preparationTimeSec - animationTimer) < 15:
                        changeTextToTimeFlag = not changeTextToTimeFlag
                        continue
                    draw.rectangle((0, 0, width, height), outline=0, fill=0)
                    x = pos
                    for i, c in enumerate(preanimationText):
                        if x > width:
                            break
                        if x < -10:
                            char_width, char_height = draw.textsize(c, font=animationFont)
                            x += char_width
                            continue
                        y = offset
                        draw.text((x, y), c, font=animationFont, fill=255)
                        char_width, char_height = draw.textsize(c, font=animationFont)
                        x += char_width
                    pos += velocity
                    if pos < -preanimationMaxWidth:
                        pos = startpos

                elif displayState == DisplayStates.SPEED:
                    if (speedCount > 4) or (attemptTimeSec - animationTimer) < 5:
                        displayState = DisplayStates.ANIMATION
                    draw.rectangle((0, 0, width, height), outline=0, fill=0)
                    draw.text((0, 0), "СКОРОСТЬ:", font=speedTexrFont, fill=255)
                    draw.text((30, 27), "{0}%".format(referenceSpeed), font=speedFont, fill=255)
                    speedCount += 1

                elif displayState == DisplayStates.TIMER:
                    if int(animationTimer) != lastDrawnSecond:
                        draw.rectangle((0, 0, width, height), outline=0, fill=0)
                        invtime = attemptTimeSec - animationTimer
                        if invtime < 0:
                            invtime = 0
                        draw.text((0, 0), "%02d:%02d" % (int(invtime // 60), int(invtime % 60)), font=animationFont, fill=255)
                        lastDrawnSecond = int(animationTimer)

                elif displayState == DisplayStates.ANIMATION:
                    if (animationText is None) or (attemptTimeSec - animationTimer) < 15:
                        changeTextToTimeFlag = not changeTextToTimeFlag
                        continue
                    draw.rectangle((0, 0, width, height), outline=0, fill=0)
                    x = pos
                    for i, c in enumerate(animationText):
                        if x > width:
                            break
                        if x < -10:
                            char_width, char_height = draw.textsize(c, font=animationFont)
                            x += char_width
                            continue
                        y = offset
                        draw.text((x, y), c, font=animationFont, fill=255)
                        char_width, char_height = draw.textsize(c, font=animationFont)
                        x += char_width
                    pos += velocity
                    if pos < -animationMaxWidth:
                        pos = startpos

                elif displayState == DisplayStates.EXIT:
                    draw.text((16, 0), "GAME", font=gameOverFont, fill=255)
                    draw.text((16, 32), "OVER", font=gameOverFont, fill=255)
                    display.image(image)
                    display.display()
                    time.sleep(0.25)
                    break

                display.image(image)
                display.display()
                time.sleep(0.25)


        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(3.0)
            sock.bind((ip, port))
        except Exception as e:
            logger.error("Ошибка инициализации сервера: {e}".format(e=e))
            sys.exit(1)

        logger.info("Сервер на роботе запущен: {ip}:{port}".format(ip=ip, port=port))
        logger.info("Ключ подключения: {key}".format(key=key))

        if INFO_DISPLAY_OK:
            threading.Thread(target=animate, daemon=True).start()
            logger.info("Анимация на дисплее запущена".format(key=key))

        print(" ")
        print("port: ", port)
        print("key: ", key)
        print(" ")

        previousStates = [None, None, None, None, None, None, None]
        actualPackageNum = -1
        timer = time.time()
        while True:
            try:
                if not connected:   # если еще не было подключения
                    if (time.time() - timer) > preparationTime * 60:
                        logger.info("Попытки подключения не было, произвожу отключение сервера...")
                        break
                elif (time.time() - timer) > attemptTime * 60:
                    logger.info("Попытка закончена, произвожу отключение сервера...")
                    break
                rawdata, addr = sock.recvfrom(1024)  # buffer size is 1024 bytes
                data = struct.unpack(__packageFormat, rawdata)
                logger.debug_2("Package: crc: {0}, key: {1}, number: {2}, data: {3}".format(*data[:3], data[3:]))
                crc = data[0]
                nkey = data[1]
                if nkey == key:
                    if crc == crc16(rawdata[struct.calcsize(__headFormat):]):
                        if not connected:
                            config.beep()
                            connected = True
                            timer = time.time()
                        packageNum = data[2]
                        if packageNum > actualPackageNum:
                            actualPackageNum = packageNum
                        else:
                            logger.warning(
                                "Старый пакет: " + "Package: crc: {0}, key: {1}, number: {2}, data: {3}. Актуальный номер пакета: {4}".format(
                                    *data[:3], data[3:], actualPackageNum))

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
                        if data[6] != previousStates[6]:
                            referenceSpeedFlag = True
                            referenceSpeed = data[6] & 0x7F
                        previousStates = data[:]
                    else:
                        logger.debug_1("Неверная crc-сумма пакета: {ncrc}/{vcrc}".format(ncrc=crc, vcrc=crc16(
                            rawdata[struct.calcsize(__headFormat):])))
                else:
                    logger.debug_1("Неверный ключ пакета: {nkey}/{vkey}".format(nkey=nkey, vkey=key))
            except socket.timeout:
                logger.debug_0("Тайм-аут приема пакета, ожидание новых пакетов, снятие онлайн метки")
                config.robot.online = False
                time.sleep(1)
            except Exception as e:
                logger.error("Ошибка при приеме пакета: {e}".format(e=e))

        exitFlag = True
        config.beep()
        time.sleep(0.1)
        config.release()
        time.sleep(1)
        logger.info("Сервер успешно завершил свою работу")
        sys.exit()
    except KeyboardInterrupt:
        exitFlag = True
        config.beep()
        time.sleep(0.1)
        config.release()
        time.sleep(1)
        logger.info("Сервер успешно завершил свою работу")
        sys.exit()
