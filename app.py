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
    init_db()
    try:
        from_location = request.args.get('from', '')
        conn = get_db_connection()
        c = conn.cursor()
        
        if from_location:
            if os.environ.get('DATABASE_URL'):
                c.execute("SELECT r.id, r.driver_id, r.from_location, r.to_location, r.departure_time, r.available_seats, r.price, r.description, u.name, u.rating FROM rides r JOIN users u ON r.driver_id = u.id WHERE r.from_location ILIKE %s", (f'%{from_location}%',))
            else:
                c.execute("SELECT r.id, r.driver_id, r.from_location, r.to_location, r.departure_time, r.available_seats, r.price, r.description, u.name, u.rating FROM rides r JOIN users u ON r.driver_id = u.id WHERE r.from_location LIKE ?", (f'%{from_location}%',))
        else:
            if os.environ.get('DATABASE_URL'):
                c.execute("SELECT r.id, r.driver_id, r.from_location, r.to_location, r.departure_time, r.available_seats, r.price, r.description, u.name, u.rating FROM rides r JOIN users u ON r.driver_id = u.id ORDER BY r.created_at DESC LIMIT 20")
            else:
                c.execute("SELECT r.id, r.driver_id, r.from_location, r.to_location, r.departure_time, r.available_seats, r.price, r.description, u.name, u.rating FROM rides r JOIN users u ON r.driver_id = u.id ORDER BY r.created_at DESC LIMIT 20")
        
        rides = c.fetchall()
        conn.close()
        
        result = []
        for ride in rides:
            result.append({
                'id': ride[0],
                'driver_id': ride[1],
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': str(ride[4]) if ride[4] else '',
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'description': ride[7] or '',
                'driver_name': ride[8],
                'driver_rating': float(ride[9]) if ride[9] else 5.0
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)