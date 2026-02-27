# ESP32 Senzor teploty a vlhkosti

Kompletní systém pro měření teploty a vlhkosti s AHT10 senzorem na ESP32 a zobrazení na web rozhraní.

## Architektura

```
ESP32 (WiFi)
    ↓
192.168.34.4:5000 (Python Flask API)
    ↓
PostgreSQL (esp32_sensors)
    ↓
petrmikeska.cz (PHP + HTML)
```

## Instalace

### 1. Databáze (PostgreSQL)

```bash
sudo -u postgres psql
postgres=# CREATE DATABASE esp32_sensors;
postgres=# CREATE USER esp_user WITH PASSWORD '<your_password>';
postgres=# GRANT ALL PRIVILEGES ON DATABASE esp32_sensors TO esp_user;
postgres=# \c esp32_sensors
esp32_sensors=# CREATE TABLE sensor_data (
    id SERIAL PRIMARY KEY,
    temperature FLOAT NOT NULL,
    humidity FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
esp32_sensors=# CREATE INDEX idx_created_at ON sensor_data(created_at DESC);
```

### 2. Python API Server (na 192.168.34.4)

```bash
cd ~/smart-temp
python3 -m venv venv
source venv/bin/activate
pip install flask psycopg2-binary
python3 server.py
```

Server bude naslouchat na `http://192.168.34.4:5000`
Upravte WiFi v `src/main.cpp`:
```cpp
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";
```

Pak nahrajte:
```bash

```bash
# Zkompilovat a nahrát
/home/petr-mikeska/.platformio/penv/bin/platformio run --target upload

# Sledovat výstup
/home/petr-mikeska/.platformio/penv/bin/platformio device monitor --port /dev/ttyUSB0 --baud 115200
```

### 4. Web interface (na petrmikeska.cz)

Nahrajte přes FTP:
- `api.php` → `petrmikeska.cz/api.php`
- `index.html` → `petrmikeska.cz/index.html`

Pak otevřete: `http://petrmikeska.cz/index.html`

## Konfigurační údaje

## Konfigurace

### ESP32 Hardware
- **I2C SDA:** GPIO 21
- **I2C SCL:** GPIO 22
- **LED:** GPIO 2

### PostgreSQL
- **Databáze:** esp32_sensors
- **Uživatel:** esp_user
- **Host:** localhost
- **Port:** 5432

## API Endpoints

### Přijímání dat (ESP32 → Server)
```
POST http://192.168.34.4:5000/api/data
Content-Type: application/json

{"temperature": 24.5, "humidity": 45.2}
```

### Čtení dat (Web → Server)
```
GET /api/latest
GET /api/history?hours=24
GET /api/stats?hours=24
GET /health
```

## Systém pracuje takto:

1. **ESP32** čte AHT10 senzor každou sekundu
2. **Každých 10 sekund** posílá data na API server
3. **API server** ukládá data do PostgreSQL
4. **Web interface** na petrmikeska.cz se připojuje k API serveru a zobrazuje data
5. **Automatická aktualizace** každých 30 sekund

## Ladění

### Kontrola spojení ESP32 s WiFi:
```
Řádek: "Připojování k WiFi: Tomsovsky"
```

### Kontrola komunikace s API:
```
Řádek: "Response: 200"
```

### Kontrola databáze:
```bash
psql esp32_sensors esp_user
esp32_sensors=> SELECT * FROM sensor_data ORDER BY created_at DESC LIMIT 5;
```

## Soubory

- `src/main.cpp` - ESP32 firmware (Arduino)
- `server.py` - Python Flask API
- `api.php` - PHP proxy pro čtení dat
- `index.html` - Web dashboard
- `platformio.ini` - PlatformIO konfigurace

## Poznámky

- ESP32 data posílá **každých 10 sekund**
- Web se obnovuje **každých 30 sekund**
- Hisotrie se drží **24 hodin**
- I2C pull-up rezistory: **3.3V s pull-up na SDA/SCL** (obvykle jsou na modulu AHT10)

## Troubleshooting

**"Žádná zařízení nenalezena" v I2C scanu:**
- Zkontrolujte zapojení: SDA (GPIO 21), SCL (GPIO 22), GND, 3.3V
- Zkontrolujte pull-up rezistory
- Zkuste resetovat AHT10 odpojením a připojením napájení

**"WiFi selhalo":**
- Zkontrolujte SSID a heslo
- Zkontrolujte signál WiFi sítě
- Resetujte ESP32

**"Chyba při připojení k databázi":**
- Zkontrolujte PostgreSQL běží: `sudo systemctl status postgresql`
- Zkontrolujte heslo v `server.py`
- Zkontrolujte tabulku existuje: `\d sensor_data` v psql
