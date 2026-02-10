import os, sys, io, network
import M5
import time
from M5 import *
from umqtt import *
from machine import Pin, SPI, I2S


# --- USER CONFIG ---
WIFI_SSID     = "coolhandbob"
WIFI_PASSWORD = ""

MQTT_BROKER   = "192.168.86.22"
MQTT_CLIENTID = "BobsDoorBell"
MQTT_TOPIC    = "DoorBellPressed"
ding_dong_times=0
INIT_MESSAGE = "I'm a doorbell"
#INIT_MESSAGE = "Door Bell Out of Order"

def btnA_wasReleased_event(state):
  global mqtt_client, wlan
  print('ding dong')
  mqtt_client.publish(MQTT_TOPIC, "DingDong",qos=0)

def mqtt_MyTestTopic_event(data):
  global mqtt_client, wlan
  print(data[0])
  print(data[1])


# --- MQTT Setup ---
def connect_mqtt():
  try:
    global mqtt_client  
    mqtt_client = MQTTClient(MQTT_CLIENTID, MQTT_BROKER, port=1883, user='', password='', keepalive=300)
    if not mqtt_client == 0:
       print ('mqtt client session created')
    mqtt_client.connect(clean_session=True)
    mqtt_client.subscribe(MQTT_TOPIC, mqtt_MyTestTopic_event, qos=0)
  except Exception as e:
    print("MQTT connect failed:", e)
    time.sleep(5)


def loop():
  global mqtt_client
  
  M5.update()
  try:
    mqtt_client.check_msg()
  except Exception:
    print("MQTT lost, reconnecting...")
    time.sleep(2)
    client=connect_mqtt()


# --- WiFi Setup ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.connect(WIFI_SSID,WIFI_PASSWORD)
 


def setup():

  M5.begin()
  Widgets.fillScreen(0x000000)
  BtnA.setCallback(type=BtnA.CB_TYPE.WAS_RELEASED, cb=btnA_wasReleased_event)
  label0 = Widgets.Label(str(INIT_MESSAGE), 3, 40, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu12)
  label1 = Widgets.Label("Press Me!", 3, 85, 1.0, 0xdadada, 0x333333, Widgets.FONTS.DejaVu18)
 
  connect_wifi()
  mqtt_clientclient = connect_mqtt()

  print("Doorbell system ready.")
  
 

if __name__ == '__main__':
  try:
    setup()
    while True:
      loop()
  except (Exception, KeyboardInterrupt) as e:
    try:
      from utility import print_error_msg
      print_error_msg(e)
    except ImportError:
      print("please update to latest firmware")


