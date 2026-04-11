import M5
from M5 import *
import network
import time
import ujson
from umqtt import *

# --- Configuration ---
WIFI_SSID = "coolhandbob"
WIFI_PASS = "myboyblue599a"
MQTT_CLIENTID = "BobsDoorBellMonitor"
MQTT_BROKER = "192.168.86.22" # Windows PC IP
MQTT_TOPIC_ENV = "BobsDoorBell/env_data"

# --- State ---
env_data = {"temp": "--", "hum": "--", "press": "--", "time": "--:--"}
display_mode = 0  # 0: Temp, 1: Press, 2: Hum, 3: Time

def mqtt_MyTestTopicEnv_event(msg):
    global env_data
    print("this is the data:")
    print(msg[0])
    print(msg[1])

    try:
      # Decode the payload from the second item in the tuple
      payload = ujson.loads(msg[1].decode())
        
      # Get Celsius and convert to Fahrenheit
      temp_c = payload.get("temp_c", 0)
      temp_f = (temp_c * 9/5) + 32
      env_data["temp"] = "{:.1f}".format(temp_f)
        
      env_data["hum"] = str(payload.get("humidity", "--"))
      env_data["press"] = str(payload.get("pressure_hpa", "--"))
        
      # Slicing the timestamp to show just the Time (HH:MM:SS)
      full_time = payload.get("timestamp", "--:--")
      env_data["time"] = full_time.split(" ")[1] if " " in full_time else full_time
        
      #draw_ui(); only populate UI at 30 second intervials inorder to avoid race condition.
    except:
        pass

def draw_ui():
    M5.Lcd.fillScreen(0) # Use fillScreen(0) instead of clear()
    M5.Lcd.setCursor(0, 10)
    #M5.Lcd.clear()
    M5.Lcd.setCursor(0, 10)
    M5.Lcd.setTextSize(2)
    
    if display_mode == 0:
        M5.Lcd.setTextColor(0x00FF00) # Green
        M5.Lcd.print(" TEMP:\n\n " + env_data["temp"] + " F")
    elif display_mode == 1:
        M5.Lcd.setTextColor(0x00FFFF) # Cyan
        M5.Lcd.print(" PRESS:\n\n " + env_data["press"])
    elif display_mode == 2:
        M5.Lcd.setTextColor(0xFFFF00) # Yellow
        M5.Lcd.print(" HUMID:\n\n " + env_data["hum"] + "%")
    elif display_mode == 3:
        M5.Lcd.setTextColor(0xFF00FF) # Magenta
        M5.Lcd.print(" TIME:\n\n " + env_data["time"])

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(WIFI_SSID, WIFI_PASS)
        while not wlan.isconnected():
            time.sleep(0.5)

def connect_mqtt():
  try:
    global mqtt_client  
    mqtt_client = MQTTClient(MQTT_CLIENTID, MQTT_BROKER, port=1883, user='', password='', keepalive=300)
    if not mqtt_client == 0:
       print ('mqtt client session created')
    mqtt_client.connect(clean_session=True)
    mqtt_client.subscribe(MQTT_TOPIC_ENV,mqtt_MyTestTopicEnv_event,qos=0)

  except Exception as e:
    print("MQTT connect failed:", e)
    time.sleep(5)

# --- Start ---
if __name__ == '__main__':
  
  last_ping = time.ticks_ms()

  try:
  


    M5.begin()
    connect_wifi()

    connect_mqtt()
    draw_ui()
    
    while True:
      M5.update()
        # IMPORTANT: This triggers the callback when data arrives
      try:
        mqtt_client.check_msg()
        
        # Manually send a ping every 60 seconds
        if time.ticks_diff(time.ticks_ms(), last_ping) > 60000:
            mqtt_client.ping()
            last_ping = time.ticks_ms()
            print("Keep-alive ping sent")
              
      except Exception as e:
        print("MQTT Error, attempting reconnect...")
        connect_mqtt() # Use your existing connect function 
      
      # Check for the screen press (mechanical click)
      if M5.BtnA.wasPressed():
        display_mode = (display_mode + 1) % 4
        draw_ui()
      
      # OPTIONAL: Redraw every 5 seconds to ensure data is fresh
      # even if you don't press the button
      if time.ticks_ms() % 5000 < 100: 
        draw_ui()
        
      time.sleep(0.1)
  except (Exception, KeyboardInterrupt) as e:
    try:
      from utility import print_error_msg
      print_error_msg(e)
    except ImportError:
      print("please update to latest firmware")

      



last_ping = time.ticks_ms()

while True:
    M5.update()
    
    try:
        mqtt_client.check_msg()
        
        # Manually send a ping every 60 seconds
        if time.ticks_diff(time.ticks_ms(), last_ping) > 60000:
            mqtt_client.ping()
            last_ping = time.ticks_ms()
            print("Keep-alive ping sent")
            
    except Exception as e:
        print("MQTT Error, attempting reconnect...")
        connect_mqtt() # Use your existing connect function
    
    if M5.BtnA.wasPressed():
        display_mode = (display_mode + 1) % 4
        needs_redraw = True

    if needs_redraw:
        draw_ui()
        needs_redraw = False
        
    time.sleep(0.1)