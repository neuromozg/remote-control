Образ ОС для Raspberry Pi
https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2021-03-25/2021-03-04-raspios-buster-armhf-lite.zip

Для корректной работы с необходимо настроить ОС Raspbian запустив  
```$ sudo raspi-config```  
В меню выбрать  
`Interfacing Options -> SSH -> Yes`  
`Interfacing Options -> I2C -> Yes`  
`Interfacing Options -> Camera -> Yes`  
`Advanced Options -> Expand file system -> Yes`  

Перезагрузить систему

Обновить пакеты  
```$ sudo apt update && sudo apt upgrade -y```

Пакеты необходимые для работы приложения на роботе  
```$ sudo apt install libgstreamer1.0-0 gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav gstreamer1.0-doc gstreamer1.0-tools gstreamer1.0-alsa gstreamer1.0-rtsp gir1.2-gst-rtsp-server-1.0 python3-pip python3-gi rpi.gpio i2c-tools python3-smbus git```

```$ sudo pip3 install pillow Adafruit_SSD1306```

Установка репозитория проекта
```$ git clone https://github.com/neuromozg/remote-control.git```
