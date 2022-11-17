import ubluetooth
from micropython import const
import ubinascii
import machine
import sys
from machine import Pin
import time
import esp32
import DS3231micro
from machine import Pin, I2C, UART
from umqtt.simple import MQTTClient
import network
import os

_IRQ_SCAN_RESULT = const(5)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

### パラメータ ###
BLE_USE = False # 位置共有機能の有無
BLE_TIME = 10 #[s]
GPS_PIN = 27

I2C_SCL_PIN = 22
I2C_SDA_PIN = 21
INTERVAL = 2 # min
RTC_SQW_PIN = 32

DOWNROAD_PIN = 33

GPSBPS = 9600 # 通信速度 データシート見て
RXPIN = 16 # GPSのTXとつなぐ
TXPIN = 17 # 使わないので接続しなくてよい

WIFI_CONFIG = [("","")] #SSIDとパスワードのタプル
MQTT_SERVER = "" #接続先MQTTブローカ
### ここまで。 ###

def hex_bytes_to_str(hex_bytes):
    hex_str = hex_bytes.decode()

    return_str = ""
    for i in range(0, len(hex_str), 2):
        char_hex = hex_str[i] + hex_str[i+1]
        return_str+= chr(int(char_hex, 16))

    return return_str

def dmm_to_deg(dmm):
    #DMM形式からDEG形式に変換
    d1 = int(dmm/100)
    d2 = (dmm - d1*100) / 60
    dmm = d1 + d2
    return dmm

class GPS_BLE:
    def __init__(self):
        self.ble = ubluetooth.BLE()
        if self.ble.active() == False:
            self.ble.active(True)
        self.ble.irq(self.bt_irq)
        self.positioning_cnt_path = "positioning_time.txt"
        self.my_positioning_cnt = self.get_my_positioning_cnt()

    def get_my_positioning_cnt(self):
        # 測位回数の取得
        # 累計測位回数の読込
        if(self.positioning_cnt_path in os.listdir()):
            f = open(self.positioning_cnt_path)
            my_positioning_cnt = int(f.read())
            f.close()
        else:
            my_positioning_cnt = 0
        print("POSITIONING : " + str(my_positioning_cnt))
        return my_positioning_cnt

    def my_positioning_cnt_up(self):
        f = open(self.positioning_cnt_path, 'w')
        f.write(str(self.my_positioning_cnt + 1))
        f.close()
        # 測位回数を増やす

    def adv(self):
        print("ble_advertise_start")
        send_str = "GPS," + str(self.my_positioning_cnt)
        send_data = send_str.encode()
        self.ble.gap_advertise(100 * 1000 , adv_data=send_data)

    def scan(self):
        print("ble_scan_start")
        self.ble.gap_scan(0,128000,11250) 

    def scan_stop(self):
        print("ble_scan_stop")
        self.ble.gap_scan(None)

    def adv_stop(self):
        print("ble_adv_stop")
        self.ble.gap_advertise(None)

    def disconnect(self,conn_handle):
        print("ble_disconnect")
        self.ble.gap_disconnect(conn_handle)
    
    def bt_irq(self, event, data):        
        if event == _IRQ_SCAN_RESULT:
            # BLEスキャンの結果
            addr_type, addr, connectable, rssi, adv_data = data
            adv_data_str = hex_bytes_to_str(ubinascii.hexlify(adv_data))

            if adv_data_str.startswith("GPS"):
                print("GPS")
                your_address_str = ubinascii.hexlify(addr).decode()
                your_id_str = your_address_str[6:]
                your_positioning_cnt = int(adv_data_str.split(",")[1])

                if(self.my_positioning_cnt <= your_positioning_cnt):
                    # 測位回数の少ない機器に接続要求を送る
                    self.ble.gap_connect(addr_type, addr, 1000)
            else:
                print(".",end="")

        if event == _IRQ_CENTRAL_CONNECT:
            # 測位回数が自分より少ない機器から接続(請負)
            self.scan_stop()
            self.adv_stop()
            conn_handle, _, addr = data
            address_str = ubinascii.hexlify(addr).decode()
            your_id_str = address_str[6:]
            print("\nble_CENTRAL_CONNECT ID: " + your_id_str)
            if not your_id_str in addr_arr:
                addr_arr.append(your_id_str)
            time.sleep_ms(300) # 通信用
            self.ble.gap_disconnect(conn_handle)

        if event == _IRQ_CENTRAL_DISCONNECT:
            # 測位回数が自分より少ない機器と切断(請負)
            conn_handle, _, _ = data
            print("\nble_CENTRAL_DISCONNECT" , conn_handle)
            self.adv()
        
        if event == _IRQ_PERIPHERAL_CONNECT:
            # 測位回数が少ない機器と接続(任せる)
            self.scan_stop()
            print("\nble_PERIPHERAL_CONNECT")
            conn_handle, addr_type, addr = data
            self._conn_handle = conn_handle
            
        if event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, _, _ = data
            # 測位回数が少ない機器と切断(任せる)
            print("ble_PERIPHERAL_DISCONNECT")
            deep_sleep()
        
def download():
    # 書き込み用
    downroad_pin = Pin(DOWNROAD_PIN, Pin.IN, Pin.PULL_UP)
    if(downroad_pin.value()):
        sys.exit()
    
def deep_sleep():
    # RTCと通信してスリープに入る
    rtc = DS3231micro.DS3231(I2C_SCL_PIN, I2C_SDA_PIN)

    now_min = rtc.getDateTime()[5]
    timer_min = INTERVAL * (1 + int(now_min / INTERVAL))
    if(timer_min == 60): timer_min = 0

    rtc.resetAlarmFlag(1)
    rtc.setAlarm1(0, 0, timer_min, 0, alarmType = "everyHour")
    rtc.turnOnAlarmIR(1)

    wake_up_pin = Pin(RTC_SQW_PIN, mode = Pin.IN)
    esp32.wake_on_ext0(pin = wake_up_pin, level = esp32.WAKEUP_ALL_LOW)  
    print("timer :" + str(timer_min))
    print(rtc.getDateTime())
    wake_up_pin.value()

    machine.deepsleep()
    pass

def ble_time_out(t):
    # bleアドバタイズ時間の終了
    global gps_ble,timer
    gps_ble.my_positioning_cnt_up()
    timer.deinit()
    print("ble_time_out")
    gps_ble.adv_stop()
    gps_ble.scan_stop()
    positioning_and_send()
    deep_sleep()


def send_data(mqtt_server,me_id_str,send_data):
    # 送信
    print("SEND_DATA")
    wifi_connect(WIFI_CONFIG)
    mqtt = MQTTClient(me_id_str, mqtt_server) 
    mqtt.connect()
    mqtt.publish("test", send_data)
    time.sleep(2)
    print("SEND_OK")

def gps_get(enable = True):
    # 位置測位
    if enable:
        print("GPS_GET")
        uart = UART(1, GPSBPS, tx=TXPIN, rx=RXPIN)
        uart.init(GPSBPS, bits=8, parity=None, stop=1, tx=TXPIN, rx=RXPIN)

        gps_v_pin.on()

        while True:
            try:
                sp = uart.readline()
                if not sp == None:
                    
                    sp = str(sp)
                    sp = sp.split(',')

                    if sp[0][3:8] == 'GPRMC':
                        if(sp[2] == "V"):
                            print("GPS測位失敗")
                        else:
                            print("GPS測位")
                            latitude_dmm = float(sp[3]) #緯度
                            if(sp[4] != "A"): latitude_dmm * -1
                            longitude_dmm = float(sp[5]) #経度
                            if(sp[6] != "E"): longitude_dmm * -1
                        
                            lat = dmm_to_deg(latitude_dmm)
                            lon = dmm_to_deg(longitude_dmm)
                            break
            except Exception as e:
                print(e)

        gps_v_pin.off()
    else:
        print("GPS_GET(debag)")
        gps_v_pin.on()
        time.sleep(5)
        lat = "35.658584"
        lon = "139.7454316"
        gps_v_pin.off()

    print("GPS_OK")

    return (lat,lon)

def positioning_and_send():
    # 位置測位と送信
    location = gps_get(True)

    print("SEND_DATA")
    data = me_id_str + "," + str(location[0]) + "," + str(location[1])

    if BLE_USE:
        print(addr_arr)
        for id in addr_arr:
            data = data + "," + id

    print(data)

    send_data(MQTT_SERVER,me_id_str,data)

def wifi_connect(wifi_config):
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)

        scandata = sta_if.scan() 

        for scan in scandata:
            for config in wifi_config:
                if(scan[0].decode() == config[0]):
                    sta_if.connect(config[0], config[1])

        while not sta_if.isconnected():
            pass
    print('connected: ' , sta_if.config('essid'))
    print('network config:' , sta_if.ifconfig())

if __name__ == "__main__":
    download()
    # GPS電源関係
    gps_v_pin = machine.Pin(GPS_PIN, machine.Pin.OUT)
    gps_v_pin.off()

    # BLE 有効
    ble = ubluetooth.BLE()
    if ble.active() == False:
        ble.active(True)

    # BLE MACアドレスから機器IDを生成
    address_str = ubinascii.hexlify(ble.config("mac")[1]).decode()
    me_id_str = address_str[6:]
    print("GPS_ID : " + me_id_str)

    if BLE_USE:
        # 変数初期化
        addr_arr = [] # 通信を行った機器を入れる

        # BLE通信
        gps_ble = GPS_BLE()
        gps_ble.adv()
        gps_ble.scan()

        # BLE送信タイマー
        timer = machine.Timer(4)
        timer.init(period=BLE_TIME*1000,mode=timer.ONE_SHOT,callback=lambda t:ble_time_out(t))

    else:
        ble.active(False)
        positioning_and_send()
        deep_sleep()