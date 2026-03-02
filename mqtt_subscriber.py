import paho.mqtt.client as mqtt
import psycopg2
import json
import os
from dotenv import load_dotenv

# Načtení proměnných z .env souboru
load_dotenv()

# Konfigurace
MQTT_BROKER = os.getenv("MQTT_SERVER", "192.168.34.4")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "esp32/climate")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "192.168.34.4"),
    "database": os.getenv("DB_NAME", "esp32_sensors"),
    "user": os.getenv("DB_USER", "esp_user"),
    "password": os.getenv("DB_PASS", "kokot")
}

def on_connect(client, userdata, flags, rc):
    print(f"Připojeno k MQTT Brokeru (rc={rc})")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        temp = data.get("temp")
        humidity = data.get("humidity")
        
        print(f"Přijata data: Teplota={temp}°C, Vlhkost={humidity}%")
        
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sensor_data (temperature, humidity) VALUES (%s, %s)",
            (temp, humidity)
        )
        conn.commit()
        cur.close()
        conn.close()
        print("Data uložena do databáze.")
        
    except Exception as e:
        print(f"Chyba při zpracování zprávy: {e}")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1) # Použití moderního API
client.on_connect = on_connect
client.on_message = on_message

print(f"Spouštím MQTT Subscriber na {MQTT_BROKER}...")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print("Ukončuji...")
except Exception as e:
    print(f"Kritická chyba: {e}")
