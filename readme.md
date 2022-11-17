# レポジトリ名
Nosuke_GPS

# このレポジトリについて
卒業研究に関するレポジトリです。

# 構成　前期
* previous_term/current_logger  
電力計測モジュールINA219を使用した、電力ロガーです。   
INA219で取得した電流値をSDカードに書き込みます。
* previous_term/ble_time_test   
BLE通信時間を計測し，ESP32内にcsvファイルを作成します。   
* previous_term/gps_logger
位置情報発信機用プログラムです。   
現時点（20220707）では位置情報共有機能が未完成です。   
接続後、データの交換処理がまだできていません。

# 構成 後期
* late_term/ble_gatt_test
IoT機器同士が通信を行うプログラム
* late_time/qmc5883l_compass
地磁気センサから角度を求めるプログラム
自動でキャリブレーションも行う
* late_time/esp32_time_test
インターネット上のNTPサーバから現在時刻を取得するプログラム
* late_time/rssi_test
RSSI値を計測する為のプログラム
* late_time/mapmatching
マップマッチングを行うプログラム
* late_time/all
実験に使用したプログラム・その他