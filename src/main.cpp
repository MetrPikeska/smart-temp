#include <Arduino.h>
#include <Wire.h>

// Definice pinu pro LED - GPIO 2 (vestavěná LED na ESP32-DEVKIT)
#define LED_PIN 2

// I2C piny
#define I2C_SDA 21
#define I2C_SCL 22

// AHT10 adresa
#define AHT10_ADDR 0x38

// AHT10 příkazy
#define AHT10_INIT 0xBE
#define AHT10_MEASURE 0xAC
#define AHT10_SOFTRESET 0xBA

// Forward declaration
void initAHT10();
bool readAHT10(float &temperature, float &humidity);

void setup() {
  // Inicializace seriové komunikace pro debug
  Serial.begin(115200);
  delay(1000);
  
  // Nastavení LED pinu jako výstup
  pinMode(LED_PIN, OUTPUT);
  
  Serial.println("\n\nESP32 - AHT10 Sensor");
  Serial.println("Inicializace I2C na SDA=" + String(I2C_SDA) + ", SCL=" + String(I2C_SCL));
  
  // Inicializace I2C
  Wire.begin(I2C_SDA, I2C_SCL);
  
  // Inicializace AHT10
  initAHT10();
}

void initAHT10() {
  Serial.println("Inicializace AHT10...");
  
  // Soft reset
  Wire.beginTransmission(AHT10_ADDR);
  Wire.write(AHT10_SOFTRESET);
  Wire.endTransmission();
  delay(20);
  
  // Inicializace
  Wire.beginTransmission(AHT10_ADDR);
  Wire.write(AHT10_INIT);
  Wire.write(0x08);
  Wire.write(0x00);
  Wire.endTransmission();
  delay(100);
  
  Serial.println("AHT10 inicializován");
}

bool readAHT10(float &temperature, float &humidity) {
  // Odeslání příkazu měření
  Wire.beginTransmission(AHT10_ADDR);
  Wire.write(AHT10_MEASURE);
  Wire.write(0x33);
  Wire.write(0x00);
  Wire.endTransmission();
  
  // Čekání na měření
  delay(80);
  
  // Čtení dat
  Wire.requestFrom(AHT10_ADDR, 6);
  
  if (Wire.available() != 6) {
    return false;
  }
  
  uint8_t data[6];
  for (int i = 0; i < 6; i++) {
    data[i] = Wire.read();
  }
  
  // Kontrola bitu "busy"
  if (data[0] & 0x80) {
    return false;
  }
  
  // Výpočet vlhkosti (20 bitů)
  uint32_t humidity_raw = ((uint32_t)data[1] << 12) | ((uint32_t)data[2] << 4) | (data[3] >> 4);
  humidity = (float)humidity_raw / 1048576.0f * 100.0f;
  
  // Výpočet teploty (20 bitů)
  uint32_t temperature_raw = (((uint32_t)data[3] & 0x0F) << 16) | ((uint32_t)data[4] << 8) | data[5];
  temperature = (float)temperature_raw / 1048576.0f * 200.0f - 50.0f;
  
  return true;
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
  } else {
    Serial.println("Chyba čtení AHT10");
  }
  
  // Zhasnutí LED
  digitalWrite(LED_PIN, LOW);
  
  // Čekání
  delay(2000);
}