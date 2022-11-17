import network
import time

def do_connect(wifi_config):
    # Wi-Fiに接続
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)

        scandata = sta_if.scan() 

        for scan in scandata:
            for config in wifi_config:
                if(scan[0].decode() == config[0] and not sta_if.isconnected()):
                    print(f"SSID: {scan[0].decode()}")
                    sta_if.connect(config[0], config[1])
                    while not sta_if.isconnected():
                        time.sleep(0.2)
                        print(".",end="")
    print('connected: ' , sta_if.config('essid'))
    return sta_if