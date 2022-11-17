import ubluetooth
from micropython import const
import ubinascii

class TEST_BLE:
    def __init__(self):
        self.ble = ubluetooth.BLE()
        if self.ble.active() == False:
            self.ble.active(True)
        self.show_bt_mac()

    def show_bt_mac(self):
        address_str = ubinascii.hexlify(self.ble.config("mac")[1]).decode()
        print("BLE_MAC : " + address_str)
    
    def adv(self):
        print("ble_advertise_start")
        send_str = "BLE,"
        send_data = send_str.encode()
        self.ble.gap_advertise(20000 , adv_data=send_data)

if __name__ == "__main__":
    # BLE通信
    print("adv start")
    gps_ble = TEST_BLE()    
    gps_ble.adv()