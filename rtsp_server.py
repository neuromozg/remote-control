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

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib

loop = GLib.MainLoop()
#GLib.threads_init()
Gst.init(None)

class FrontCamFactory(GstRtspServer.RTSPMediaFactory):
	def __init__(self):
		GstRtspServer.RTSPMediaFactory.__init__(self)

	def do_create_element(self, url):
		pipeline_str = "( v4l2src device=/dev/video2 ! video/x-raw, width=640, height=360, framerate=10/1, pixel-aspect-ratio=1/1 ! \
				gdkpixbufoverlay location=aim2.png offset-x=265 offset-y=90 overlay-height=0 overlay-width=0 ! videorate ! \
				v4l2h264enc ! rtph264pay name=pay0 pt=96 \
				alsasrc device=plughw:1,0 ! audio/x-raw, rate=16000, channels=1 ! audiochebband mode=band-pass lower-frequency=1000 upper-frequency=4000 type=2 ! audioconvert ! opusenc ! rtpopuspay name=pay1 )"

		print(pipeline_str)
		return Gst.parse_launch(pipeline_str)

class PotatoCamFactory(GstRtspServer.RTSPMediaFactory):
        def __init__(self):
                GstRtspServer.RTSPMediaFactory.__init__(self)

        def do_create_element(self, url):
                pipeline_str = "( v4l2src device=/dev/video0 ! image/jpeg, width=320, height=240, framerate=20/1, pixel-aspect-ratio=1/1 ! \
                                jpegparse ! rtpjpegpay name=pay0 pt=96 )"
                print(pipeline_str)
                return Gst.parse_launch(pipeline_str)


# функция вывода сообщений на экран
def print_display(line, y, shutdown):
	if shutdown == 0:
		draw.text((0, y), line, font=font, fill=255)  # формируем текст
	if shutdown == 1:
		draw.rectangle((0, 0, width, height), outline=0, fill=0)  # прямоугольник, залитый черным - очищаем дисплей
		draw.text((0, y), line, font=font, fill=255)  # формируем текст

	disp.image(image)  # записываем изображение в буффер
	disp.display()  # выводим его на экран

#Возвращает ip
def getIP():
        #cmd = 'hostname -I | cut -d\' \' -f1'
        #ip = subprocess.check_output(cmd, shell = True) #получаем IP
        res = os.popen('hostname -I | cut -d\' \' -f1').readline().replace('\n','') #получаем IP, удаляем \n
        return res


class GstServer():
	def __init__(self):
		self.server = GstRtspServer.RTSPServer()

		frontCam = FrontCamFactory()
		frontCam.set_shared(True)

		potatoCam = PotatoCamFactory()
		potatoCam.set_shared(True)

		m = self.server.get_mount_points()
		m.add_factory("/front", frontCam)
		m.add_factory("/potato", potatoCam)

		self.server.attach(None)
		# Рисование
		port_FrontServer = self.server.get_bound_port()
		print('RTSP server started: rtsp://%s:%d/front' % (getIP(), port_FrontServer))
		print('RTSP server started: rtsp://%s:%d/potato' % (getIP(), port_FrontServer))
		print_display(line="Robot started", y=0, shutdown=0)
		print_display(line="ip:" + getIP(), y=8, shutdown=0)
		print_display(line="RTSP server started", y=16, shutdown=0)

if __name__ == '__main__':

	disp = Adafruit_SSD1306.SSD1306_128_64(rst=None)
	disp.begin()  # запускаем дисплей
	disp.clear()  # очищаем буффер изображения
	width, height = disp.width, disp.height  # получаем высоту и ширину дисплея
	image = Image.new('1', (width, height))  # создаем изображение из библиотеки PIL для вывода на экран. 1 = картинка черно-белая, далее размер изображения
	draw = ImageDraw.Draw(image)  # создаем объект, которым будем рисовать
	font = ImageFont.load_default()  # загружаем стандартный шрифт
	draw.rectangle((0, 0, width, height), outline=0, fill=0)  # прямоугольник, залитый черным - очищаем дисплей

	s = GstServer()
	loop.run()


