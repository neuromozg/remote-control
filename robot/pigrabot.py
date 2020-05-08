import threading
import time

try:
    import Adafruit_SSD1306  # sudo pip3 install Adafruit-SSD1306
    display = Adafruit_SSD1306.SSD1306_128_64(rst=None)  # создаем обект для работы c OLED дисплеем 128х64
except:
    display = None

_SHUNT_OHMS = 0.01  # значение сопротивления шунта на плате EduBot
_MAX_EXPECTED_AMPS = 2.0


class Registers:
    """ Класс, хранящий регистры драйвера моторов """
    REG_WHY_IAM = 0x00  # регистр, возвращающий 42
    REG_ONLINE = 0x01
    REG_SERVO_0 = 0x02
    REG_SERVO_1 = 0x03
    REG_SERVO_2 = 0x04
    REG_SERVO_3 = 0x05
    REG_DIR_0 = 0x06  # направление вращения мотора A
    REG_PWM_0 = 0x07  # ШИМ задаваемый мотору А в режиме WORK_MODE_PWM_I2C
    REG_DIR_1 = 0x08  # направление вращения мотора B
    REG_PWM_1 = 0x09  # ШИМ задаваемый мотору B в режиме WORK_MODE_PWM_I2C
    REG_BEEP = 0x0A


class Pigrabot:
    def __init__(self, bus, addr=0x27):
        self._bus = bus  # шина i2c
        self._addr = addr  # адресс устройства
        self.online = False  # флаг, определяющий шлется онлайн метка или нет
        self.__exit = False  # метка выхода из потоков

    def whoIam(self):
        """ Должен вернуть 42 """
        return self._bus.read_byte_data(self._addr, Registers.REG_WHY_IAM)

    def _setDirection0(self, direction):
        """ Устанавливает направление вращения мотора 0 """
        self._bus.write_byte_data(self._addr, Registers.REG_DIR_0, direction)
        time.sleep(0.001)

    def _setDirection1(self, direction):
        """ Устанавливает направление вращения мотора 1 """
        self._bus.write_byte_data(self._addr, Registers.REG_DIR_1, direction)
        time.sleep(0.001)

    def setPwm0(self, pwm):
        """ Устанавливает скорость через параметры шима """
        pwm = min(max(-255, pwm), 255)  # проверяем значение pwm
        self._setDirection0(int(pwm > 0))
        self._bus.write_byte_data(self._addr, Registers.REG_PWM_0, abs(pwm))
        time.sleep(0.001)

    def setPwm1(self, pwm):
        """ Устанавливает скорость через параметры шима """
        pwm = min(max(-255, pwm), 255)  # проверяем значение pwm
        self._setDirection1(int(pwm > 0))
        self._bus.write_byte_data(self._addr, Registers.REG_PWM_1, abs(pwm))
        time.sleep(0.001)

    def setServo0(self, pos):
        """ Установка позиции 0 сервы """
        pos = min(max(0, pos), 125)  # проверяем значение pos
        self._bus.write_byte_data(self._addr, Registers.REG_SERVO_0, pos)
        time.sleep(0.001)

    def setServo1(self, pos):
        """ Установка позиции 1 сервы """
        pos = min(max(0, pos), 125)  # проверяем значение pos
        self._bus.write_byte_data(self._addr, Registers.REG_SERVO_1, pos)
        time.sleep(0.001)

    def setServo2(self, pos):
        """ Установка позиции 2 сервы """
        pos = min(max(0, pos), 125)  # проверяем значение pos
        self._bus.write_byte_data(self._addr, Registers.REG_SERVO_2, pos)
        time.sleep(0.001)

    def setServo3(self, pos):
        """ Установка позиции 3 сервы """
        pos = min(max(0, pos), 125)  # проверяем значение pos
        self._bus.write_byte_data(self._addr, Registers.REG_SERVO_3, pos)
        time.sleep(0.001)

    def beep(self):
        """ Бибикнуть """
        self._bus.write_byte_data(self._addr, Registers.REG_BEEP, 3)
        time.sleep(0.001)

    def __onlineThread(self):
        """ поток отправляющий онлайн метки """
        while not self.__exit:
            try:
                if self.online:  # если включена посылка онлайн меток
                    self._bus.write_byte_data(self._addr, Registers.REG_ONLINE, 1)
            except:
                pass
            time.sleep(1)

    def start(self):
        threading.Thread(target=self.__onlineThread, daemon=True).start()  # включаем посылку онлайн меток

    def exit(self):
        self.__exit = True
