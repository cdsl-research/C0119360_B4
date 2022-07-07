import time

from machine import Pin, I2C, Timer, SDCard
from ina219 import INA219
import sys
import ssd1306
import ds1307
import os

""" パラメータ """
# i2c関係
I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
SENSER_I2C_ADDRESS = 64
SENSER2_I2C_ADDRESS = 65
DISPLAY_I2C_ADDRESS = 60

# 電流計測モジュールに付いている抵抗
# R100 = 0.1Ω
SHUNT_OHMS = 0.1

# PIN ダウンロード用
DOWNROAD_PIN = 32

# 平均計算までのカウント
# 10で1秒毎に記録
# 5で0.5秒毎に記録
# 2で0.2秒毎に記録
WRITE_CNT = 2

""" パラメータ(終わり) """


class OLED_DISPLAY():

    # 128*64 ディスプレイ表示用
    def __init__(self,i2c):
        self.display = ssd1306.SSD1306_I2C(128, 64, i2c)
        self.blinking_control_flag = False

    def show_display(self, arr, arr2):
        #   電圧と電流を表示する
        #   arrは電圧と電流のタプル
        self.display.fill_rect(0, 0, 106, 40, 0) 
        self.display.text("1 %.3f v" % (arr[0]), 0, 0)
        self.display.text("  %.3f mA" % (arr[1]), 0, 10)
        self.display.text("2 %.3f v" % (arr2[0]), 0, 20)
        self.display.text("  %.3f mA" % (arr2[1]), 0, 30)
        #self.display.text("%.3f mW" % (arr[0]*arr[1]), 0, 20)
        self.display.show()

    def sd_show(self,sd_mount):
        #   sdカードの状態をOLEDに表示
        if(sd_mount):
            self.display.fill_rect(106, 0, 20, 20, 1) 
            self.display.text("SD", 108, 2, 0)
            self.display.text("OK", 108, 10, 0)
            self.display.show()
        else:
            self.display.fill_rect(106, 0, 20, 20, 0) 
            self.display.text("SD", 108, 2, 1)
            self.display.text("NG", 108, 10, 1)
            self.display.show()
            return

    def write_show(self,write_flag):
        #   sdカードの状態をOLEDに表示
        if(write_flag):
            if(self.blinking_control_flag):
                background_color = 0
                char_color = 1
                self.blinking_control_flag = False
            else:
                background_color = 1
                char_color = 0
                self.blinking_control_flag = True
                
            self.display.fill_rect(100, 55, 28, 9, background_color) 
            self.display.text("REC", 100, 56, char_color)
            self.display.show()
        else:
            self.display.fill_rect(100, 55, 28, 9, 0) 
            self.display.text("SB", 100, 56, 1)
            self.display.show()
            return

    def file_cnt_show(self,cnt):
        #   ファイル数の表示
        self.display.fill_rect(100, 43, 18, 10, 0) 
        self.display.text(str(cnt), 100, 43)

    
    def timeshow(self, now):
        self.display.fill_rect(0, 40, 100, 60, 0) 
        self.display.text("%4d/%d/%d" % (now[0],now[1],now[2]), 0, 40)
        self.display.text("%2d:%02d:%02d" % (now[4],now[5],now[6]), 0, 50)
        self.display.show()

    def show_display_err(self):
        #   電圧電流を---にする
        self.display.fill_rect(0, 0, 100, 30, 0) 
        self.display.text("--- v", 0, 0)
        self.display.text("--- mA", 0, 10)
        self.display.text("--- mW", 0, 20)
        self.display.show()

    def display_download_mode(self):
        self.display.fill(1) 
        self.display.text("download", 0, 0, 0)
        self.display.text("pin: " + str(DOWNROAD_PIN), 0, 20, 0)
        self.display.show()
        
class SD_Card():
    # SDカード記録用 
    def __init__(self):
        self.mount = False
        self.sd_mount_try_cnt = 0
        self.sd = SDCard(slot=2)
        self.file_cnt = -1

    def sd_mount_try(self):
        # sdカードのマウントを行う
        if(self.mount):
            return True

        if(self.sd_mount_try_cnt >= 5):
            self.sd_mount_try_cnt = 0
            try:
                self.sd = SDCard(slot=2)
            except Exception:
                pass
        
        self.sd_mount_try_cnt += 1
        
        try:
            os.mount(self.sd, '/sd')
            print("sd mount")
            self.mount = True
            self.get_file_cnt()
            return True
        except Exception as e:
            print("sd err")
            self.mount = False
            return False

    def sd_check(self):
        if(not self.mount):
            return False
        try:
            with open('/sd/esp32.txt', 'w') as f:
                f.write("esp_test")
            with open("sd/esp32.txt", "r") as f:
                s = f.read()
                if("esp_test" in s):
                    self.mount = True
                    return True
                else:
                    self.mount = False
                    return False
        except Exception:
            self.mount = False
            return False

    def sd_write(self,file_name,time_str,arr,arr2):
        # 電流・電圧の書き込み
        try:
            with open(file_name, 'a') as f:
                f.write('%s,%.3f,%.3f,%.3f,%.3f\n' % (time_str,arr[0],arr[1],arr2[0],arr2[1]))
                return True
        except Exception:
            self.mount_flag = False
            return False

    def get_file_cnt(self):
        if(self.mount):
            self.file_cnt = len(os.listdir("/sd/"))
            return self.file_cnt
        else:
            self.file_cnt = -1
            return -1
        

def calc_avg(arr):
    #   配列から電流と電圧の平均を求める    
    sum_voltage = 0
    sum_current = 0
    for data in arr:
        sum_voltage += data[0]
        sum_current += data[1]
    avg_voltage = sum_voltage / len(arr)
    avg_current = sum_current / len(arr)
    return (avg_voltage, avg_current)

p_scl = Pin(I2C_SCL_PIN, Pin.IN, Pin.PULL_UP)
p_sda = Pin(I2C_SDA_PIN, Pin.IN, Pin.PULL_UP)
i2c = I2C(scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
downroad_pin = Pin(DOWNROAD_PIN, Pin.IN, Pin.PULL_UP)

ina1 = INA219(SHUNT_OHMS, i2c, address=SENSER_I2C_ADDRESS)
ina2 = INA219(SHUNT_OHMS, i2c, address=SENSER2_I2C_ADDRESS)
ina1.configure()
ina2.configure()

oled = OLED_DISPLAY(i2c)
ds = ds1307.DS1307(i2c)
sd = SD_Card()

# 平均算出用
cnt = 1
temporary1 = []
temporary2 = []

# エラー表示処理用
err_flag = False

# SDカード書き込み用
file_name = ""
write_flag = False

# ボタン処理(長押し等)
button_cnt = 0

def callback(t):
    # 100ms毎に実行される
    global cnt, temporary1, temporary2, oled, err_flag, ds, file_name ,button_cnt ,write_flag, sd
    try:
        temporary1.append((ina1.voltage(), ina1.current()))
        temporary2.append((ina2.voltage(), ina2.current()))
        if(err_flag):
            err_flag = False
            print('ok')
    except Exception:
        print('ina219 err')
        oled.show_display_err()
        err_flag = True

    now = ds.datetime()
    oled.timeshow(now)
    
    if(downroad_pin.value()):
        button_cnt = 0
    else:
        button_cnt += 1

    oled.file_cnt_show(sd.file_cnt)

    if(button_cnt == 2):
        if(write_flag):
            write_flag = False
        else:
            if(sd.mount):
                file_cnt = sd.get_file_cnt()
                now = ds.datetime()
                file_name = "/sd/%d_%4d%02d%02d_%2d%02d%02d.csv" % (file_cnt, now[0],now[1],now[2],now[4],now[5],now[6])
                write_flag = True
                print(file_name)

    if(cnt == WRITE_CNT):
        cnt = 0
        avg_data_1 = calc_avg(temporary1)
        avg_data_2 = calc_avg(temporary2)

        time_str = "%4d/%d/%d %2d:%02d:%02d" % (now[0],now[1],now[2],now[4],now[5],now[6])
        print("sensor1 %.3f,%.3f" % (avg_data_1[0], avg_data_1[1]))
        print("sensor2 %.3f,%.3f" % (avg_data_2[0], avg_data_2[1]))
        oled.show_display(avg_data_1,avg_data_2)
        temporary1 = []
        temporary2 = []

        if(not sd.sd_check()):
            write_flag = False

        if(write_flag):
            if(sd.sd_write(file_name,time_str,avg_data_1,avg_data_2)):
                print("ok")
            else:
                print("ng")
                write_flag = False

        sd.sd_mount_try()
        
        oled.sd_show(sd.mount)
        oled.write_show(write_flag)


    cnt += 1


if(not downroad_pin.value()):
    oled.display_download_mode()
    sys.exit()

tim = Timer(4)
tim.init(period=100, callback=callback)

while True:
    pass

