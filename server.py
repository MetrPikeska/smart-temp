#!/usr/bin/env python3
"""
Flask API server pro ESP32 senzor
Spustit: python3 server.py
Server naslouchá na 192.168.34.4:5000
"""

from flask import Flask, request, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import os

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

@app.route('/api/data', methods=['POST'])
def receive_data():
    """Přijmout data z ESP32 a uložit do databáze"""
    try:
        data = request.get_json()
        temperature = float(data.get('temperature'))
        humidity = float(data.get('humidity'))
        
        # Uložit do databáze
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute(
            "INSERT INTO sensor_data (temperature, humidity) VALUES (%s, %s)",
            (temperature, humidity)
        )
        
        conn.commit()
        cur.close()
        conn.close()
        
        print(f"[{datetime.now()}] Uloženo: Teplota={temperature}°C, Vlhkost={humidity}%")
        
        return jsonify({'status': 'ok', 'message': 'Data uložena'}), 200
    
    except Exception as e:
        print(f"Chyba: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/latest', methods=['GET'])
def get_latest():
    """Vrátit poslední měření"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute(
            "SELECT temperature, humidity, created_at FROM sensor_data ORDER BY created_at DESC LIMIT 1"
        )
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if row:
            return jsonify({
                'temperature': row['temperature'],
                'humidity': row['humidity'],
                'created_at': row['created_at'].isoformat()
            }), 200
        else:
            return jsonify({'error': 'Žádná data'}), 404
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/history', methods=['GET'])
def get_history():
    """Vrátit historii posledních 24 hodin"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        hours = request.args.get('hours', 24, type=int)
        since = datetime.now() - timedelta(hours=hours)
        
        cur.execute(
            "SELECT temperature, humidity, created_at FROM sensor_data WHERE created_at > %s ORDER BY created_at",
            (since,)
        )
        
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        data = [{
            'temperature': row['temperature'],
            'humidity': row['humidity'],
            'created_at': row['created_at'].isoformat()
        } for row in rows]
        
        return jsonify(data), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Vrátit statistiku posledních 24 hodin"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        hours = request.args.get('hours', 24, type=int)
        since = datetime.now() - timedelta(hours=hours)
        
        cur.execute("""
            SELECT 
                AVG(temperature) as avg_temp,
                MAX(temperature) as max_temp,
                MIN(temperature) as min_temp,
                AVG(humidity) as avg_humidity,
                MAX(humidity) as max_humidity,
                MIN(humidity) as min_humidity,
                COUNT(*) as count
            FROM sensor_data 
            WHERE created_at > %s
        """, (since,))
        
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        return jsonify({
            'temperature': {
                'average': round(row['avg_temp'], 2) if row['avg_temp'] else None,
                'max': round(row['max_temp'], 2) if row['max_temp'] else None,
                'min': round(row['min_temp'], 2) if row['min_temp'] else None
            },
            'humidity': {
                'average': round(row['avg_humidity'], 2) if row['avg_humidity'] else None,
                'max': round(row['max_humidity'], 2) if row['max_humidity'] else None,
                'min': round(row['min_humidity'], 2) if row['min_humidity'] else None
            },
            'measurements': row['count']
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    print("Spuštění Flask serveru na 0.0.0.0:5000...")
    app.run(host='0.0.0.0', port=5000, debug=False)
