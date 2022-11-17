import ubluetooth
from micropython import const
import ubinascii
import machine
import sys
from machine import Pin
import time
import os
import utime

_IRQ_SCAN_RESULT = const(5)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

### パラメータ ###
BLE_TIME = 15 #[s]
INTERVAL = 1 #[s]

MAX_DEVAICES = 8 #[台]

ADV_MS = 100 # 20ms〜10,240msの間で調整(デフォは300)

SCAN_WINDW_MS = 1280
SCAN_INTERVAL_MS = 11.25

AC_PIN = 27

I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
RTC_SQW_PIN = 32

DOWNROAD_PIN = 33

END = 100
### ここまで。 ###

def hex_bytes_to_str(hex_bytes):
    hex_str = hex_bytes.decode()

    return_str = ""
    for i in range(0, len(hex_str), 2):
        char_hex = hex_str[i] + hex_str[i+1]
        return_str+= chr(int(char_hex, 16))

    return return_str

class GPS_BLE:
    def __init__(self,adv_ms):
        self.ble = ubluetooth.BLE()
        if self.ble.active() == False:
            self.ble.active(True)
        self.ble.irq(self.bt_irq)
        self.adv_ms = adv_ms

    def adv(self):
        print("ble_advertise_start")
        send_str = "GPS_M," + str(0)
        send_data = send_str.encode()
        self.ble.gap_advertise(self.adv_ms * 1000 , adv_data=send_data)

    def scan_stop(self):
        self.ble.gap_scan(None)

    def adv_stop(self):
        self.ble.gap_advertise(None)

    def disconnect(self,conn_handle):
        print("dis_connect")
        self.ble.gap_disconnect(conn_handle)
    
    def bt_irq(self, event, data):        
        if event == _IRQ_CENTRAL_CONNECT:
            # 要求元と接続
            self.scan_stop()
            self.adv_stop()
            conn_handle, _, addr = data
            address_str = ubinascii.hexlify(addr).decode()
            your_id_str = address_str[6:]
            print("\nble_CENTRAL_CONNECT ID: " + your_id_str)
            if not your_id_str in addr_arr:
                addr_arr.append(your_id_str)
            print(str(len(addr_arr)) + "/" + str(MAX_DEVAICES))
            time.sleep_ms(300) # 通信用
            
            end_time = utime.ticks_ms()
            print("TIME: " + str((end_time - start_time) / 1000))
            times.append((end_time - start_time) / 1000)

            if(len(addr_arr) >= MAX_DEVAICES):
                timer.deinit()
                write_time(times)
                #cnt_up()
                reset()
            self.ble.gap_disconnect(conn_handle)

        if event == _IRQ_CENTRAL_DISCONNECT:
            # 要求元と接続終了
            conn_handle, _, _ = data
            print("\nble_CENTRAL_DISCONNECT" , conn_handle)
            self.adv()

def download():
    # downloadPIN
    downroad_pin = Pin(DOWNROAD_PIN, Pin.IN, Pin.PULL_UP)
    if(downroad_pin.value()):
        sys.exit()
    
def sleep(sleep_time):
    print("sleep:" + str(sleep_time) + "s")
    time.sleep(sleep_time)

def reset():
    print("reset")
    machine.reset()

def ble_time_out(t):
    timer.deinit()
    print("ble_time_out")
    write_time(times)
    gps_ble.adv_stop()
    gps_ble.scan_stop()
    reset()

def write_time(times):
    print("write")
    data_string = "cnt=" + str(len(times))
    for t in times:
        data_string = data_string + "," + str(t)
    data_string = data_string + "\n"
    print(data_string) 
    f = open("time.txt", 'a')
    f.write(str(data_string))
    f.close()

def read_cnt():
    data_path_str = "cnt.txt"
    if(data_path_str in os.listdir()):
        f = open(data_path_str)
        cnt = int(f.read())
        f.close()
    else:
        print("CREATE : " + data_path_str)
        f = open(data_path_str, 'w')
        f.write(str(0))
        f.close()
        cnt = 0
    print("CNT: " + str(cnt))
    return cnt

def cnt_up():
    data_path_str = "cnt.txt"
    cnt = cnt + 1
    f = open(data_path_str, 'w')
    f.write(cnt)
    f.close()
    print("CNT : " + str(cnt))


if __name__ == "__main__":
    download()

    cnt = read_cnt()

    ac = Pin(AC_PIN, Pin.OUT)
    ac.off()

    sleep(INTERVAL)

    addr_arr = []
    gps_ble = GPS_BLE(ADV_MS)
    gps_ble.adv()

    # タイマー用
    timer = machine.Timer(4)
    timer.init(period=BLE_TIME*1000,mode=timer.ONE_SHOT,callback=lambda t:ble_time_out(t))

    # 電源ON
    ac.on()

    # 立ち上がり待機
    time.sleep_ms(1500)

    # 時間入れる用
    times = []

    # タイム計測
    start_time = utime.ticks_ms()

    while True:
        pass