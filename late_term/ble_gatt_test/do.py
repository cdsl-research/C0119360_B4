import ubluetooth
from micropython import const
import os
import ubinascii
import sys

_IRQ_SCAN_RESULT = const(5)
_IRQ_PERIPHERAL_CONNECT = const(7)
_IRQ_PERIPHERAL_DISCONNECT = const(8)
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

### パラメータ ###

ADV_MS = 100 # 20ms〜10,240msの間で調整(デフォは300)
SCAN_WINDW_MS = 1280
SCAN_INTERVAL_MS = 11

# configファイル内にデータあり
ID = "-" # ID(0~9)
MODE = 0 # 0:通常(旧) 1:提案(新)
execfile("config.py")

### ここまで。 ###

def hex_bytes_to_str(hex_bytes):
    # バイナリデータを文字列に変換
    hex_str = hex_bytes.decode()

    return_str = ""
    for i in range(0, len(hex_str), 2):
        char_hex = hex_str[i] + hex_str[i+1]
        return_str+= chr(int(char_hex, 16))

    return return_str

class GPS_BLE:
    def __init__(self,adv_ms,id,mode):
        # BLE関係初期化
        self.ble = ubluetooth.BLE()
        if self.ble.active() == False:
            self.ble.active(True)
        self.adv_ms = adv_ms
        self.ble.irq(self.bt_irq)
        self.positioning_cnt_path = "positioning_time.txt"
        self.my_positioning_cnt = self.get_my_positioning_cnt()
        self.my_id = id # 機器のID(0~9)
        self.mode = mode # 既存方式？提案方式？
        self.show_info() 
        self.agency_id = [] # 代行を行ったID
        self.your_agency_id = {} # スキャンしたIoT機器が代行を行ったID（仮）

    def show_info(self):
        # 機器の情報を表示
        print("------ info -----")
        if(self.mode == 1):
            print("NEW_PROGRAM")
        else:
            print("OLD_PROGRAM")
        print("ID:" + self.my_id)
        print("CNT:" + str(self.my_positioning_cnt))
        print("---- info end ----")

    def set_id(self,id):
        # IDの設定
        self.my_id = id

    def adv(self):
        # アドバタイズの開始
        if(self.mode == 1):
            send_str = "N"
        else:
            send_str = "O" 

        send_str = send_str + "," + str(self.my_id) + "," + str(self.my_positioning_cnt)

        for id in self.agency_id:
            send_str = send_str + "," + str(id)

        print("MY ID: " + str(self.my_id))
        agency_str = "AGENCY ID:"
        for id in self.agency_id:
            agency_str = agency_str + str(id) + ","
        print(agency_str)

        # 代行するIDの表示
        send_data = send_str.encode()
        print("ADV_DATA: " + send_str)
        self.ble.gap_advertise(self.adv_ms * 1000 , adv_data=send_data)
        print("BLE_ADVERTISE_START")
        
    
    def scan(self):
        # スキャンの開始        
        print("BLE_SCAN_START")
        self.ble.gap_scan(0,128000,11250) 
        print(".",end="")

    def scan_stop(self):
        # スキャンの停止
        print("BLE_SCAN_STOP")
        self.ble.gap_scan(None)

    def adv_stop(self):
        # アドバタイズの停止
        print("BLE_ADV_STOP")
        self.ble.gap_advertise(None)
        
    def bt_irq(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            # スキャン結果の表示
            addr_type, addr, connectable, rssi, adv_data = data
            adv_data_str = hex_bytes_to_str(ubinascii.hexlify(adv_data))

            if(self.mode == 1 and adv_data_str.startswith("N,") or self.mode == 0 and adv_data_str.startswith("O,")):
                # 提案手法と既存手法は互いに通信できないようにする
                adv_data_arr = adv_data_str.split(",")
                your_positioning_cnt = int(adv_data_arr[2])
                print("GPS" + str(your_positioning_cnt))
                
                if(self.my_positioning_cnt <= your_positioning_cnt):
                    # 測位回数の多い機器に接続要求（やります）
                    """
                    多い機器が今まで測位代行した機器を変数に入れる
                    """
                    address_str = ubinascii.hexlify(addr).decode()
                    print("SOKUI DAIKOU SIMASU YOII? ID:" + str(adv_data_arr[1])) 
                    self.ble.gap_connect(addr_type, addr, 1000)

                    agency_id_ = []
                    agency_id_.append(int(adv_data_arr[1]))
                    for i in range(3,len(adv_data_arr)):
                        agency_id_.append(int(adv_data_arr[i]))
                    self.your_agency_id[address_str] = agency_id_
            
            else:
                print(".",end="")
        
        if event == _IRQ_PERIPHERAL_CONNECT:
            # 測位代行することが伝わった
            conn_handle, addr_type, addr = data
            address_str = ubinascii.hexlify(addr).decode()

            print("SOKUI DAIKOU SIMASU! ID:" + str(self.your_agency_id[address_str][0]))
            self.scan_stop()
            self.adv_stop()

            # 代行処理するIDを追加
            for id in self.your_agency_id[address_str]:
                if(not id in self.agency_id):
                    if(str(id) == str(self.my_id)):
                        # 自分のIDが代行IDに入らないようにする
                        print("DEL MY ID IN AGENCY")
                    else:
                        self.agency_id.append(id)
            """
            ココに代行する機器を記録する
            代行数によってBLE通信をやめる
            """
            gps_ble.adv()
            gps_ble.scan()
            
    
        if event == _IRQ_CENTRAL_CONNECT:
            # やってくれるらしい
            self.scan_stop()
            self.adv_stop()
            conn_handle, _, addr = data
            self.ble.gap_disconnect(conn_handle)
            print("=========== END ===========")
            
        

    def get_my_positioning_cnt(self):
        # 測位回数の取得
        # 累計測位回数の読込
        if(self.positioning_cnt_path in os.listdir()):
            f = open(self.positioning_cnt_path)
            my_positioning_cnt = int(f.read())
            f.close()
        else:
            my_positioning_cnt = 0
        print("POSITIONING_CNT : " + str(my_positioning_cnt))
        return my_positioning_cnt
    
if __name__ == "__main__":
    gps_ble = GPS_BLE(ADV_MS,ID,MODE)
    gps_ble.adv()
    gps_ble.scan()

    while True:
        pass