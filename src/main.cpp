#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <PubSubClient.h>
#include <Wire.h>
#include <Adafruit_AHTX0.h>
#include <ArduinoJson.h>

// WiFi
const char* ssid = "Tomsovsky";
const char* password = "604246127";

// MQTT
const char* mqtt_server = "192.168.34.4";
const int mqtt_port = 1883;
const char* mqtt_topic = "esp32/climate";

// Piny
const int LED_PIN = 2;
const int SDA_PIN = 21;
const int SCL_PIN = 22;

WebServer server(80);
WiFiClient espClient;
PubSubClient client(espClient);
Adafruit_AHTX0 aht;

float temp = 0;
float humidity = 0;

void handleRoot();
void handleAPI();
void reconnectMQTT();

void setup() {
  Serial.begin(115200);
  delay(100);
  
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  Serial.println("\n\nESP32 - Teplota + Web Server + MQTT");
  
  // I2C a AHT10
  Wire.begin(SDA_PIN, SCL_PIN);
  if (!aht.begin()) {
    Serial.println("AHT10 nenalezen!");
  } else {
    Serial.println("AHT10 inicializován");
  }
  
  // WiFi
  WiFi.begin(ssid, password);
  Serial.print("Připojování k WiFi...");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nPřipojeno!");
    Serial.print("IP adresa: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nChyba připojení WiFi!");
  }
  
  // Web server
  server.on("/", handleRoot);
  server.on("/api/data", handleAPI);
  server.begin();
  Serial.println("Web server spuštěn na portu 80");
  
  // MQTT
  client.setServer(mqtt_server, mqtt_port);
  Serial.println("MQTT broker nastaven na: " + String(mqtt_server));
}

void loop() {
  // Web server
  server.handleClient();
  
  // MQTT reconnection
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  // Čtení senzoru každé 2 sekundy
  static unsigned long lastRead = 0;
  if (millis() - lastRead > 2000) {
    lastRead = millis();
    
    sensors_event_t humidity_event, temp_event;
    if (aht.getEvent(&humidity_event, &temp_event)) {
      temp = temp_event.temperature;
      humidity = humidity_event.relative_humidity;
      
      Serial.printf("Teplota: %.2f °C | Vlhkost: %.2f %%\n", temp, humidity);
      
      // Bliknutí LED při měření
      digitalWrite(LED_PIN, HIGH);
      delay(50);
      digitalWrite(LED_PIN, LOW);
      
      // Odeslat přes MQTT
      if (client.connected()) {
        char payload[100];
        snprintf(payload, sizeof(payload), "{\"temp\":%.2f,\"humidity\":%.2f}", temp, humidity);
        if (client.publish(mqtt_topic, payload)) {
          Serial.println("Data publikována na MQTT");
        } else {
          Serial.println("Chyba publikování na MQTT");
        }
      }
    } else {
       Serial.println("Chyba při čtení senzoru!");
    }
  }
}

void reconnectMQTT() {
  static unsigned long lastAttempt = 0;
  if (millis() - lastAttempt < 5000) return;
  lastAttempt = millis();
  
  Serial.print("Připojování k MQTT (" + String(mqtt_server) + ")...");
  if (client.connect("ESP32_Climate")) {
    Serial.println(" Připojeno!");
  } else {
    Serial.print(" Chyba (rc=");
    Serial.print(client.state());
    Serial.println(") - zkusím znovu za 5s");
  }
}

void handleRoot() {
  String html = R"(
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ESP32 Klimatizace</title>
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; text-align: center; background: #f4f7f6; margin: 0; padding: 20px; color: #333; }
    .container { max-width: 450px; margin: 40px auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    h1 { color: #2c3e50; margin-bottom: 30px; }
    .sensor { margin: 25px 0; padding: 25px; background: #fafafa; border-radius: 10px; border: 1px solid #eee; }
    .value { font-size: 42px; color: #3498db; font-weight: bold; }
    .label { color: #7f8c8d; margin-top: 12px; font-size: 1.1em; text-transform: uppercase; letter-spacing: 1px; }
    .icon { font-size: 52px; margin-bottom: 5px; }
    .status { margin-top: 30px; font-size: 0.85em; padding: 12px; background: #e8f4fd; border-radius: 8px; color: #2980b9; }
    .chip-info { font-size: 0.75em; color: #bdc3c7; margin-top: 15px; }
  </style>
</head>
<body>
  <div class="container">
    <h1>🌍 ESP32 Dashboard</h1>
    
    <div class="sensor">
      <div class="icon">🌡️</div>
      <div class="value" id="temp">--. - °C</div>
      <div class="label">Aktuální teplota</div>
    </div>
    
    <div class="sensor">
      <div class="icon">💧</div>
      <div class="value" id="humidity">--. - %</div>
      <div class="label">Relativní vlhkost</div>
    </div>
    
    <div class="status" id="status">Připojování k senzoru...</div>
    <div class="chip-info">ESP32 Klima Monitoring | MQTT: Enabled</div>
  </div>
  
  <script>
    function updateData() {
      fetch('/api/data')
        .then(r => r.json())
        .then(data => {
          document.getElementById('temp').textContent = data.temp.toFixed(1) + ' °C';
          document.getElementById('humidity').textContent = data.humidity.toFixed(1) + ' %';
          document.getElementById('status').textContent = '✓ Poslední data přijata: ' + new Date().toLocaleTimeString('cs-CZ');
        })
        .catch(e => {
          document.getElementById('status').textContent = '✗ Selhalo spojení se zařízením';
          console.error(e);
        });
    }
    
    updateData();
    setInterval(updateData, 2000);
  </script>
</body>
</html>
  )";
  server.send(200, "text/html", html);
}

void handleAPI() {
  StaticJsonDocument<100> doc;
  doc["temp"] = temp;
  doc["humidity"] = humidity;
  String json;
  serializeJson(doc, json);
  server.send(200, "application/json", json);
}
