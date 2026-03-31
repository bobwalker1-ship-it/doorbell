import paho.mqtt.client as mqtt
import pygame
import time
import json
import csv
import os

LOG_FILE = "doorbell_log.csv"

# --- Configuration ---
MQTT_BROKER = "192.168.86.22" # Your Mosquitto IP
MQTT_TOPIC = "DoorBellPressed"
SOUND_FILE = "/home/bobwalker1/Music/arcade-game-victory-chime-epic-stock-media-1-00-01.mp3"

# Initialize Pygame Mixer
pygame.mixer.init()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to broker successfully")
        # SUBMIT SUBSCRIPTIONS HERE
        # This ensures they are sent every time the connection is established
        client.subscribe([("DoorBellPressed", 0), ("BobsDoorBell/env_data", 0)])
    else:
        print(f"Connection failed with code {rc}")
      


def on_message(client, userdata, msg):
    print(f"Doorbell pressed! Topic: {msg.topic}")
    # Load and play the sound
    pygame.mixer.music.load(SOUND_FILE)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    
def on_message_env(client, userdata, msg):
    print(f"Env Data! Topic: {msg.topic}")
    try:
        # 1. Parse JSON
        data = json.loads(msg.payload.decode())
        
        # 2. Define the row
        row = [data['timestamp'], data['temp_c'], data['humidity'], data['pressure_hpa']]
        
        # 3. OPEN IN APPEND MODE ('a') AND USE WITH STATEMENT
        # The 'with' statement automatically closes the file after writing
        file_exists = os.path.isfile("doorbell_log.csv")
        
        with open("doorbell_log.csv", mode='a', newline='') as f:
            writer = csv.writer(f)
            # Add header only if the file is brand new
            if not file_exists:
                writer.writerow(["Timestamp", "Temp_C", "Humidity", "Pressure"])
            
            writer.writerow(row)
            # Optional: f.flush() - but 'with' handles this on close
            
        print(f"Logged data at {data['timestamp']}")
        
    except Exception as e:
        print(f"Logging Error: {e}")

   

client = mqtt.Client()
client.on_connect = on_connect

# 3. Map topics to specific functions
client.message_callback_add("DoorBellPressed", on_message)
client.message_callback_add("BobsDoorBell/env_data", on_message_env)

client.connect(MQTT_BROKER, 1883, 60)

# Keep the script running
client.loop_forever()
