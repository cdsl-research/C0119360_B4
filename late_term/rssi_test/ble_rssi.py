import ubluetooth
from micropython import const
import ubinascii

_IRQ_SCAN_RESULT = const(5)

def hex_bytes_to_str(hex_bytes):
    hex_str = hex_bytes.decode()

    return_str = ""
    for i in range(0, len(hex_str), 2):
        char_hex = hex_str[i] + hex_str[i+1]
        return_str+= chr(int(char_hex, 16))

    return return_str

class TEST_BLE:
    def __init__(self):
        self.ble = ubluetooth.BLE()
        if self.ble.active() == False:
            self.ble.active(True)
        self.ble.irq(bt_irq)

    def scan(self):
        print("SCAN_START")
        self.ble.gap_scan(0,128000,11250) 

def bt_irq(event, data): # BLEスキャンの結果
    addr_type, addr, connectable, rssi, adv_data = data
    adv_data_str = hex_bytes_to_str(ubinascii.hexlify(adv_data))

    if adv_data_str.startswith("BLE"):
        print(str(rssi)) 
    else:
        print(".")

if __name__ == "__main__":

    # BLE通信
    gps_ble = TEST_BLE()
    gps_ble.scan()

