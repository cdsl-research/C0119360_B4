# このレポジトリの名前
Nosuke_GPS

# このレポジトリについて
卒業研究に関するレポジトリです。

# 構成
* current_logger  
電力計測モジュールINA219を使用した、電力ロガーです。   
INA219で取得した電流値をSDカードに書き込みます。
* ble_time_test   
BLE通信時間を計測し，ESP32内にcsvファイルを作成します。   
* gps_logger
位置情報発信機用プログラムです。   
現時点（20220707）では位置情報共有機能が未完成です。   
接続後、データの交換処理がまだできていません。
