from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import sqlite3
import hashlib
import datetime
import os
import json
import signal
import sys
import requests
from backend_search_api import create_search_routes

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Slovník pro ukládání pozic uživatelů
user_locations = {}



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/debug')
def debug_panel():
    return render_template('debug.html')

@app.route('/api/status')
def api_status():
    return jsonify({
        'message': 'Spolujízda API server běží!',
        'endpoints': [
            'POST /api/users/register',
            'POST /api/users/login', 
            'POST /api/rides/offer',
            'GET /api/rides/search',
            'WebSocket /socket.io - real-time lokalizace'
        ]
    })

@app.route('/api/cities', methods=['GET'])
def get_cities():
    """Vrací seznam měst pro autocomplete"""
    cities = [
        'Praha', 'Brno', 'Ostrava', 'Plzeň', 'Liberec', 'Olomouc', 'Ústí nad Labem',
        'České Budějovice', 'Hradec Králové', 'Pardubice', 'Zlín', 'Havířov',
        'Kladno', 'Most', 'Opava', 'Frýdek-Místek', 'Karviná', 'Jihlava',
        'Teplice', 'Děčín', 'Karlovy Vary', 'Jablonec nad Nisou', 'Mladá Boleslav',
        'Prostějov', 'Přerov', 'Česká Lípa', 'Třebíč', 'Třinec', 'Tábor',
        'Znojmo', 'Příbram', 'Cheb', 'Trutnov', 'Chomutov', 'Kolín', 'Písek'
    ]
    return jsonify(cities)

@app.route('/api/users/locations', methods=['GET'])
def get_user_locations():
    """Vrací aktuální polohy uživatelů"""
    return jsonify(user_locations)

@app.route('/api/users/list', methods=['GET'])
def list_users():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT id, name, phone, password_hash, created_at FROM users ORDER BY created_at DESC')
        users = c.fetchall()
        conn.close()
        
        result = []
        for user in users:
            result.append({
                'id': user[0],
                'name': user[1],
                'phone': user[2],
                'password_hash': user[3],
                'created_at': user[4]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/password/<password>', methods=['GET'])
def test_password_hash(password):
    import hashlib
    hash_result = hashlib.sha256(password.encode()).hexdigest()
    return jsonify({
        'original_password': password,
        'sha256_hash': hash_result
    })

DATABASE = 'spolujizda.db'

def init_db():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Tabulka uživatelů
        c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  phone TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE,
                  password_hash TEXT NOT NULL,
                  rating REAL DEFAULT 5.0,
                  total_rides INTEGER DEFAULT 0,
                  verified BOOLEAN DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Tabulka jízd
        c.execute('''CREATE TABLE IF NOT EXISTS rides
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  from_location TEXT NOT NULL,
                  to_location TEXT NOT NULL,
                  departure_time TEXT NOT NULL,
                  available_seats INTEGER,
                  price_per_person INTEGER,
                  route_waypoints TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        # Tabulka rezervací
        c.execute('''CREATE TABLE IF NOT EXISTS reservations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ride_id INTEGER,
                  passenger_id INTEGER,
                  seats_reserved INTEGER DEFAULT 1,
                  status TEXT DEFAULT 'pending',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (ride_id) REFERENCES rides (id),
                  FOREIGN KEY (passenger_id) REFERENCES users (id))''')
        
        # Tabulka zpráv
        c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ride_id INTEGER,
                  sender_id INTEGER,
                  message TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (ride_id) REFERENCES rides (id),
                  FOREIGN KEY (sender_id) REFERENCES users (id))''')
        
        # Tabulka hodnocení
        c.execute('''CREATE TABLE IF NOT EXISTS ratings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  ride_id INTEGER,
                  rater_id INTEGER,
                  rated_id INTEGER,
                  rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                  comment TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (ride_id) REFERENCES rides (id),
                  FOREIGN KEY (rater_id) REFERENCES users (id),
                  FOREIGN KEY (rated_id) REFERENCES users (id))''')
        
        # Tabulka blokovaných uživatelů
        c.execute('''CREATE TABLE IF NOT EXISTS blocked_users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  blocker_id INTEGER,
                  blocked_id INTEGER,
                  reason TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (blocker_id) REFERENCES users (id),
                  FOREIGN KEY (blocked_id) REFERENCES users (id))''')
        
        # Tabulka pravidelných jízd
        c.execute('''CREATE TABLE IF NOT EXISTS recurring_rides
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  from_location TEXT NOT NULL,
                  to_location TEXT NOT NULL,
                  departure_time TEXT NOT NULL,
                  days_of_week TEXT NOT NULL,
                  available_seats INTEGER,
                  price_per_person INTEGER,
                  active BOOLEAN DEFAULT 1,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        # Tabulka statistik uživatelů
        c.execute('''CREATE TABLE IF NOT EXISTS user_stats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER UNIQUE,
                  total_rides INTEGER DEFAULT 0,
                  total_distance REAL DEFAULT 0,
                  co2_saved REAL DEFAULT 0,
                  money_saved REAL DEFAULT 0,
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        # Tabulka SMS kódů
        c.execute('''CREATE TABLE IF NOT EXISTS sms_codes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  phone TEXT NOT NULL,
                  code TEXT NOT NULL,
                  expires_at TIMESTAMP NOT NULL,
                  used BOOLEAN DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        # Přidá chybějící sloupce do existujících tabulek
        try:
            c.execute('ALTER TABLE users ADD COLUMN rating REAL DEFAULT 5.0')
        except sqlite3.OperationalError:
            pass  # Sloupec už existuje
        
        try:
            c.execute('ALTER TABLE users ADD COLUMN email TEXT UNIQUE')
        except sqlite3.OperationalError:
            pass  # Sloupec už existuje
        
        conn.commit()
        conn.close()
        print("Všechny tabulky vytvořeny")
    except Exception as e:
        print(f"Chyba při vytváření tabulek: {e}")
        if 'conn' in locals():
            conn.close()
        raise

@app.route('/api/users/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        password = data.get('password')
        
        email = data.get('email', '').strip()
        password_confirm = data.get('password_confirm')
        
        if not all([name, phone, password, password_confirm]):
            return jsonify({'error': 'Jméno, telefon, heslo a potvrzení hesla jsou povinné'}), 400
        
        if password != password_confirm:
            return jsonify({'error': 'Hesla se neshodují'}), 400
        
        # Normalizuje telefonní číslo - odebere všechny mezery a speciální znaky
        phone_clean = ''.join(filter(str.isdigit, phone))
        
        # Odstraní předvolbu
        if phone_clean.startswith('420'):
            phone_clean = phone_clean[3:]
        
        # Ověří formát (9 číslic)
        if len(phone_clean) != 9:
            return jsonify({'error': 'Neplatný formát telefonu (9 číslic)'}), 400
        
        # Vždy uloží ve formátu +420xxxxxxxxx
        phone_full = f'+420{phone_clean}'
        
        # Validace emailu pokud je zadán
        if email and '@' not in email:
            return jsonify({'error': 'Neplatný formát emailu'}), 400
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Zkontroluje existující telefon
        c.execute('SELECT id FROM users WHERE phone = ?', (phone_full,))
        if c.fetchone():
            conn.close()
            return jsonify({'error': 'Toto telefonní číslo je již registrováno'}), 409
        
        # Zkontroluje existující email pokud je zadán
        if email:
            c.execute('SELECT id FROM users WHERE email = ?', (email,))
            if c.fetchone():
                conn.close()
                return jsonify({'error': 'Tento email je již registrován'}), 409
        
        try:
            # Registruje uživatele
            c.execute('INSERT INTO users (name, phone, email, password_hash, rating) VALUES (?, ?, ?, ?, ?)',
                     (name, phone_full, email if email else None, password_hash, 5.0))
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Uživatel úspěšně registrován'}), 201
        except sqlite3.Error as e:
            conn.close()
            return jsonify({'error': f'Chyba databáze: {str(e)}'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        login_field = data.get('phone')  # Může být telefon nebo email
        password = data.get('password')
        
        if not all([login_field, password]):
            return jsonify({'error': 'Telefon/email a heslo jsou povinné'}), 400
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Zkusí přihlášení pomocí telefonu nebo emailu
        if '@' in login_field:
            # Přihlášení emailem
            c.execute('SELECT id, name, rating FROM users WHERE email = ? AND password_hash = ?',
                     (login_field, password_hash))
        else:
            # Přihlášení telefonem - normalizuj formát
            phone_clean = ''.join(filter(str.isdigit, login_field))
            if phone_clean.startswith('420'):
                phone_clean = phone_clean[3:]
            phone_full = f'+420{phone_clean}'
            
            c.execute('SELECT id, name, rating FROM users WHERE phone = ? AND password_hash = ?',
                     (phone_full, password_hash))
        
        user = c.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'message': 'Přihlášení úspěšné',
                'user_id': user[0],
                'name': user[1],
                'rating': user[2] or 5.0
            }), 200
        else:
            return jsonify({'error': 'Neplatné přihlašovací údaje'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/offer', methods=['POST'])
def offer_ride():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        from_location = data.get('from_location')
        to_location = data.get('to_location')
        departure_time = data.get('departure_time')
        available_seats = data.get('available_seats')
        price_per_person = data.get('price_per_person')
        route_waypoints = json.dumps(data.get('route_waypoints', []))
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''INSERT INTO rides 
                     (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints))
        conn.commit()
        conn.close()
        
        ride_id = c.lastrowid
        return jsonify({
            'message': 'Jízda úspěšně nabídnuta',
            'ride_id': ride_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/search', methods=['GET'])
def search_rides():
    try:
        from_location = request.args.get('from', '')
        to_location = request.args.get('to', '')
        user_lat = float(request.args.get('lat', 0))
        user_lng = float(request.args.get('lng', 0))
        user_id = int(request.args.get('user_id', 0))
        max_price = request.args.get('max_price')
        search_range = float(request.args.get('range', 50))
        include_own = request.args.get('include_own', 'false').lower() == 'true'
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Základní dotaz - všechny jízdy
        query = '''SELECT r.*, COALESCE(u.name, 'Neznámý řidič'), COALESCE(u.rating, 5.0) FROM rides r 
                   LEFT JOIN users u ON r.user_id = u.id
                   WHERE 1=1'''
        params = []
        
        print(f"=== HLEDÁNÍ JÍzD ===")
        print(f"User ID: {user_id}, Include own: {include_own}")
        print(f"GPS pozice: {user_lat}, {user_lng}")
        print(f"Rozsah hledání: {search_range} km")
        print(f"Max price: {max_price}")
        
        # Bezpečná kontrola pro max_price - filtruje, jen pokud je hodnota zadaná a je to číslo
        if max_price and str(max_price).isdigit():
            query += ' AND r.price_per_person <= ?'
            params.append(int(max_price))
        
        # Hodnocení odstraňeno z filtrace
        
        c.execute(query, params)
        rides = c.fetchall()
        print(f"Nalezeno {len(rides)} jízd v databázi")
        
        # Získej rezervace uživatele
        reservations = []
        if user_id > 0:
            c.execute('SELECT ride_id FROM reservations WHERE passenger_id = ? AND status = "confirmed"', (user_id,))
            reservations = [row[0] for row in c.fetchall()]
        
        conn.close()
        
        import math
        
        def calculate_distance(lat1, lng1, lat2, lng2):
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        # Odstraněna složitá funkce point_to_line_distance
        
        result = []
        for ride in rides:
            # Bezpečné načítání waypoints, aby chyba v jedné jízdě neshodila celé hledání
            try:
                waypoints = json.loads(ride[7]) if ride[7] else []
            except json.JSONDecodeError:
                print(f"Chyba dekódování JSON pro jízdu ID: {ride[0]}. Waypoints budou ignorovány.")
                waypoints = []
            
            # Výchozí vzdálenost je mimo rozsah, takže jízda bude ignorována, pokud se nenajde bližší bod
            distance = search_range + 1
            
            if user_lat and user_lng:
                min_distance = float('inf')
                if waypoints:
                    for waypoint in waypoints:
                        # Bezpečnostní kontrola, zda waypoint obsahuje platné souřadnice
                        if isinstance(waypoint, dict) and 'lat' in waypoint and 'lng' in waypoint:
                            wp_distance = calculate_distance(user_lat, user_lng, waypoint['lat'], waypoint['lng'])
                            min_distance = min(min_distance, wp_distance)
                
                if min_distance != float('inf'):
                    distance = min_distance
            else:
                # Pokud uživatel nemá GPS, nelze filtrovat podle vzdálenosti
                distance = 0
            
            print(f"Jízda {ride[0]}: {ride[2]} -> {ride[3]}, vzdálenost: {distance:.1f} km")
            
            # Zobraz jízdy v nastaveném rozsahu
            if user_lat and user_lng and distance > search_range:
                continue
            
            # Urč typ jízdy
            is_own = (user_id > 0 and ride[1] == user_id)
            is_reserved = (ride[0] in reservations)
            
            result.append({
                'id': ride[0],
                'user_id': ride[1],
                'driver_name': ride[10],
                'driver_rating': ride[11] or 5.0,
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': ride[4],
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'route_waypoints': waypoints,
                'distance': round(distance, 1),
                'is_own': is_own,
                'is_reserved': is_reserved
            })
        
        result.sort(key=lambda x: x['distance'])
        print(f"Vracím {len(result)} jízd po filtrování")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Chyba v search_rides: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/search', methods=['POST'])
def search_user():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Zadejte email nebo telefon'}), 400
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Hledání podle emailu nebo telefonu
        if '@' in query:
            c.execute('SELECT id, name, phone, email, rating FROM users WHERE email LIKE ?', (f'%{query}%',))
        else:
            # Normalizace telefonu - hledá všechny formáty
            phone_clean = ''.join(filter(str.isdigit, query))
            
            # Hledá různé formáty telefonu
            search_patterns = [
                f'%{phone_clean}%',
                f'%+420{phone_clean}%',
                f'%420{phone_clean}%'
            ]
            
            # Pokud začíná 420, zkusí i bez něj
            if phone_clean.startswith('420'):
                search_patterns.append(f'%{phone_clean[3:]}%')
            
            c.execute('SELECT id, name, phone, email, rating FROM users WHERE ' + 
                     ' OR '.join(['phone LIKE ?' for _ in search_patterns]), 
                     search_patterns)
        
        user = c.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        return jsonify({
            'id': user[0],
            'name': user[1],
            'phone': user[2],
            'email': user[3] or '',
            'rating': user[4] or 5.0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/all', methods=['GET'])
def get_all_rides():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''SELECT r.*, u.name FROM rides r 
                     LEFT JOIN users u ON r.user_id = u.id
                     ORDER BY r.created_at DESC''')
        rides = c.fetchall()
        conn.close()
        
        result = []
        for ride in rides:
            result.append({
                'id': ride[0],
                'user_id': ride[1],
                'driver_name': ride[8] or 'Neznámý řidič',
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': ride[4],
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'created_at': ride[8]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# SocketIO events pro real-time lokalizaci
@socketio.on('connect')
def handle_connect():
    print('Uživatel se připojil')
    emit('connected', {'message': 'Připojeno k serveru'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Uživatel se odpojil')

@socketio.on('update_location')
def handle_location_update(data):
    user_id = data.get('user_id')
    lat = data.get('lat')
    lng = data.get('lng')
    
    if user_id and lat and lng:
        user_locations[user_id] = {
            'lat': lat,
            'lng': lng,
            'timestamp': datetime.datetime.now().isoformat()
        }
        # Pošli aktualizaci všem připojeným klientům
        emit('location_updated', {
            'user_id': user_id,
            'lat': lat,
            'lng': lng
        }, broadcast=True)

@socketio.on('get_user_location')
def handle_get_location(data):
    user_id = data.get('user_id')
    if user_id in user_locations:
        emit('user_location', {
            'user_id': user_id,
            'location': user_locations[user_id]
        })
    else:
        emit('user_location', {
            'user_id': user_id,
            'location': None
        })

# Real-time chat
@socketio.on('join_ride_chat')
def handle_join_chat(data):
    ride_id = data.get('ride_id')
    user_name = data.get('user_name')
    join_room(f'ride_{ride_id}')
    emit('user_joined', {
        'message': f'{user_name} se připojil do chatu',
        'timestamp': datetime.datetime.now().isoformat()
    }, room=f'ride_{ride_id}')

@socketio.on('send_chat_message')
def handle_chat_message(data):
    ride_id = data.get('ride_id')
    user_name = data.get('user_name')
    message = data.get('message')
    
    # Uloží zprávu do databáze
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Získá sender_id z dat
    sender_id = data.get('user_name', 'Neznámý')
    c.execute('INSERT INTO messages (ride_id, sender_id, message) VALUES (?, ?, ?)',
             (ride_id, sender_id, message))
    conn.commit()
    conn.close()
    
    emit('new_chat_message', {
        'user_name': user_name,
        'message': message,
        'timestamp': datetime.datetime.now().isoformat()
    }, room=f'ride_{ride_id}')

@socketio.on('leave_ride_chat')
def handle_leave_chat(data):
    ride_id = data.get('ride_id')
    user_name = data.get('user_name')
    leave_room(f'ride_{ride_id}')
    emit('user_left', {
        'message': f'{user_name} opustil chat',
        'timestamp': datetime.datetime.now().isoformat()
    }, room=f'ride_{ride_id}')

# Sdílení polohy v reálném čase
@socketio.on('share_live_location')
def handle_live_location(data):
    ride_id = data.get('ride_id')
    user_name = data.get('user_name')
    lat = data.get('lat')
    lng = data.get('lng')
    
    emit('live_location_update', {
        'user_name': user_name,
        'lat': lat,
        'lng': lng,
        'timestamp': datetime.datetime.now().isoformat()
    }, room=f'ride_{ride_id}')

# Přímý chat mezi uživateli
@socketio.on('join_direct_chat')
def handle_join_direct_chat(data):
    target_user = data.get('target_user')
    user_name = data.get('user_name')
    
    # Vytvoří jedinečný room pro dva uživatele
    room_name = f'direct_{min(user_name, target_user)}_{max(user_name, target_user)}'
    join_room(room_name)
    
    emit('user_joined', {
        'message': f'{user_name} se připojil k chatu',
        'timestamp': datetime.datetime.now().isoformat()
    }, room=room_name)

@socketio.on('send_direct_message')
def handle_direct_message(data):
    target_user = data.get('target_user')
    user_name = data.get('user_name')
    message = data.get('message')
    
    room_name = f'direct_{min(user_name, target_user)}_{max(user_name, target_user)}'
    
    emit('direct_message_received', {
        'from_user': user_name,
        'message': message,
        'timestamp': datetime.datetime.now().isoformat()
    }, room=room_name)

@socketio.on('leave_direct_chat')
def handle_leave_direct_chat(data):
    target_user = data.get('target_user')
    user_name = data.get('user_name')
    
    room_name = f'direct_{min(user_name, target_user)}_{max(user_name, target_user)}'
    leave_room(room_name)
    
    emit('user_left', {
        'message': f'{user_name} opustil chat',
        'timestamp': datetime.datetime.now().isoformat()
    }, room=room_name)

# Požadavek na polohu uživatele
@socketio.on('request_user_location')
def handle_location_request(data):
    target_user = data.get('target_user')
    requester = data.get('requester')
    
    # Zkontroluje, zda je cílový uživatel online a má polohu
    if target_user in user_locations:
        location = user_locations[target_user]
        emit('user_location_response', {
            'user_name': target_user,
            'lat': location['lat'],
            'lng': location['lng'],
            'timestamp': location['timestamp']
        })
    else:
        emit('user_location_response', {
            'user_name': target_user,
            'lat': None,
            'lng': None
        })

# API pro rezervace
@app.route('/api/reservations/create', methods=['POST'])
def create_reservation():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        passenger_id = data.get('passenger_id')
        
        if not passenger_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        seats_reserved = data.get('seats_reserved', 1)
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Zkontroluje dostupnost míst
        c.execute('SELECT available_seats FROM rides WHERE id = ?', (ride_id,))
        ride = c.fetchone()
        
        if not ride or ride[0] < seats_reserved:
            return jsonify({'error': 'Nedostatek volných míst'}), 400
        
        # Vytvoří rezervaci
        c.execute('INSERT INTO reservations (ride_id, passenger_id, seats_reserved) VALUES (?, ?, ?)',
                 (ride_id, passenger_id, seats_reserved))
        
        # Aktualizuje počet volných míst
        c.execute('UPDATE rides SET available_seats = available_seats - ? WHERE id = ?',
                 (seats_reserved, ride_id))
        
        # Nastav status rezervace na confirmed
        c.execute('UPDATE reservations SET status = "confirmed" WHERE ride_id = ? AND passenger_id = ?',
                 (ride_id, passenger_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Rezervace úspěšně vytvořena'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro zprávy
@app.route('/api/messages/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        sender_id = data.get('sender_id')
        
        if not sender_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        message = data.get('message')
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO messages (ride_id, sender_id, message) VALUES (?, ?, ?)',
                 (ride_id, sender_id, message))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Zpráva odeslána'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro hodnocení
@app.route('/api/ratings/create', methods=['POST'])
def create_rating():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        rater_id = data.get('rater_id')
        
        if not rater_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        rated_id = data.get('rated_id')
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO ratings (ride_id, rater_id, rated_id, rating, comment) VALUES (?, ?, ?, ?, ?)',
                 (ride_id, rater_id, rated_id, rating, comment))
        
        # Aktualizace průměrného hodnocení
        c.execute('SELECT AVG(rating) FROM ratings WHERE rated_id = ?', (rated_id,))
        avg_rating = c.fetchone()[0]
        if avg_rating:
            c.execute('UPDATE users SET rating = ? WHERE id = ?', (avg_rating, rated_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Hodnocení odesláno'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro blokování uživatelů
@app.route('/api/users/block', methods=['POST'])
def block_user():
    try:
        data = request.get_json()
        blocker_id = data.get('blocker_id')
        
        if not blocker_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        blocked_id = data.get('blocked_id')
        reason = data.get('reason', '')
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('INSERT INTO blocked_users (blocker_id, blocked_id, reason) VALUES (?, ?, ?)',
                 (blocker_id, blocked_id, reason))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Uživatel zablokován'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro statistiky
@app.route('/api/users/<int:user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    try:
        # Ověří, že uživatel existuje
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if not c.fetchone():
            conn.close()
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT * FROM user_stats WHERE user_id = ?', (user_id,))
        stats = c.fetchone()
        
        if not stats:
            c.execute('INSERT INTO user_stats (user_id) VALUES (?)', (user_id,))
            conn.commit()
            stats = (None, user_id, 0, 0, 0, 0)
        
        conn.close()
        
        return jsonify({
            'total_rides': stats[2],
            'total_distance': stats[3],
            'co2_saved': stats[4],
            'money_saved': stats[5]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro pravidelné jízdy
@app.route('/api/rides/recurring', methods=['POST'])
def create_recurring_ride():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        from_location = data.get('from_location')
        to_location = data.get('to_location')
        departure_time = data.get('departure_time')
        days_of_week = ','.join(data.get('days_of_week', []))
        available_seats = data.get('available_seats')
        price_per_person = data.get('price_per_person')
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''INSERT INTO recurring_rides 
                     (user_id, from_location, to_location, departure_time, days_of_week, available_seats, price_per_person)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (user_id, from_location, to_location, departure_time, days_of_week, available_seats, price_per_person))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Pravidelná jízda vytvořena'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/recurring', methods=['GET'])
def get_recurring_rides():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''SELECT r.*, u.name FROM recurring_rides r
                     LEFT JOIN users u ON r.user_id = u.id
                     WHERE r.active = 1 AND (r.user_id = ? OR ? = 0)''', (user_id, user_id))
        rides = c.fetchall()
        conn.close()
        
        result = []
        for ride in rides:
            result.append({
                'id': ride[0],
                'driver_name': ride[8] or 'Neznámý řidič',
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': ride[4],
                'days_of_week': ride[5].split(','),
                'available_seats': ride[6],
                'price_per_person': ride[7],
                'active': ride[8]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    shutdown_in_progress = False
    
    def signal_handler(sig, frame):
        global shutdown_in_progress
        if shutdown_in_progress:
            return
        shutdown_in_progress = True
        
        print('\n⚠️  Ukončuji server...')
        print('✅ Server úspěšně ukončen')
        sys.exit(0)
    
    # Registruje signal handler pro Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("Inicializace databáze...")
        init_db()
        print("Databáze inicializována")
        
        # Přidání pokročilých search API routes
        try:
            create_search_routes(app)
            print("Pokročilé vyhledávání aktivováno")
        except Exception as e:
            print(f"Chyba při aktivaci pokročilého vyhledávání: {e}")
        
        # Přidá HTTPS hlavičky pro mobilní zařízení
        @app.after_request
        def after_request(response):
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # Mobilní cache fix
            user_agent = request.headers.get('User-Agent', '')
            if any(mobile in user_agent for mobile in ['Mobile', 'Android', 'iPhone', 'iPad']):
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
            
            return response
        
        print("Server se spouští na:")
        print("  Lokální: http://localhost:8080")
        print("  Veřejná: http://0.0.0.0:8080")
        print("  🔴 Stiskni Ctrl+C pro ukončení")
        
        # Získá IP adresu
        import socket
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"  Síťová: http://{local_ip}:8080")
        except:
            pass
        
        port = int(os.environ.get('PORT', 8080))
        socketio.run(app, debug=False, host='0.0.0.0', port=port, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"Chyba při spuštění serveru: {e}")
        import traceback
        traceback.print_exc()
        input("Stiskněte Enter pro ukončení...")