#!/usr/bin/env python3
# -*- coding:utf-8 vi:ts=4:noexpandtab
# Simple RTSP server. Run as-is or with a command-line to replace the default pipeline

import sys
import gi
import RPi.GPIO as GPIO
import os
import subprocess
import time
from PIL import Image       # библиотеки для рисования на дисплее
from PIL import ImageDraw
from PIL import ImageFont
import Adafruit_SSD1306

#Возвращает ip
def getIP():
        #cmd = 'hostname -I | cut -d\' \' -f1'
        #ip = subprocess.check_output(cmd, shell = True) #получаем IP
        res = os.popen('hostname -I | cut -d\' \' -f1').readline().replace('\n','') #получаем IP, удаляем \n
        return res

# функция вывода сообщений на экран
def print_display(line, y, shutdown):
	if shutdown == 0:
		draw.text((0, y), line, font=font, fill=255)  # формируем текст
	if shutdown == 1:
		draw.rectangle((0, 0, width, height), outline=0, fill=0)  # прямоугольник, залитый черным - очищаем дисплей
		draw.text((0, y), line, font=font, fill=255)  # формируем текст

	disp.image(image)  # записываем изображение в буффер
	disp.display()  # выводим его на экран

if __name__ == '__main__':
    disp = Adafruit_SSD1306.SSD1306_128_64(rst=None)
    disp.begin()  # запускаем дисплей
    disp.clear()  # очищаем буффер изображения
    width, height = disp.width, disp.height  # получаем высоту и ширину дисплея
    image = Image.new('1', (width, height))  # создаем изображение из библиотеки PIL для вывода на экран. 1 = картинка черно-белая, далее размер изображения
    draw = ImageDraw.Draw(image)  # создаем объект, которым будем рисовать
    font = ImageFont.load_default()  # загружаем стандартный шрифт
    draw.rectangle((0, 0, width, height), outline=0, fill=0)  # прямоугольник, залитый черным - очищаем дисплей
    i = 0
    while (i < 40):
        print_display(line="i:" + str(i), y=0, shutdown=1)
        print_display(line="ip:" + getIP(), y=9, shutdown=0)
        time.sleep(1)
        i += 1
