from importlib import import_module
from turtle import distance
import serial
import sys
import time
import os

""" パラメータ """
CNT = 200 # RSSI取得回数
port = "/dev/tty.usbserial-0001" # 接続先
speed = 115200 # シリアル通信 速度
csv_path = os.path.dirname(__file__) + "/rssi.csv" # csv出力先
""" パラメータ ここまで"""

def hex_bytes_to_str(hex_bytes):
    hex_str = hex_bytes.decode()

    return_str = ""
    for i in range(0, len(hex_str), 2):
        char_hex = hex_str[i] + hex_str[i+1]
        return_str+= chr(int(char_hex, 16))

    return return_str

def csv_out(distance,rssi):
    with open(csv_path, 'a') as f:
        print(str(distance) + "," + str(rssi), file=f)

distance = int(input("distance? [m] : "))

cnt = 0

ser = serial.Serial(port, speed)
ser.close()
ser.open()
r = ser.read()
print(len(r))
print("start")

while True:
    r = ser.readline()
    try:
        str1 = r.strip().decode()
        rssi = int(str1)
        if(rssi < 0):
            cnt += 1
            print("RSSI:" + str(rssi) + " CNT:(" + str(cnt) + "/" + str(CNT) + ")" + " DISTANCE:" +  str(distance) + "[m]")
            csv_out(distance,rssi)
    except:
        pass

    if(cnt>=CNT):
        sys.exit()