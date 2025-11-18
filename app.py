from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import os
import datetime
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    import sqlite3

app = Flask(__name__)
CORS(app)

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    else:
        import sqlite3
        return sqlite3.connect('simple_app.db')

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id SERIAL PRIMARY KEY, name TEXT, phone TEXT UNIQUE, password_hash TEXT, rating REAL DEFAULT 5.0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS rides
                     (id SERIAL PRIMARY KEY, driver_id INTEGER, from_location TEXT, to_location TEXT, 
                      departure_time TIMESTAMP, available_seats INTEGER, price REAL, description TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY, name TEXT, phone TEXT UNIQUE, password_hash TEXT, rating REAL DEFAULT 5.0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS rides
                     (id INTEGER PRIMARY KEY, driver_id INTEGER, from_location TEXT, to_location TEXT, 
                      departure_time TEXT, available_seats INTEGER, price REAL, description TEXT,
                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@app.route('/api/users/register', methods=['POST'])
def register():
    init_db()  # Ensure DB exists
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        password = data.get('password')
        
        # Simple hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id FROM users WHERE phone = %s" if os.environ.get('DATABASE_URL') else "SELECT id FROM users WHERE phone = ?", (phone,))
        if c.fetchone():
            return jsonify({'error': 'Telefon již registrován'}), 409
        
        # Insert user
        if os.environ.get('DATABASE_URL'):
            c.execute("INSERT INTO users (name, phone, password_hash) VALUES (%s, %s, %s) RETURNING id",
                      (name, phone, password_hash))
            user_id = c.fetchone()[0]
        else:
            c.execute("INSERT INTO users (name, phone, password_hash) VALUES (?, ?, ?)",
                      (name, phone, password_hash))
            user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Registrace úspěšná', 'user_id': user_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    init_db()  # Ensure DB exists
    try:
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        
        # Simple hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        c = conn.cursor()
        if os.environ.get('DATABASE_URL'):
            c.execute("SELECT id, name, rating FROM users WHERE phone = %s AND password_hash = %s",
                      (phone, password_hash))
        else:
            c.execute("SELECT id, name, rating FROM users WHERE phone = ? AND password_hash = ?",
                      (phone, password_hash))
        user = c.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'message': 'Přihlášení úspěšné',
                'user_id': user[0],
                'name': user[1],
                'rating': float(user[2]) if user[2] is not None else 5.0
            }), 200
        else:
            return jsonify({'error': 'Neplatné přihlašovací údaje'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/offer', methods=['POST'])
def offer_ride():
    init_db()
    try:
        data = request.get_json()
        conn = get_db_connection()
        c = conn.cursor()
        
        if os.environ.get('DATABASE_URL'):
            c.execute("INSERT INTO rides (driver_id, from_location, to_location, departure_time, available_seats, price, description) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                      (data.get('driver_id'), data.get('from_location'), data.get('to_location'), 
                       data.get('departure_time'), data.get('available_seats'), data.get('price'), data.get('description', '')))
        else:
            c.execute("INSERT INTO rides (driver_id, from_location, to_location, departure_time, available_seats, price, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (data.get('driver_id'), data.get('from_location'), data.get('to_location'), 
                       data.get('departure_time'), data.get('available_seats'), data.get('price'), data.get('description', '')))
        
        conn.commit()
        conn.close()
        return jsonify({'message': 'Jízda nabídnuta', 'ride_id': c.lastrowid}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/search', methods=['GET'])
def search_rides():
    try:
        from_location = request.args.get('from', '')
        
        # Mock ride data
        mock_rides = [
            {
                'id': 1,
                'driver_id': 1,
                'from_location': 'Praha',
                'to_location': 'Brno',
                'departure_time': '2025-11-18 15:00',
                'available_seats': 3,
                'price_per_person': 200,
                'description': 'Pohodová jízda',
                'driver_name': 'Jan Novák',
                'driver_rating': 4.8
            },
            {
                'id': 2,
                'driver_id': 2,
                'from_location': 'Brno',
                'to_location': 'Praha',
                'departure_time': '2025-11-18 17:30',
                'available_seats': 2,
                'price_per_person': 250,
                'description': 'Rychlá jízda',
                'driver_name': 'Marie Svobodová',
                'driver_rating': 4.9
            },
            {
                'id': 3,
                'driver_id': 3,
                'from_location': 'Ostrava',
                'to_location': 'Praha',
                'departure_time': '2025-11-18 14:00',
                'available_seats': 1,
                'price_per_person': 300,
                'description': 'Komfortní auto',
                'driver_name': 'Petr Dvořák',
                'driver_rating': 5.0
            }
        ]
        
        # Filter by from_location if provided
        if from_location:
            result = [ride for ride in mock_rides if from_location.lower() in ride['from_location'].lower()]
        else:
            result = mock_rides
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)