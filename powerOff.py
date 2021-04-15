#!/usr/bin/env python3
# -*- coding:utf-8 vi:ts=4:noexpandtab
# Simple RTSP server. Run as-is or with a command-line to replace the default pipeline


import RPi.GPIO as GPIO
from PIL import Image       # библиотеки для рисования на дисплее
from PIL import ImageDraw
from PIL import ImageFont
import Adafruit_SSD1306



if __name__ == '__main__':
    disp = Adafruit_SSD1306.SSD1306_128_64(rst=None)
    disp.begin()  # запускаем дисплей
    disp.clear()  # очищаем буффер изображения
    width, height = disp.width, disp.height  # получаем высоту и ширину дисплея
    image = Image.new('1', (width, height))  # создаем изображение из библиотеки PIL для вывода на экран. 1 = картинка черно-белая, далее размер изображения
    draw = ImageDraw.Draw(image)  # создаем объект, которым будем рисовать
    draw.rectangle((0, 0, width, height), outline=0, fill=0)  # прямоугольник, залитый черным - очищаем дисплей

    font = ImageFont.load_default();

    draw.ellipse((0,0,40,64),outline=255, fill = 255)
    draw.ellipse((9, 9, 31, 55), outline=0, fill=0)

    draw.rectangle((52, 18, 61, 64), outline=255, fill=255)
    draw.rectangle((46, 35, 68, 42), outline=255, fill=255)
    i = 1
    while i < 11:
        draw.arc([51+i,0,79+i,37],180,0,fill=255)
        i = i + 1

    x = 39
    draw.rectangle((54+x, 18, 63+x, 64), outline=255, fill=255)
    draw.rectangle((48+x, 35, 70+x, 42), outline=255, fill=255)
    i = 1
    while i < 11:
        draw.arc([53 + i +x, 0, 81 + i +x, 37], 180, 0, fill=255)
        i = i + 1

    disp.image(image)
    disp.display() # вывод текста


