import prog.config as config
import prog.net as net

import time
import ntptime
from machine import Pin, Timer, RTC

def time1000ms(tim):
    global led,led2
    now_sec = rtc.datetime()[6]
    print(now_sec)
    if(now_sec == 0):
        print("start")
        led2.on()
    if(now_sec == 10):
        print("stop")
        led2.off()

if __name__ == "__main__":
    led = Pin(23,Pin.OUT)
    led2 = Pin(19,Pin.OUT)

    print("power on")

    wifi = net.do_connect(config.NET_CONFIG)
    ntptime.host = "ntp.nict.jp"
    ntptime.settime()

    rtc = RTC()
    rtc.datetime()

    led.on()
    tim = Timer(0)
    tim.init(period=1000, callback=time1000ms)


