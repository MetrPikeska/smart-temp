import paho.mqtt.client as mqtt
import psycopg2
import json

# Konfigurace
MQTT_BROKER = "192.168.34.4"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/climate"

DB_CONFIG = {
    "host": "192.168.34.4",
    "database": "esp32_sensors",
    "user": "esp_user",
    "password": "kokot"
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
        
        # Uložení do PostgreSQL
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

client = mqtt.Client()
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
