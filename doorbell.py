import os, sys, io, network, time, ujson, ntptime
import M5
from M5 import *
from umqtt import *
from unit import ENVUnit
from hardware import I2C
from hardware import Pin

# --- CONFIG ---
WIFI_SSID     = ""
WIFI_PASSWORD = ""
MQTT_BROKER   = "192.168.86.22"
MQTT_CLIENTID = "BobsDoorBell"
MQTT_TOPIC    = "DoorBellPressed"
MQTT_TOPIC_ENV = "BobsDoorBell/env_data"
ding_dong_times=0
INIT_MESSAGE = "I'm a doorbell"
#INIT_MESSAGE = "Door Bell Out of Order"

last_broadcast_time = 0
BROADCAST_INTERVAL = 30  # Seconds between sensor updates

# Austin is UTC-6 (Standard) or UTC-5 (Daylight Savings)
UTC_OFFSET = -5 * 3600 
last_broadcast_time = 0
BROADCAST_INTERVAL = 30 
bobs_env3 = None

def btnA_wasReleased_event(state):
  global mqtt_client, wlan
  print('ding dong')
  mqtt_client.publish(MQTT_TOPIC, 'DingDong',qos=0)

def mqtt_MyTestTopic_event(data):
  global mqtt_client, wlan
  print(data[0])
  print(data[1])


def mqtt_MyTestTopicEnv_event(data):
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
    mqtt_client.subscribe(MQTT_TOPIC_ENV,mqtt_MyTestTopicEnv_event,qos=0)

  except Exception as e:
    print("MQTT connect failed:", e)
    time.sleep(5)


def sync_time():
    try:
        print("Syncing time via NTP...")
        ntptime.settime() # Grab UTC time from pool.ntp.org
        print("Time synced successfully.")
    except Exception as e:
        print("NTP sync failed:", e)

def get_timestamp():
    # Apply the UTC offset to the internal RTC
    t = time.localtime(time.time() + UTC_OFFSET)
    return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        t[0], t[1], t[2], t[3], t[4], t[5]
    )

def broadcast_env_data():
    global bobs_env3, mqtt_client
    try:
        # 1. Read the ENV-III Sensors
        temp = bobs_env3.read_temperature()
        humi = bobs_env3.read_humidity()
        pres = bobs_env3.read_pressure()
        
        # 2. Get the current time (Austin is UTC-6)
        # Note: adjust UTC_OFFSET to -5 * 3600 during Daylight Savings
        t = time.localtime(time.time() + UTC_OFFSET)
        timestamp = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            t[0], t[1], t[2], t[3], t[4], t[5]
        )
        
        # 3. Create the Python Dictionary
        # This structure is clean and easy to expand later
        sensor_data = {
            "timestamp": timestamp,
            "temp_c": round(temp, 2),
            "humidity": round(humi, 2),
            "pressure_hpa": round(pres, 2)
        }
        
        # 4. Serialize to JSON string and publish
        payload = ujson.dumps(sensor_data)
        mqtt_client.publish(MQTT_TOPIC_ENV, payload)
        
        print("Sent JSON Update:", payload)
        
    except Exception as e:
        print("Sensor Polling Error:", e)

def loop():
  global mqtt_client, last_broadcast_time
  
  M5.update()
  
  try:
    mqtt_client.check_msg()
  except Exception:
    print("MQTT lost, reconnecting...")
    time.sleep(2)
    client=connect_mqtt()

  # Polling logic: check if 30 seconds have passed
  current_time = time.time()
  if current_time - last_broadcast_time > BROADCAST_INTERVAL:
    broadcast_env_data()
    last_broadcast_time = current_time


# --- WiFi Setup ---
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.connect(WIFI_SSID,WIFI_PASSWORD)

def setup():
    global bobs_env3
    M5.begin()

    Widgets.fillScreen(0x000000)
    BtnA.setCallback(type=BtnA.CB_TYPE.WAS_RELEASED, cb=btnA_wasReleased_event)
    label0 = Widgets.Label(str(INIT_MESSAGE), 3, 40, 1.0, 0xffffff, 0x000000, Widgets.FONTS.DejaVu12)
    label1 = Widgets.Label("Press Me!", 3, 85, 1.0, 0xdadada, 0x333333, Widgets.FONTS.DejaVu18)

    i2c0 = I2C(0, scl=Pin(1), sda=Pin(2), freq=100000)
    bobs_env3 = ENVUnit(i2c0, type=3) 
    
    connect_wifi()
    

    print("Doorbell system ready.")
    
    sync_time() # Set the clock
    
    mqtt_clientclient = connect_mqtt()

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
      