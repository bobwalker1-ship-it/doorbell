import paho.mqtt.client as mqtt
import pygame
import time

# --- Configuration ---
MQTT_BROKER = "192.168.86.22" # Your Mosquitto IP
MQTT_TOPIC = "DoorBellPressed"
SOUND_FILE = "/home/bobwalker1/Music/arcade-game-victory-chime-epic-stock-media-1-00-01.mp3"

# Initialize Pygame Mixer
pygame.mixer.init()

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(f"Doorbell pressed! Topic: {msg.topic}")
    # Load and play the sound
    pygame.mixer.music.load(SOUND_FILE)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, 1883, 60)

# Keep the script running
client.loop_forever()
