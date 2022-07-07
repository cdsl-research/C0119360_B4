import ubluetooth
from micropython import const
import ubinascii
from machine import Pin
import sys

_IRQ_SCAN_RESULT = const(5)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

DOWNROAD_PIN = 23

ADV_MS = 100 # 20ms〜10,240msの間で調整(デフォは300)

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
    
    def set_cnt(self,cnt):
        self.cnt = cnt
    
    def scan(self):
        print("ble_scan_start")
        self.ble.gap_scan(0,128000,11250) 

    def scan_stop(self):
        self.ble.gap_scan(None)
    
    def bt_irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, connectable, rssi, adv_data = data
            adv_data_str = hex_bytes_to_str(ubinascii.hexlify(adv_data))

            if adv_data_str.startswith("GPS_M"):
                print("GPS_M")
                self.ble.gap_connect(addr_type, addr, 1000)
            else:
                print(".",end="")
        
        if event == _IRQ_PERIPHERAL_CONNECT:
            # 要求先に接続完了
            self.scan_stop()
            print("\nble_PERIPHERAL_CONNECT")
            conn_handle, addr_type, addr = data
            print(data)
            self._conn_handle = conn_handle
            
        if event == _IRQ_PERIPHERAL_DISCONNECT:
            conn_handle, _, _ = data
            # 要求先と接続終了
            print("ble_PERIPHERAL_DISCONNECT")
            sys.exit()

def download():
    # downloadPIN
    downroad_pin = Pin(DOWNROAD_PIN, Pin.IN, Pin.PULL_UP)
    if(not downroad_pin.value()):
        sys.exit()

if __name__ == "__main__":
    download()
    gps_ble = GPS_BLE(ADV_MS)
    gps_ble.scan()

    while True:
        pass