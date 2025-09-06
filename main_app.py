from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, Response
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import sqlite3
import hashlib
import datetime
import os
import json
import signal
import sys
import requests
import stripe
# from backend_search_api import create_search_routes

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Configure SQLAlchemy
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+psycopg2://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///spolujizda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Suppress a warning

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ROBOTS.TXT - NEJVYŠŠÍ PRIORITA
@app.route('/robots.txt')
def robots():
    return '''User-agent: *
Allow: /
Allow: /search
Allow: /terms
Allow: /privacy
Disallow: /api/
Disallow: /admin/
Disallow: /debug
Disallow: /test
Disallow: /payment-*
Disallow: /qr-payment

Sitemap: https://www.sveztese.cz/sitemap.xml''', 200, {'Content-Type': 'text/plain'}

# Rate limiting
from collections import defaultdict
from time import time
request_counts = defaultdict(list)

def rate_limit(max_requests=10, window=60):
    def decorator(f):
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            now = time()
            # Vyčisti staré požadavky
            request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] if now - req_time < window]
            # Zkontroluj limit
            if len(request_counts[client_ip]) >= max_requests:
                return jsonify({'error': 'Příliš mnoho požadavků'}), 429
            request_counts[client_ip].append(now)
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
app.debug = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app, resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"], "allow_headers": ["Content-Type"]}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Stripe konfigurace
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_51QYOhzP8xJKqGzKvYourSecretKey')  # Nastav v produkci
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_51QYOhzP8xJKqGzKvYourPublishableKey')

# Konfigurace provize
COMMISSION_RATE = 0.10  # 10% provize
YOUR_STRIPE_ACCOUNT_ID = 'acct_YourConnectedAccountId'  # Váš Stripe Connect účet

# Slovník pro ukládání pozic uživatelů
user_locations = {}


print("--- main_app.py is being loaded! ---")



@app.route('/')
def home():
    return render_template('app.html')

@app.route('/fixed')
def fixed_home():
    return render_template('index_fixed.html')

@app.route('/debug')
def debug_panel():
    return render_template('debug.html')

@app.route('/health')
def health_check():
    import datetime
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.datetime.now().isoformat(),
        'robots_txt': f'{request.host_url}robots.txt',
        'sitemap_xml': f'{request.host_url}sitemap.xml'
    }), 200

@app.route('/test')
def test_page():
    return render_template('test.html')

@app.route('/search')
def search_page():
    return render_template('search.html')

@app.route('/api/status')
def api_status():
    return jsonify({
        'message': 'Spolujízda API server běží!',
        'robots_txt_url': f'{request.host_url}robots.txt',
        'sitemap_url': f'{request.host_url}sitemap.xml',
        'endpoints': [
            'POST /api/users/register',
            'POST /api/users/login', 
            'POST /api/rides/offer',
            'GET /api/rides/search',
            'WebSocket /socket.io - real-time lokalizace'
        ]
    })

@app.route('/api/rides/driver/<int:user_id>')
def get_driver_rides(user_id):
    try:
        with db.session.begin():
            rides = db.session.execute(db.text('''
                SELECT r.*, COUNT(res.id) as reservations_count
                FROM rides r
                LEFT JOIN reservations res ON r.id = res.ride_id AND res.status != 'cancelled'
                WHERE r.user_id = :user_id
                GROUP BY r.id
                ORDER BY r.departure_time ASC
            '''), {'user_id': user_id}).fetchall()
        
        result = []
        for ride in rides:
            result.append({
                'id': ride[0],
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': ride[4].isoformat(),
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'reservations_count': ride[9] or 0
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/<int:ride_id>/reservations')
def get_ride_reservations(ride_id):
    try:
        with db.session.begin():
            reservations = db.session.execute(db.text('''
                SELECT res.seats_reserved, u.name, u.phone
                FROM reservations res
                JOIN users u ON res.passenger_id = u.id
                WHERE res.ride_id = :ride_id AND res.status != 'cancelled'
            '''), {'ride_id': ride_id}).fetchall()
        
        result = []
        for res in reservations:
            result.append({
                'seats_reserved': res[0],
                'passenger_name': res[1],
                'passenger_phone': res[2]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/<int:ride_id>/messages')
def get_ride_messages(ride_id):
    try:
        with db.session.begin():
            messages = db.session.execute(db.text('''
                SELECT m.message, m.created_at, m.sender_id, u.name as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.ride_id = :ride_id
                ORDER BY m.created_at ASC
            '''), {'ride_id': ride_id}).fetchall()
        
        result = []
        for msg in messages:
            result.append({
                'message': msg[0],
                'created_at': msg[1],
                'sender_id': msg[2],
                'sender_name': msg[3]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations/user/<int:user_id>')
def reservations_test(user_id):
    try:
        with db.session.begin():
            reservations = db.session.execute(db.text('''
                SELECT res.id, res.seats_reserved, res.status, res.created_at,
                       r.from_location, r.to_location, r.departure_time, r.price_per_person,
                       u.name as driver_name, u.phone as driver_phone
                FROM reservations res
                JOIN rides r ON res.ride_id = r.id
                JOIN users u ON r.user_id = u.id
                WHERE res.passenger_id = :user_id AND res.status != 'cancelled'
                ORDER BY r.departure_time ASC
            '''), {'user_id': user_id}).fetchall()
        
        result = []
        for res in reservations:
            result.append({
                'reservation_id': res[0],
                'seats_reserved': res[1],
                'status': res[2],
                'created_at': res[3],
                'from_location': res[4],
                'to_location': res[5],
                'departure_time': res[6].isoformat(),
                'price_per_person': res[7],
                'driver_name': res[8],
                'driver_phone': res[9]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/list', methods=['GET'])
def list_users():
    try:
        with db.session.begin():
            users = db.session.execute(db.text('SELECT id, name, phone, password_hash, created_at FROM users ORDER BY created_at DESC')).fetchall()
        
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

@app.route('/api/users/get_hash/<phone>', methods=['GET'])
def get_user_hash(phone):
    try:
        with db.session.begin():
            password_hash = db.session.execute(db.text('SELECT password_hash FROM users WHERE phone = :phone'), {'phone': phone}).fetchone()
        
        if password_hash:
            return jsonify({'password_hash': password_hash[0]}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Removed SQLite-specific database initialization. Database migrations are now handled by Alembic and PostgreSQL.
# DATABASE = 'spolujizda.db'
# def init_db():
#    pass


@app.route('/api/users/register', methods=['POST'])
@rate_limit(max_requests=5, window=300)  # Max 5 registrací za 5 minut
def register():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        phone = data.get('phone')
        password = data.get('password')
        
        # Validace jména
        forbidden_names = ['neznámý řidič', 'neznámý', 'unknown', 'driver', 'řidič', 'neznámy ridic', 'test', 'user', 'anonym', 'guest', 'admin', 'null', 'undefined', 'testovací', 'robot']
        
        # Input sanitization
        import re
        name = re.sub(r'[<"\'/]', '', name.strip())
        phone = re.sub(r'[^+0-9\s-]', '', phone.strip())
        
        if len(name) < 2:
            return jsonify({'error': 'Jméno musí mít alespoň 2 znaky'}), 400
            
        if any(forbidden in name.lower() for forbidden in forbidden_names):
            return jsonify({'error': 'Zadejte platné jméno a příjmení'}), 400
        
        email = data.get('email', '').strip()
        home_city = data.get('home_city', '').strip()
        paypal_email = data.get('paypal_email', '').strip()
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
        
        with db.session.begin():
            # Zkontroluje existující telefon
            existing_phone = db.session.execute(db.text('SELECT id FROM users WHERE phone = :phone'), {'phone': phone_full}).fetchone()
            if existing_phone:
                return jsonify({'error': 'Toto telefonní číslo je již registrováno'}), 409
            
            # Zkontroluje existující email pokud je zadán
            if email:
                existing_email = db.session.execute(db.text('SELECT id FROM users WHERE email = :email'), {'email': email}).fetchone()
                if existing_email:
                    return jsonify({'error': 'Tento email je již registrován'}), 409
            
            # Registruje uživatele
            db.session.execute(db.text('INSERT INTO users (name, phone, email, password_hash, rating, home_city, paypal_email) VALUES (:name, :phone_full, :email, :password_hash, :rating, :home_city, :paypal_email)'),
                             {'name': name, 'phone_full': phone_full, 'email': email if email else None, 'password_hash': password_hash, 'rating': 5.0, 'home_city': home_city if home_city else None, 'paypal_email': paypal_email if paypal_email else None})
            
            return jsonify({'message': 'Uživatel úspěšně registrován'}), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users/login', methods=['POST'])
@rate_limit(max_requests=10, window=300)  # Max 10 přihlášení za 5 minut
def login():
    try:
        data = request.get_json()
        login_field = data.get('phone')  # Může být telefon nebo email
        password = data.get('password')
        
        if not all([login_field, password]):
            return jsonify({'error': 'Telefon/email a heslo jsou povinné'}), 400
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with db.session.begin():
            # Zkusí přihlášení pomocí telefonu nebo emailu
            if '@' in login_field:
                # Přihlášení emailem
                user = db.session.execute(db.text('SELECT id, name, rating FROM users WHERE email = :login_field AND password_hash = :password_hash'),
                                         {'login_field': login_field, 'password_hash': password_hash}).fetchone()
            else:
                # Přihlášení telefonem - normalizuj formát
                phone_clean = ''.join(filter(str.isdigit, login_field))
                if phone_clean.startswith('420'):
                    phone_clean = phone_clean[3:]
                phone_full = f'+420{phone_clean}'
                
                user = db.session.execute(db.text('SELECT id, name, rating FROM users WHERE phone = :phone_full AND password_hash = :password_hash'),
                                         {'phone_full': phone_full, 'password_hash': password_hash}).fetchone()
        
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
        departure_time = datetime.datetime.strptime(data.get('departure_time'), "%Y-%m-%dT%H:%M")
        available_seats = data.get('available_seats')
        price_per_person = data.get('price_per_person')
        route_waypoints = json.dumps(data.get('route_waypoints', []))
        
        with db.session.begin():
            result = db.session.execute(db.text('''INSERT INTO rides 
                                                 (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints)
                                                 VALUES (:user_id, :from_location, :to_location, :departure_time, :available_seats, :price_per_person, :route_waypoints)'''),
                                     {'user_id': user_id, 'from_location': from_location, 'to_location': to_location, 'departure_time': departure_time, 'available_seats': available_seats, 'price_per_person': price_per_person, 'route_waypoints': route_waypoints})
            ride_id = result.lastrowid
        
        return jsonify({
            'message': 'Jízda úspěšně nabídnuta',
            'ride_id': ride_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/search', methods=['GET'])
def search_rides():
    try:
        # Získání parametrů z URL
        from_location = request.args.get('from', '').strip()
        to_location = request.args.get('to', '').strip()
        max_price = request.args.get('max_price', type=int)
        user_id = request.args.get('user_id', type=int)
        include_own = request.args.get('include_own', 'true').lower() == 'true'
        
        # GPS parametry
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
        search_range = request.args.get('range', type=int)
        
        # Datum a čas parametry
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        time_from = request.args.get('time_from', '').strip()
        time_to = request.args.get('time_to', '').strip()

        # Základní dotaz
        query = "SELECT r.*, u.name, u.rating FROM rides r LEFT JOIN users u ON r.user_id = u.id"
        conditions = []
        params = {}

        # Přidání podmínek podle parametrů
        if from_location:
            conditions.append("r.from_location LIKE :from_location")
            params['from_location'] = f'%{from_location}%'
        
        if to_location:
            conditions.append("r.to_location LIKE :to_location")
            params['to_location'] = f'%{to_location}%'

        if max_price is not None:
            conditions.append("r.price_per_person <= :max_price")
            params['max_price'] = max_price

        if not include_own and user_id is not None:
            conditions.append("r.user_id != :user_id")
            params['user_id'] = user_id
        
        # Filtrování podle data a času
        if date_from:
            conditions.append("DATE(r.departure_time) >= :date_from")
            params['date_from'] = date_from
        
        if date_to:
            conditions.append("DATE(r.departure_time) <= :date_to")
            params['date_to'] = date_to
        
        if time_from:
            conditions.append("TIME(r.departure_time) >= :time_from")
            params['time_from'] = time_from
        
        if time_to:
            conditions.append("TIME(r.departure_time) <= :time_to")
            params['time_to'] = time_to

        # Sestavení finálního dotazu
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        with db.session.begin():
            rides = db.session.execute(db.text(query), params).fetchall()

        # Města a jejich souřadnice pro výpočet vzdálenosti
        cities = {
            'Praha': [50.0755, 14.4378],
            'Brno': [49.1951, 16.6068],
            'Ostrava': [49.8209, 18.2625],
            'Plzeň': [49.7384, 13.3736],
            'Liberec': [50.7663, 15.0543],
            'Olomouc': [49.5938, 17.2509],
            'Zlín': [49.2265, 17.6679],
            'Rájec Jestřebí': [49.4186, 16.7486],
            'České Budějovice': [48.9745, 14.4743],
            'Hradec Králové': [50.2103, 15.8327]
        }

        def calculate_distance(lat1, lng1, lat2, lng2):
            import math
            R = 6371  # Poloměr Země v km
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2) * math.sin(dlng/2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c

        result = []
        current_user_id = request.args.get('user_id', type=int)

        for ride in rides:
            waypoints = json.loads(ride[7]) if ride[7] else []
            
            # Výpočet vzdálenosti od uživatele
            distance = 999  # Nastav na vysoké číslo jako výchozí
            if user_lat and user_lng and search_range:
                # Zkontroluj vzdálenost k OBOU městům (odkud i kam)
                from_coords = cities.get(ride[2].split(',')[0].strip())  # Pouze město, bez ulice
                to_coords = cities.get(ride[3].split(',')[0].strip())    # Pouze město, bez ulice
                
                # Vzdálenost pouze k výchozímu městu (odkud jede jízda)
                if from_coords:
                    distance = calculate_distance(user_lat, user_lng, from_coords[0], from_coords[1])
                else:
                    # Pokud nemáme souřadnice výchozího města, přeskoč jízdu
                    continue
                
                # Filtruj podle vzdálenosti - jízda musí být blízko ALESPOŇ jednoho z měst
                if distance > search_range:
                    continue
            
            # Zjištění, zda je jízda vlastní nebo rezervovaná
            is_own = False
            if current_user_id and ride[1] == current_user_id:
                is_own = True

            is_reserved = False

            result.append({
                'id': ride[0],
                'user_id': ride[1],
                'driver_name': ride[9],
                'driver_rating': ride[10] or 5.0,
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': ride[4].isoformat(),
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'route_waypoints': waypoints,
                'distance': round(distance, 1),
                'is_own': is_own,
                'is_reserved': is_reserved
            })
        
        # Seřadí podle vzdálenosti
        if user_lat and user_lng:
            result.sort(key=lambda x: x['distance'])
            
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/search', methods=['POST'])
def search_user():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Zadejte email nebo telefon'}), 400
        
        with db.session.begin():
            # Hledání pouze podle emailu (telefon skryt)
            if '@' in query:
                user = db.session.execute(db.text('SELECT id, name, phone, email, rating FROM users WHERE email LIKE :query'), {'query': f'%{query}%'}).fetchone()
            else:
                # Hledání podle jména
                user = db.session.execute(db.text('SELECT id, name, phone, email, rating FROM users WHERE name LIKE :query'), {'query': f'%{query}%'}).fetchone()
        
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
    import traceback
    try:
        with db.session.begin():
            rides = db.session.execute(db.text('''SELECT r.*, u.name, u.rating FROM rides r 
                                                 LEFT JOIN users u ON r.user_id = u.id
                                                 ORDER BY r.created_at DESC''')).fetchall()
        
        result = []
        for ride in rides:
            result.append({
                'id': ride[0],
                'user_id': ride[1],
                'driver_name': (ride[9] if len(ride) > 9 else None) or 'Neznámý řidič',
                'driver_rating': (ride[10] if len(ride) > 10 else None) or 5.0,
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': ride[4].isoformat(),
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'route_waypoints': json.loads(ride[7]) if ride[7] else [],
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

@app.route('/api/reservations/user/<int:user_id>')
def get_user_reservations_simple(user_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            SELECT res.id, res.seats_reserved, res.status, res.created_at,
                   r.from_location, r.to_location, r.departure_time, r.price_per_person,
                   u.name as driver_name, u.phone as driver_phone, r.id as ride_id
            FROM reservations res
            JOIN rides r ON res.ride_id = r.id
            JOIN users u ON r.user_id = u.id
            WHERE res.passenger_id = ? AND res.status = 'confirmed'
            ORDER BY r.departure_time ASC
        ''', (user_id,))
        
        reservations = c.fetchall()
        
        result = []
        for res in reservations:
            # Zkontroluj, zda je platba dokončena
            c.execute('SELECT status FROM payments WHERE ride_id = ? AND passenger_id = ? AND status = "completed"', (res[10], user_id))
            payment = c.fetchone()
            
            # Skryj pouze telefon pokud není zaplaceno
            driver_phone = res[9] if payment else "Skryto - zaplaťte nejdříve"
            
            result.append({
                'reservation_id': res[0],
                'seats_reserved': res[1],
                'status': res[2],
                'created_at': res[3],
                'from_location': res[4],
                'to_location': res[5],
                'departure_time': res[6].isoformat(),
                'price_per_person': res[7],
                'driver_name': res[8],
                'driver_phone': driver_phone,
                'is_paid': bool(payment)
            })
        
        conn.close()
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations/<int:reservation_id>')
def get_reservation_details(reservation_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            SELECT res.id, res.ride_id, res.passenger_id, res.seats_reserved, res.status,
                   r.from_location, r.to_location, r.departure_time, r.price_per_person
            FROM reservations res
            JOIN rides r ON res.ride_id = r.id
            WHERE res.id = ?
        ''', (reservation_id,))
        
        reservation = c.fetchone()
        conn.close()
        
        if not reservation:
            return jsonify({'error': 'Rezervace nenalezena'}), 404
        
        return jsonify({
            'id': reservation[0],
            'ride_id': reservation[1],
            'passenger_id': reservation[2],
            'seats_reserved': reservation[3],
            'status': reservation[4],
            'from_location': reservation[5],
            'to_location': reservation[6],
            'departure_time': reservation[7].isoformat(),
            'price_per_person': reservation[8]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations/driver/<int:driver_id>')
def get_driver_reservations(driver_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            SELECT res.id, res.seats_reserved, res.status, res.created_at,
                   r.from_location, r.to_location, r.departure_time, r.id as ride_id,
                   u.name as passenger_name, u.id as passenger_id
            FROM reservations res
            JOIN rides r ON res.ride_id = r.id
            JOIN users u ON res.passenger_id = u.id
            WHERE r.user_id = ? AND res.status = 'confirmed'
            ORDER BY r.departure_time DESC
        ''', (driver_id,))
        
        reservations = c.fetchall()
        conn.close()
        
        result = []
        for res in reservations:
            result.append({
                'reservation_id': res[0],
                'seats_reserved': res[1],
                'status': res[2],
                'created_at': res[3],
                'from_location': res[4],
                'to_location': res[5],
                'departure_time': res[6].isoformat(),
                'ride_id': res[7],
                'passenger_name': res[8],
                'passenger_id': res[9]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/cancel/<int:ride_id>', methods=['DELETE'])
def cancel_ride(ride_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Zruš všechny rezervace pro tuto jízdu
        c.execute('UPDATE reservations SET status = "cancelled" WHERE ride_id = ?', (ride_id,))
        
        # Smaž jízdu
        c.execute('DELETE FROM rides WHERE id = ?', (ride_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Jízda zrušena'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations/cancel/<int:reservation_id>', methods=['DELETE'])
def cancel_reservation_new(reservation_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        c.execute('SELECT ride_id, seats_reserved FROM reservations WHERE id = ?', (reservation_id,))
        reservation = c.fetchone()
        
        if not reservation:
            conn.close()
            return jsonify({'error': 'Rezervace nenalezena'}), 404
        
        ride_id, seats_reserved = reservation
        
        c.execute('UPDATE reservations SET status = "cancelled" WHERE id = ?', (reservation_id,))
        c.execute('UPDATE rides SET available_seats = available_seats + ? WHERE id = ?', (seats_reserved, ride_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Rezervace zrušena'}), 200
        
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
@app.route('/api/users/<user_name>/reviews', methods=['GET'])
def get_user_reviews(user_name):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Najdi user_id podle jména
        c.execute('SELECT id FROM users WHERE name = ?', (user_name,))
        user = c.fetchone()
        
        if not user:
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        user_id = user[0]
        
        # Získej hodnocení
        c.execute('''
            SELECT r.rating, r.comment, r.created_at, u.name as rater_name
            FROM ratings r
            JOIN users u ON r.rater_id = u.id
            WHERE r.rated_id = ? AND r.comment IS NOT NULL AND r.comment != ''
            ORDER BY r.created_at DESC
            LIMIT 10
        ''', (user_id,))
        
        reviews = c.fetchall()
        conn.close()
        
        result = []
        for review in reviews:
            result.append({
                'rating': review[0],
                'comment': review[1],
                'created_at': review[2],
                'rater_name': review[3]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ratings/create', methods=['POST'])
def create_rating():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        rater_id = data.get('rater_id')
        
        if not rater_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        
        rating = data.get('rating')
        comment = data.get('comment', '')
        driver_name = data.get('driver_name')
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Najdi rated_id podle jména
        rated_id = None
        if driver_name:
            c.execute('SELECT id FROM users WHERE name = ?', (driver_name,))
            user = c.fetchone()
            if user:
                rated_id = user[0]
        
        if not rated_id:
            rated_id = data.get('rated_id', 0)
        
        c.execute('INSERT INTO ratings (ride_id, rater_id, rated_id, rating, comment) VALUES (?, ?, ?, ?, ?)',
                 (ride_id, rater_id, rated_id, rating, comment))
        
        # Aktualizace průměrného hodnocení
        if rated_id:
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
        departure_time = datetime.datetime.strptime(data.get('departure_time'), "%Y-%m-%dT%H:%M")
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

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# API pro platby (mock implementace)
@app.route('/api/payments/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        user_id = data.get('user_id')
        amount = data.get('amount')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        
        # Získej detaily jízdy
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT from_location, to_location, user_id FROM rides WHERE id = ?', (ride_id,))
        ride = c.fetchone()
        
        if not ride:
            conn.close()
            return jsonify({'error': 'Jízda nenalezena'}), 404
        
        # Kontrola a výpočet provize
        if amount is None:
            return jsonify({'error': 'Částka není zadána'}), 400
        
        try:
            amount = int(amount)
        except (ValueError, TypeError):
            return jsonify({'error': 'Neplatná částka'}), 400
        
        commission = int(amount * COMMISSION_RATE)
        driver_amount = amount - commission
        
        # Mock platební session (bez Stripe)
        mock_session_id = f'mock_session_{ride_id}_{user_id}'
        
        # Ulož platbu do databáze
        c.execute('''INSERT INTO payments (ride_id, passenger_id, driver_id, amount, commission, driver_amount, stripe_payment_id, status)
                     VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')''',
                 (ride_id, user_id, ride[2], amount, commission, driver_amount, mock_session_id))
        conn.commit()
        conn.close()
        
        # QR platební brána s nízkými poplatky
        qr_payment_url = f'{request.host_url}qr-payment?ride_id={ride_id}&amount={commission}&commission={commission}&driver_amount={driver_amount}'
        
        return jsonify({'checkout_url': qr_payment_url}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/qr-payment')
def qr_payment():
    ride_id = request.args.get('ride_id')
    amount = request.args.get('amount', '0')
    commission = request.args.get('commission', '0')
    driver_amount = request.args.get('driver_amount', '0')
    
    # QR kód pro bankovní platbu
    qr_data = f'SPD*1.0*ACC:CZ2501000001235652280207*AM:{commission}*CC:CZK*MSG:Sveztese.cz #{ride_id}*X-VS:{ride_id}'
    
    return f'''
    <html>
    <head>
        <title>QR Platba - Jízda #{ride_id}</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 500px; margin: 50px auto; padding: 20px; text-align: center; }}
            .qr-code {{ margin: 20px 0; }}
            .amount {{ font-size: 24px; font-weight: bold; color: #007bff; margin: 20px 0; }}
            .btn {{ background: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 10px; text-decoration: none; display: inline-block; }}
            .btn-cancel {{ background: #dc3545; }}
        </style>
    </head>
    <body>
        <h1>📱 QR Platba</h1>
        
        <div class="amount">
            K úhradě: {commission} Kč
        </div>
        
        <div class="qr-code">
            <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_data}" alt="QR kód pro platbu">
        </div>
        
        <p><strong>Instrukce:</strong></p>
        <ol style="text-align: left;">
            <li>Otevřete bankovní aplikaci</li>
            <li>Naskenujte QR kód</li>
            <li>Potvrdte platbu</li>
            <li>Klikněte "Platba provedena"</li>
        </ol>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p><strong>Účet:</strong> 123-5652280207/0100</p>
            <p><strong>Variabilní symbol:</strong> {ride_id}</p>
            <p><strong>Částka:</strong> {commission} Kč</p>
        </div>
        
        <a href="/payment-success?ride_id={ride_id}&amount={amount}&commission={commission}" class="btn">✓ Platba provedena</a>
        <a href="/payment-cancel" class="btn btn-cancel">❌ Zrušit</a>
    </body>
    </html>
    '''

@app.route('/payment-gateway')
def payment_gateway():
    ride_id = request.args.get('ride_id')
    amount = request.args.get('amount', '0')
    commission = request.args.get('commission', '0')
    driver_amount = request.args.get('driver_amount', '0')
    
    return f'''
    <html>
    <head>
        <title>Platba za jízdu #{ride_id}</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .bank-info {{ background: #e3f2fd; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .amount {{ font-size: 24px; font-weight: bold; color: #007bff; text-align: center; margin: 20px 0; }}
            .btn {{ background: #28a745; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 10px 5px; text-decoration: none; display: inline-block; }}
            .btn-cancel {{ background: #dc3545; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>💳 Platba za jízdu #{ride_id}</h1>
            
            <div class="amount">
                K úhradě: {amount} Kč
            </div>
            
            <div class="bank-info">
                <h3>🏦 Bankovní údaje pro platbu:</h3>
                <p><strong>Číslo účtu:</strong> 123-5652280207/0100</p>
                <p><strong>IBAN:</strong> CZ25 0100 0001 2356 5228 0207</p>
                <p><strong>SWIFT:</strong> KOMBCZPPXXX</p>
                <p><strong>Variabilní symbol:</strong> {ride_id}</p>
                <p><strong>Účel platby:</strong> Spolujízda #{ride_id}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h4>Detail platby:</h4>
                <p>Cena jízdy: {amount} Kč</p>
                <p>Poplatek Sveztese.cz: {commission} Kč (10%)</p>
                <p>Řidiči: {driver_amount} Kč</p>
            </div>
            
            <p><strong>Instrukce:</strong></p>
            <ol>
                <li>Proveďte bankovní převod na výše uvedený účet</li>
                <li>Jako variabilní symbol uveďte: <strong>{ride_id}</strong></li>
                <li>Po provedení platby klikněte na "Platba provedena"</li>
                <li>Kontaktní údaje řidiče získáte po ověření platby</li>
            </ol>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/payment-success?ride_id={ride_id}&amount={amount}&commission={commission}" class="btn">✓ Platba provedena</a>
                <a href="/payment-cancel" class="btn btn-cancel">❌ Zrušit platbu</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/payment-success')
def payment_success():
    ride_id = request.args.get('ride_id')
    amount = request.args.get('amount', '0')
    commission = request.args.get('commission', '0')
    driver_amount = int(amount) - int(commission) if amount and commission else 0
    
    return f'''
    <html>
    <head><title>Platba úspěšná</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🎉 Platba úspěšná!</h1>
        <p>Vaše místo v jízdě #{ride_id} bylo rezervováno.</p>
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; max-width: 400px; margin-left: auto; margin-right: auto;">
            <h3>Detail platby:</h3>
            <p><strong>Poplatek Sveztese.cz:</strong> {commission} Kč (zaplaceno online)</p>
            <p><strong>Řidiči v hotovosti:</strong> {driver_amount} Kč</p>
            <p><strong>Celková cena jízdy:</strong> {amount} Kč</p>
        </div>
        <p><strong>Důležité:</strong> Zbytek ({driver_amount} Kč) zaplaťte řidiči v hotovosti při jízdě.</p>
        <p>Brzy vás bude kontaktovat řidič.</p>
        <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Zpět do aplikace</a>
    </body>
    </html>
    '''

@app.route('/payment-cancel')
def payment_cancel():
    return f'''
    <html>
    <head><title>Platba zrušena</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>❌ Platba zrušena</h1>
        <p>Platba byla zrušena. Můžete to zkusit znovu.</p>
        <a href="/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Zpět do aplikace</a>
    </body>
    </html>
    '''

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')



@app.route('/sitemap.xml', methods=['GET'])
def sitemap_xml():
    sitemap = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://www.sveztese.cz/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://www.sveztese.cz/search</loc>
    <changefreq>hourly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://www.sveztese.cz/terms</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
  <url>
    <loc>https://www.sveztese.cz/privacy</loc>
    <changefreq>monthly</changefreq>
    <priority>0.3</priority>
  </url>
</urlset>'''
    
    return Response(sitemap, mimetype='application/xml', headers={
        'Cache-Control': 'public, max-age=86400',
        'Access-Control-Allow-Origin': '*'
    })

@app.route('/api/notifications/send', methods=['POST'])
def send_notification():
    try:
        data = request.get_json()
        recipient = data.get('recipient')
        title = data.get('title')
        body = data.get('body')
        
        print(f"📱 Notifikace pro {recipient}: {title} - {body}")
        
        return jsonify({'message': 'Notifikace odeslána'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/location', methods=['POST'])
def update_user_location():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        lat = data.get('lat')
        lng = data.get('lng')
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Vytvoř tabulku pro polohy pokud neexistuje
        c.execute('''CREATE TABLE IF NOT EXISTS user_locations
                     (user_id INTEGER PRIMARY KEY,
                      lat REAL NOT NULL,
                      lng REAL NOT NULL,
                      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                      FOREIGN KEY (user_id) REFERENCES users (id))''')
        
        # Aktualizuj nebo vlož polohu
        c.execute('''INSERT OR REPLACE INTO user_locations (user_id, lat, lng, updated_at)
                     VALUES (?, ?, ?, CURRENT_TIMESTAMP)''', (user_id, lat, lng))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Poloha aktualizována'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro seznam uživatelů
@app.route('/api/users/all', methods=['GET'])
def get_all_users():
    try:
        # Ověř, že uživatel má alespoň jednu dokončenou platbu
        user_id = request.args.get('user_id', type=int)
        if user_id:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM payments WHERE passenger_id = ? AND status = "completed"', (user_id,))
            payment_count = c.fetchone()[0]
            if payment_count == 0:
                conn.close()
                return jsonify({'error': 'Přístup pouze pro zaplacené uživatele'}), 403
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            SELECT u.id, u.name, u.phone, u.rating, u.total_rides, u.verified, u.created_at, u.home_city,
                   COUNT(DISTINCT rh1.id) as rides_as_driver,
                   COUNT(DISTINCT rh2.id) as rides_as_passenger
            FROM users u
            LEFT JOIN ride_history rh1 ON u.id = rh1.driver_id
            LEFT JOIN ride_history rh2 ON u.id = rh2.passenger_id
            GROUP BY u.id
            ORDER BY u.rating DESC, u.total_rides DESC
        ''')
        
        users = c.fetchall()
        conn.close()
        
        result = []
        for user in users:
            result.append({
                'id': user[0],
                'name': user[1],
                'phone': '***-***-***',  # Skryj celý telefon
                'rating': user[3] or 5.0,
                'total_rides': user[4] or 0,
                'verified': user[5] or False,
                'last_active': user[6],  # created_at jako last_active
                'home_city': user[7] or 'Neznámé',
                'rides_as_driver': user[8] or 0,
                'rides_as_passenger': user[9] or 0
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Základní info o uživateli
        c.execute('''
            SELECT u.id, u.name, u.rating, u.total_rides, u.verified, u.created_at, u.bio,
                   COUNT(DISTINCT rh1.id) as rides_as_driver,
                   COUNT(DISTINCT rh2.id) as rides_as_passenger
            FROM users u
            LEFT JOIN ride_history rh1 ON u.id = rh1.driver_id
            LEFT JOIN ride_history rh2 ON u.id = rh2.passenger_id
            WHERE u.id = ?
            GROUP BY u.id
        ''', (user_id,))
        
        user = c.fetchone()
        if not user:
            conn.close()
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        # Posledních 5 recenzí
        c.execute('''
            SELECT r.rating, r.comment, r.created_at, u.name as reviewer_name
            FROM ratings r
            JOIN users u ON r.rater_id = u.id
            WHERE r.rated_id = ? AND r.comment IS NOT NULL AND r.comment != ''
            ORDER BY r.created_at DESC
            LIMIT 5
        ''', (user_id,))
        
        reviews = c.fetchall()
        
        # Historie jízd (posledních 10)
        c.execute('''
            SELECT rh.from_location, rh.to_location, rh.departure_time, rh.status,
                   CASE WHEN rh.driver_id = ? THEN 'driver' ELSE 'passenger' END as role
            FROM ride_history rh
            WHERE rh.driver_id = ? OR rh.passenger_id = ?
            ORDER BY rh.completed_at DESC
            LIMIT 10
        ''', (user_id, user_id, user_id))
        
        history = c.fetchall()
        conn.close()
        
        result = {
            'id': user[0],
            'name': user[1],
            'rating': user[2] or 5.0,
            'total_rides': user[3] or 0,
            'verified': user[4] or False,
            'member_since': user[5],
            'bio': user[6] or '',
            'rides_as_driver': user[7] or 0,
            'rides_as_passenger': user[8] or 0,
            'reviews': [{
                'rating': review[0],
                'comment': review[1],
                'date': review[2],
                'reviewer': review[3]
            } for review in reviews],
            'recent_rides': [{
                'from': ride[0],
                'to': ride[1],
                'date': ride[2].isoformat(),
                'status': ride[3],
                'role': ride[4]
            } for ride in history]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/locations', methods=['GET'])
def get_user_locations():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Získej polohy uživatelů (pouze posledních 5 minut)
        c.execute('''
            SELECT ul.user_id, ul.lat, ul.lng, ul.updated_at, u.name
            FROM user_locations ul
            JOIN users u ON ul.user_id = u.id
            WHERE ul.updated_at > datetime('now', '-5 minutes')
        ''')
        
        locations = c.fetchall()
        conn.close()
        
        result = []
        for loc in locations:
            result.append({
                'user_id': loc[0],
                'lat': loc[1],
                'lng': loc[2],
                'updated_at': loc[3],
                'user_name': loc[4]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro oblíbené uživatele
@app.route('/api/users/favorites', methods=['POST'])
def add_favorite_user():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        favorite_user_id = data.get('favorite_user_id')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Zkontroluj, zda už není v oblíbených
        c.execute('SELECT id FROM favorite_users WHERE user_id = ? AND favorite_user_id = ?', 
                 (user_id, favorite_user_id))
        if c.fetchone():
            conn.close()
            return jsonify({'error': 'Uživatel je již v oblíbených'}), 400
        
        c.execute('INSERT INTO favorite_users (user_id, favorite_user_id) VALUES (?, ?)',
                 (user_id, favorite_user_id))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Uživatel přidán do oblíbených'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/favorites', methods=['GET'])
def get_favorite_users(user_id):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('''
            SELECT u.id, u.name, u.rating, u.total_rides, u.verified
            FROM favorite_users f
            JOIN users u ON f.favorite_user_id = u.id
            WHERE f.user_id = ?
            ORDER BY u.rating DESC
        ''', (user_id,))
        
        favorites = c.fetchall()
        conn.close()
        
        result = []
        for fav in favorites:
            result.append({
                'id': fav[0],
                'name': fav[1],
                'rating': fav[2] or 5.0,
                'total_rides': fav[3] or 0,
                'verified': fav[4] or False
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro vyhledávání uživatelů
@app.route('/api/users/search', methods=['GET'])
def search_users():
    try:
        # Ověř, že uživatel má alespoň jednu dokončenou platbu
        user_id = request.args.get('user_id', type=int)
        if user_id:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute('SELECT COUNT(*) FROM payments WHERE passenger_id = ? AND status = "completed"', (user_id,))
            payment_count = c.fetchone()[0]
            if payment_count == 0:
                conn.close()
                return jsonify({'error': 'Přístup pouze pro zaplacené uživatele'}), 403
            conn.close()
        
        query = request.args.get('q', '').strip()
        min_rating = request.args.get('min_rating', type=float)
        verified_only = request.args.get('verified', 'false').lower() == 'true'
        city_filter = request.args.get('city', '').strip()
        
        if not query and not city_filter:
            return jsonify({'error': 'Zadejte jméno nebo vyberte město'}), 400
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        sql = '''
            SELECT u.id, u.name, u.rating, u.total_rides, u.verified, u.created_at, u.home_city
            FROM users u
            WHERE 1=1
        '''
        params = []
        
        if query:
            sql += ' AND u.name LIKE ?'
            params.append(f'%{query}%')
        
        if min_rating:
            sql += ' AND u.rating >= ?'
            params.append(min_rating)
        
        if verified_only:
            sql += ' AND u.verified = 1'
        
        if city_filter:
            sql += ' AND u.home_city = ?'
            params.append(city_filter)
        
        # Debug výpisy
        print(f"DEBUG: query='{query}', city_filter='{city_filter}'")
        print(f"DEBUG: SQL={sql}")
        print(f"DEBUG: params={params}")
        
        sql += ' ORDER BY u.rating DESC, u.total_rides DESC LIMIT 20'
        
        c.execute(sql, params)
        users = c.fetchall()
        print(f"DEBUG: Nalezeno {len(users)} uživatelů")
        for user in users:
            print(f"DEBUG: - {user[1]}: {user[6]}")
        conn.close()
        
        result = []
        for user in users:
            result.append({
                'id': user[0],
                'name': user[1],
                'rating': user[2] or 5.0,
                'total_rides': user[3] or 0,
                'verified': user[4] or False,
                'last_active': user[5],
                'home_city': user[6] or 'Neznámé'
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro přidání jízdy do historie
@app.route('/api/rides/<int:ride_id>/complete', methods=['POST'])
def complete_ride(ride_id):
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Získej detaily jízdy
        c.execute('''
            SELECT r.id, r.user_id, r.from_location, r.to_location, r.departure_time, r.price_per_person
            FROM rides r WHERE r.id = ?
        ''', (ride_id,))
        
        ride = c.fetchone()
        if not ride:
            conn.close()
            return jsonify({'error': 'Jízda nenalezena'}), 404
        
        # Získej všechny pasažéry
        c.execute('''
            SELECT res.passenger_id FROM reservations res
            WHERE res.ride_id = ? AND res.status = 'confirmed'
        ''', (ride_id,))
        
        passengers = c.fetchall()
        
        # Přidej do historie pro řidiče
        c.execute('''
            INSERT INTO ride_history (ride_id, driver_id, from_location, to_location, departure_time, price_per_person)
            VALUES (?, ?, ?, ?, ?, ?) 
        ''', (ride[0], ride[1], ride[2], ride[3], ride[4].isoformat(), ride[5]))
        
        # Přidej do historie pro každého pasažéra
        for passenger in passengers:
            c.execute('''
                INSERT INTO ride_history (ride_id, driver_id, passenger_id, from_location, to_location, departure_time, price_per_person)
                VALUES (?, ?, ?, ?, ?, ?, ?) 
            ''', (ride[0], ride[1], passenger[0], ride[2], ride[3], ride[4].isoformat(), ride[5]))
        
        # Aktualizuj počet jízd uživatelů
        c.execute('UPDATE users SET total_rides = total_rides + 1 WHERE id = ?', (ride[1],))
        for passenger in passengers:
            c.execute('UPDATE users SET total_rides = total_rides + 1 WHERE id = ?', (passenger[0],))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Jízda označena jako dokončená'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro města
@app.route('/api/cities', methods=['GET'])
def get_cities():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT name, region, population FROM cities ORDER BY population DESC, name ASC')
        cities = c.fetchall()
        conn.close()
        
        result = []
        for city in cities:
            result.append({
                'name': city[0],
                'region': city[1],
                'population': city[2]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro smazání uživatele
@app.route('/api/users/delete/<user_name>', methods=['DELETE'])
def delete_user_by_name(user_name):
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Najdi uživatele podle jména
        c.execute('SELECT id FROM users WHERE name = ?', (user_name,))
        user = c.fetchone()
        
        if not user:
            conn.close()
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        user_id = user[0]
        
        # Smaž všechna související data
        c.execute('DELETE FROM reservations WHERE passenger_id = ?', (user_id,))
        c.execute('DELETE FROM rides WHERE user_id = ?', (user_id,))
        c.execute('DELETE FROM messages WHERE sender_id = ?', (user_id,))
        c.execute('DELETE FROM ratings WHERE rater_id = ? OR rated_id = ?', (user_id, user_id))
        c.execute('DELETE FROM blocked_users WHERE blocker_id = ? OR blocked_id = ?', (user_id, user_id))
        c.execute('DELETE FROM favorite_users WHERE user_id = ? OR favorite_user_id = ?', (user_id, user_id))
        c.execute('DELETE FROM ride_history WHERE driver_id = ? OR passenger_id = ?', (user_id, user_id))
        c.execute('DELETE FROM user_stats WHERE user_id = ?', (user_id,))
        
        # Smaž uživatele
        c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Uživatel {user_name} byl smazán'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Debug endpoint pro kontrolu uživatelů
@app.route('/api/debug/users', methods=['GET'])
def debug_users():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute('SELECT name, home_city, phone FROM users ORDER BY name')
        users = c.fetchall()
        conn.close()
        
        result = []
        for user in users:
            result.append({
                'name': user[0],
                'home_city': user[1],
                'phone': user[2]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro aktualizaci města uživatele
@app.route('/api/users/update-city', methods=['POST'])
def update_user_city():
    try:
        data = request.get_json()
        user_name = data.get('name')
        home_city = data.get('home_city')
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Aktualizuj město uživatele
        c.execute('UPDATE users SET home_city = ? WHERE name = ?', (home_city, user_name))
        
        if c.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': f'Město {home_city} přidáno uživateli {user_name}'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Webhook pro Stripe platby
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_test')
        )
    except ValueError:
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        return 'Invalid signature', 400
    
    # Zpracuj úspěšnou platbu
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Získej metadata
        ride_id = session['metadata']['ride_id']
        user_id = session['metadata']['user_id']
        amount = int(session['metadata']['amount'])
        commission = int(session['metadata']['commission'])
        driver_amount = amount - commission
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Aktualizuj status platby
        c.execute('UPDATE payments SET status = "completed" WHERE stripe_payment_id = ?', (session['id'],))
        
        # Získej řidiče
        c.execute('SELECT user_id FROM rides WHERE id = ?', (ride_id,))
        driver = c.fetchone()
        
        if driver:
            driver_id = driver[0]
            
            # Ulož platbu do databáze
            c.execute('''INSERT INTO payments (ride_id, passenger_id, driver_id, amount, commission, driver_amount, stripe_payment_id, status)
                         VALUES (?, ?, ?, ?, ?, ?, ?, "completed")''',
                     (ride_id, user_id, driver_id, amount, commission, driver_amount, session['id']))
            
            # TODO: Zde byš měl poslat peníze řidiči
            # Např. přes Stripe Connect nebo bankovní převod
            print(f"PLATBA: {driver_amount} Kč pro řidiče {driver_id}, provize {commission} Kč")
        
        conn.commit()
        conn.close()
    
    return 'Success', 200

# API pro přidání bankovního účtu řidiče
@app.route('/api/driver/bank-account', methods=['POST'])
def add_driver_bank_account():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        bank_account = data.get('bank_account')
        iban = data.get('iban')
        account_holder = data.get('account_holder')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Ulož nebo aktualizuj bankovní účet
        c.execute('''INSERT OR REPLACE INTO driver_accounts (user_id, bank_account, iban, account_holder)
                     VALUES (?, ?, ?, ?)''',
                 (user_id, bank_account, iban, account_holder))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Bankovní účet uložen'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API pro vyčištění databáze
@app.route('/api/admin/cleanup', methods=['POST'])
def cleanup_database():
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Smaž uživatele bez domovského města
        c.execute('DELETE FROM users WHERE home_city IS NULL OR home_city = ""')
        deleted_users = c.rowcount
        
        # Smaž jízdy s neplatnou cenou (NULL, 0 nebo záporná)
        c.execute('DELETE FROM rides WHERE price_per_person IS NULL OR price_per_person <= 0')
        deleted_rides = c.rowcount
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Databáze vyčištěna',
            'deleted_users': deleted_users,
            'deleted_rides': deleted_rides
        }), 200
        
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
        
        # Pokročilé vyhledávání je již implementováno
        print("API endpointy připraveny")
        
        # Import bezpečnostních hlaviček
        from security_headers import add_security_headers
        from flask import Flask, redirect, request

        app = Flask(__name__)


        
        
        @app.before_request
        def redirect_root_to_www():
            if request.host == "sveztese.cz":
                return redirect("https://www.sveztese.cz" + request.full_path, code=301)
        
        @app.before_request
        def force_https():
            if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
                if 'herokuapp.com' in request.host:
                    return redirect(request.url.replace('http://', 'https://'))
        
        @app.after_request
        def after_request(response):
            return add_security_headers(response)
        
        print("Server se spouští na:")
        print("  Lokální: http://localhost:8080")
        print("  Veřejná: http://0.0.0.0:8080")
        print("  Stiskni Ctrl+C pro ukonceni")
        
        # Získá IP adresu
        import socket
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            print(f"  Síťová: http://{local_ip}:8080")
        except:
            pass
        
        port = int(os.environ.get('PORT', 5000))
        print(f"Starting server on port {port}")
        # Pro Heroku použij gunicorn, pro lokální vývoj Flask
        if os.environ.get('DYNO'):
            # Heroku prostředí
            app.run(debug=False, host='0.0.0.0', port=port)
        else:
            # Lokální vývoj
            app.run(debug=True, host='0.0.0.0', port=port)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        print(f"Chyba při spuštění serveru: {e}")
        import traceback
        traceback.print_exc()
        input("Stiskněte Enter pro ukončení...")