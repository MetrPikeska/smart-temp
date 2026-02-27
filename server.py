#!/usr/bin/env python3
"""
Flask API server pro ESP32 senzor
Spustit: python3 server.py
Server naslouchá na 192.168.34.4:5000
"""

import psycopg2
from flask import Flask, request, jsonify
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta

app = Flask(__name__)

# PostgreSQL konfigurace
DB_CONFIG = {
    'host': 'localhost',
    'database': 'esp32_sensors',
    'user': 'esp_user',
    'password': 'kokot',
    'port': 5432
}

def get_db():
    """Připojit k databázi"""
    return psycopg2.connect(**DB_CONFIG)

@app.route('/')
def index():
    """Servírovat HTML dashboard"""
    try:
        with open('index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Chyba: {e}", 500

@app.route('/api/data', methods=['POST'])
def receive_data():
    """Přijmout data z ESP32"""
    try:
        data = request.get_json()
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        
        if temperature is None or humidity is None:
            return jsonify({'error': 'Chybí temperature nebo humidity'}), 400
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sensor_data (temperature, humidity) VALUES (%s, %s)",
            (temperature, humidity)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[{datetime.now()}] Uloženo: temp={temperature}°C, humidity={humidity}%")
        return jsonify({'status': 'ok', 'message': 'Data uložena'}), 201
    except Exception as e:
        print(f"Chyba: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """Získat poslední měření"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT temperature, humidity, created_at FROM sensor_data ORDER BY created_at DESC LIMIT 1"
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            return jsonify(result), 200
        return jsonify({'error': 'Žádná data'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Získat historii za poslední N hodin"""
    try:
        hours = request.args.get('hours', 24, type=int)
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT temperature, humidity, created_at FROM sensor_data WHERE created_at > NOW() - INTERVAL '%s hours' ORDER BY created_at DESC",
            (hours,)
        )
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Získat statistiku"""
    try:
        hours = request.args.get('hours', 24, type=int)
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                AVG(temperature) as avg_temp,
                MAX(temperature) as max_temp,
                MIN(temperature) as min_temp,
                AVG(humidity) as avg_humidity,
                MAX(humidity) as max_humidity,
                MIN(humidity) as min_humidity
            FROM sensor_data 
            WHERE created_at > NOW() - INTERVAL '%s hours'
        """, (hours,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("Spuštění Flask serveru na 0.0.0.0:5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)

def get_db():
    """Připojit k databázi"""
    return psycopg2.connect(**DB_CONFIG)

@app.route('/api/data', methods=['POST'])
def receive_data():
    """Přijmout data z ESP32"""
    try:
        data = request.get_json()
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        
        if temperature is None or humidity is None:
            return jsonify({'error': 'Chybí temperature nebo humidity'}), 400
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sensor_data (temperature, humidity) VALUES (%s, %s)",
            (temperature, humidity)
        )
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[{datetime.now()}] Uloženo: temp={temperature}°C, humidity={humidity}%")
        return jsonify({'status': 'ok', 'message': 'Data uložena'}), 201
    except Exception as e:
        print(f"Chyba: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """Získat poslední měření"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT temperature, humidity, created_at FROM sensor_data ORDER BY created_at DESC LIMIT 1"
        )
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result:
            return jsonify(result), 200
        return jsonify({'error': 'Žádná data'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Získat historii za poslední N hodin"""
    try:
        hours = request.args.get('hours', 24, type=int)
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            "SELECT temperature, humidity, created_at FROM sensor_data WHERE created_at > NOW() - INTERVAL '%s hours' ORDER BY created_at DESC",
            (hours,)
        )
        results = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify(results), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Získat statistiku"""
    try:
        hours = request.args.get('hours', 24, type=int)
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT 
                AVG(temperature) as avg_temp,
                MAX(temperature) as max_temp,
                MIN(temperature) as min_temp,
                AVG(humidity) as avg_humidity,
                MAX(humidity) as max_humidity,
                MIN(humidity) as min_humidity
            FROM sensor_data 
            WHERE created_at > NOW() - INTERVAL '%s hours'
        """, (hours,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.close()
        conn.close()
        return jsonify({'status': 'ok'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    print("Spuštění Flask serveru na 0.0.0.0:5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)