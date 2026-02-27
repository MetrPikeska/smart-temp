#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// WiFi
const char* ssid = "Tomsovsky";
const char* password = "604246127";

// Server
const char* server = "192.168.34.4";
const int port = 5432;  // PostgreSQL port

// I2C
#define LED_PIN 2
#define I2C_SDA 21
#define I2C_SCL 22

// AHT10
#define AHT10_ADDR 0x38
#define AHT10_INIT 0xBE
#define AHT10_MEASURE 0xAC
#define AHT10_SOFTRESET 0xBA

// Forward declarations
void initAHT10();
bool readAHT10(float &temperature, float &humidity);
void sendToServer(float temp, float humidity);
void connectWiFi();

unsigned long lastSend = 0;
const unsigned long sendInterval = 10000; // 10 sekund

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  pinMode(LED_PIN, OUTPUT);
  
  Serial.println("\n\nESP32 - AHT10 + WiFi");
  
  Wire.begin(I2C_SDA, I2C_SCL);
  initAHT10();
  
  connectWiFi();
}

void connectWiFi() {
  Serial.print("Připojování k WiFi: ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi připojeno!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi selhalo!");
  }
}

void initAHT10() {
  Serial.println("Inicializace AHT10...");
  
  Wire.beginTransmission(AHT10_ADDR);
  Wire.write(AHT10_SOFTRESET);
  Wire.endTransmission();
  delay(20);
  
  Wire.beginTransmission(AHT10_ADDR);
  Wire.write(AHT10_INIT);
  Wire.write(0x08);
  Wire.write(0x00);
  Wire.endTransmission();
  delay(100);
  
  Serial.println("AHT10 inicializován");
}

bool readAHT10(float &temperature, float &humidity) {
  Wire.beginTransmission(AHT10_ADDR);
  Wire.write(AHT10_MEASURE);
  Wire.write(0x33);
  Wire.write(0x00);
  Wire.endTransmission();
  
  delay(80);
  
  Wire.requestFrom(AHT10_ADDR, 6);
  
  if (Wire.available() != 6) {
    return false;
  }
  
  uint8_t data[6];
  for (int i = 0; i < 6; i++) {
    data[i] = Wire.read();
  }
  
  if (data[0] & 0x80) {
    return false;
  }
  
  uint32_t humidity_raw = ((uint32_t)data[1] << 12) | ((uint32_t)data[2] << 4) | (data[3] >> 4);
  humidity = (float)humidity_raw / 1048576.0f * 100.0f;
  
  uint32_t temperature_raw = (((uint32_t)data[3] & 0x0F) << 16) | ((uint32_t)data[4] << 8) | data[5];
  temperature = (float)temperature_raw / 1048576.0f * 200.0f - 50.0f;
  
  return true;
}

void sendToServer(float temp, float humidity) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi není připojeno!");
    return;
  }
  
  // Připravit JSON
  StaticJsonDocument<200> doc;
  doc["temperature"] = temp;
  doc["humidity"] = humidity;
  
  String jsonData;
  serializeJson(doc, jsonData);
  
  // Odeslat na Python API server
  HTTPClient http;
  String url = "http://192.168.34.4:5000/api/data";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(jsonData);
  
  if (httpResponseCode > 0) {
    Serial.print("Response: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("Chyba: ");
    Serial.println(http.errorToString(httpResponseCode));
  }
  
  http.end();
}

void loop() {
  // Rozsvícení LED
  digitalWrite(LED_PIN, HIGH);
  
  // Čtení senzoru
  float temp = 0, humidity = 0;
  if (readAHT10(temp, humidity)) {
    Serial.print("Teplota: ");
    Serial.print(temp, 1);
    Serial.print(" °C | Vlhkost: ");
    Serial.print(humidity, 1);
    Serial.println(" %");
    
    // Posílat na server každých 10 sekund
    if (millis() - lastSend >= sendInterval) {
      sendToServer(temp, humidity);
      lastSend = millis();
    }
  } else {
    Serial.println("Chyba čtení AHT10");
  }
  
  // Zhasnutí LED
  digitalWrite(LED_PIN, LOW);
  
  delay(1000);
}