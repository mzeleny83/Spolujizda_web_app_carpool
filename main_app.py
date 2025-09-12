from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, Response
from flask_cors import CORS
# from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import hashlib
import datetime
import os
import json
import signal
import sys
import requests
import stripe
import traceback

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

def parse_datetime_str(dt_str):
    if not dt_str:
        return None
    if isinstance(dt_str, datetime.datetime):
        return dt_str
    try:
        return datetime.datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, TypeError):
        try:
            return datetime.datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            return None

@app.route('/robots.txt')
def robots():
    content = """User-agent: *
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

Sitemap: https://www.sveztese.cz/sitemap.xml"""
    return Response(content, mimetype='text/plain')

from collections import defaultdict
from time import time
request_counts = defaultdict(list)

def rate_limit(max_requests=10, window=60):
    def decorator(f):
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            now = time()
            request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] if now - req_time < window]
            if len(request_counts[client_ip]) >= max_requests:
                return jsonify({'error': 'Příliš mnoho požadavků'}), 429
            request_counts[client_ip].append(now)
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
app.debug = True
app.config['TEMPLATES_AUTO_RELOAD'] = True
CORS(app, resources={'/*': {'origins': '*', 'methods': ['GET', 'POST', 'OPTIONS'], 'allow_headers': ['Content-Type']}})
# socketio = SocketIO(app, cors_allowed_origins='*')

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_51QYOhzP8xJKqGzKvYourSecretKey')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_51QYOhzP8xJKqGzKvYourPublishableKey')
COMMISSION_RATE = 0.10
YOUR_STRIPE_ACCOUNT_ID = 'acct_YourConnectedAccountId'

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

@app.route('/chat')
def chat_page():
    return render_template('chat.html')

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

@app.route('/api/cities', methods=['GET'])
def get_cities():
    return jsonify([])

@app.route('/api/rides/driver/<int:user_id>')
def get_driver_rides(user_id):
    try:
        with db.session.begin():
            rides = db.session.execute(db.text("""
                SELECT r.id, r.user_id, r.from_location, r.to_location, r.departure_time, 
                       r.available_seats, r.price_per_person, r.route_waypoints, r.created_at,
                       u.name, u.rating
                FROM rides r
                LEFT JOIN users u ON r.user_id = u.id
                WHERE r.user_id = :user_id
                ORDER BY r.departure_time ASC
            """), {'user_id': user_id}).fetchall()
        
        result = []
        for ride in rides:
            departure_time_val = parse_datetime_str(ride[4])
            result.append({
                'id': ride[0],
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': departure_time_val.isoformat() if departure_time_val else None,
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'driver_name': ride[9] or 'Neznámý řidič',
                'driver_rating': float(ride[10]) if ride[10] is not None else 5.0,
                'reservations_count': 0
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/<int:ride_id>/reservations')
def get_ride_reservations(ride_id):
    try:
        with db.session.begin():
            reservations = db.session.execute(db.text("""
                SELECT res.seats_reserved, u.name, u.phone
                FROM reservations res
                JOIN users u ON res.passenger_id = u.id
                WHERE res.ride_id = :ride_id AND res.status != 'cancelled'
            """), {'ride_id': ride_id}).fetchall()
        
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
            messages = db.session.execute(db.text("""
                SELECT m.message, m.created_at, m.sender_id, u.name as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.ride_id = :ride_id
                ORDER BY m.created_at ASC
            """), {'ride_id': ride_id}).fetchall()
        
        result = []
        for msg in messages:
            created_at_val = parse_datetime_str(msg[1])
            result.append({
                'message': msg[0],
                'created_at': created_at_val.isoformat() if created_at_val else None,
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
            reservations = db.session.execute(db.text("""
                SELECT res.id, res.seats_reserved, res.status, res.created_at,
                       r.from_location, r.to_location, r.departure_time, r.price_per_person,
                       u.name as driver_name, u.phone as driver_phone
                FROM reservations res
                JOIN rides r ON res.ride_id = r.id
                JOIN users u ON r.user_id = u.id
                WHERE res.passenger_id = :user_id AND res.status != 'cancelled'
                ORDER BY r.departure_time ASC
            """), {'user_id': user_id}).fetchall()
        
        result = []
        for res in reservations:
            created_at_val = parse_datetime_str(res[3])
            departure_time_val = parse_datetime_str(res[6])
            result.append({
                'reservation_id': res[0],
                'seats_reserved': res[1],
                'status': res[2],
                'created_at': created_at_val.isoformat() if created_at_val else None,
                'from_location': res[4],
                'to_location': res[5],
                'departure_time': departure_time_val.isoformat() if departure_time_val else None,
                'price_per_person': res[7],
                'driver_name': res[8],
                'driver_phone': res[9]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/all', methods=['GET'])
def get_all_users_redirect():
    return redirect('/api/users/list', code=302)

@app.route('/api/users/list', methods=['GET'])
def list_users():
    try:
        with db.session.begin():
            users = db.session.execute(db.text('SELECT id, name, phone, password_hash, created_at, rating FROM users ORDER BY created_at DESC')).fetchall()
        
        result = []
        for user in users:
            created_at_val = parse_datetime_str(user[4])
            result.append({
                'id': user[0],
                'name': user[1],
                'phone': user[2],
                'password_hash': user[3],
                'created_at': created_at_val.isoformat() if created_at_val else None,
                'driver_rating': float(user[5]) if user[5] is not None else 5.0
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test/password/<password>', methods=['GET'])
def test_password_hash(password):
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
        
        if not password_hash:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'password_hash': password_hash[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        phone = data.get('phone')
        password = data.get('password')
        
        forbidden_names = ['neznámý řidič', 'neznámý', 'unknown', 'driver', 'řidič', 'neznámy ridic', 'test', 'user', 'anonym', 'guest', 'admin', 'null', 'undefined', 'testovací', 'robot']
        
        import re
        name = re.sub(r'[<"\'/]', '', name.strip())
        phone = re.sub(r'[^+\d\s-]', '', phone.strip())
        
        if len(name) < 2:
            return jsonify({'error': 'Jméno musí mít alespoň 2 znaky'}), 400
            
        if any(forbidden in name.lower() for forbidden in forbidden_names):
            return jsonify({'error': 'Zadejte platné jméno a příjmení'}), 400
        
        email = data.get('email', '').strip()
        password_confirm = data.get('password_confirm')
        
        if not all([name, phone, password, password_confirm]):
            return jsonify({'error': 'Jméno, telefon, heslo a potvrzení hesla jsou povinné'}), 400
        
        if password != password_confirm:
            return jsonify({'error': 'Hesla se neshodují'}), 400
        
        phone_clean = ''.join(filter(str.isdigit, phone))
        
        if phone_clean.startswith('420'):
            phone_clean = phone_clean[3:]
        
        if len(phone_clean) != 9:
            return jsonify({'error': 'Neplatný formát telefonu (9 číslic)'}), 400
        
        phone_full = f'+420{phone_clean}'
        
        if email and '@' not in email:
            return jsonify({'error': 'Neplatný formát emailu'}), 400
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with db.session.begin():
            existing_phone = db.session.execute(db.text('SELECT id FROM users WHERE phone = :phone'), {'phone': phone_full}).fetchone()
            if existing_phone:
                return jsonify({'error': 'Toto telefonní číslo je již registrováno'}), 409
            
            if email:
                existing_email = db.session.execute(db.text('SELECT id FROM users WHERE email = :email'), {'email': email}).fetchone()
                if existing_email:
                    return jsonify({'error': 'Tento email je již registrován'}), 409
            
            db.session.execute(db.text('INSERT INTO users (name, phone, email, password_hash, rating) VALUES (:name, :phone, :email, :password_hash, :rating)'),
                             {'name': name, 'phone': phone_full, 'email': email if email else None, 'password_hash': password_hash, 'rating': 5.0})
            
            return jsonify({'message': 'Uživatel úspěšně registrován'}), 201
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        login_field = data.get('phone')
        password = data.get('password')
        
        if not all([login_field, password]):
            return jsonify({'error': 'Telefon/email a heslo jsou povinné'}), 400
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with db.session.begin():
            if '@' in login_field:
                user = db.session.execute(db.text('SELECT id, name, rating FROM users WHERE email = :login_field AND password_hash = :password_hash'),
                                         {'login_field': login_field, 'password_hash': password_hash}).fetchone()
            else:
                phone_clean = ''.join(filter(str.isdigit, login_field))
                if phone_clean.startswith('420'):
                    phone_clean = phone_clean[3:]
                phone_full = f'+420{phone_clean}'
                
                user = db.session.execute(db.text('SELECT id, name, rating FROM users WHERE phone = :phone AND password_hash = :password_hash'),
                                         {'phone': phone_full, 'password_hash': password_hash}).fetchone()
        
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
            result = db.session.execute(db.text('INSERT INTO rides (user_id, from_location, to_location, departure_time, available_seats, price_per_person, route_waypoints) VALUES (:user_id, :from_location, :to_location, :departure_time, :available_seats, :price_per_person, :route_waypoints)'),
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
        from_location = request.args.get('from', '').strip()
        to_location = request.args.get('to', '').strip()
        max_price = request.args.get('max_price', type=int)
        user_id = request.args.get('user_id', type=int)
        include_own = request.args.get('include_own', 'true').lower() == 'true'
        
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
        search_range = request.args.get('range', type=int)
        
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        time_from = request.args.get('time_from', '').strip()
        time_to = request.args.get('time_to', '').strip()

        query = "SELECT r.*, u.name, u.rating FROM rides r LEFT JOIN users u ON r.user_id = u.id"
        conditions = []
        params = {}

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

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        with db.session.begin():
            rides = db.session.execute(db.text(query), params).fetchall()

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
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2) * math.sin(dlng/2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c

        result = []
        current_user_id = request.args.get('user_id', type=int)

        for ride in rides:
            waypoints = json.loads(ride[7]) if ride[7] else []
            
            from_city_name = ride[2].split(',')[0].strip()
            to_city_name = ride[3].split(',')[0].strip()
            
            from_coords = cities.get(from_city_name)
            to_coords = cities.get(to_city_name)
            
            distance = 999
            if user_lat and user_lng and search_range:
                from_coords = cities.get(ride[2].split(',')[0].strip())
                to_coords = cities.get(ride[3].split(',')[0].strip())
                
                if from_coords:
                    distance = calculate_distance(user_lat, user_lng, from_coords[0], from_coords[1])
                else:
                    continue
                
                if distance > search_range:
                    continue
            
            is_own = False
            if current_user_id and ride[1] == current_user_id:
                is_own = True

            is_reserved = False
            
            departure_time_val = parse_datetime_str(ride[4])

            result.append({
                'id': ride[0],
                'user_id': ride[1],
                'driver_name': ride[9],
                'driver_rating': float(ride[10]) if ride[10] is not None else 5.0,
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': departure_time_val.isoformat() if departure_time_val else None,
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'route_waypoints': waypoints,
                'distance': round(distance, 1),
                'is_own': is_own,
                'is_reserved': is_reserved,
                'from_coords': from_coords if from_coords else None,
                'to_coords': to_coords if to_coords else None
            })
        
        if user_lat and user_lng:
            result.sort(key=lambda x: x['distance'])
            
        return jsonify(result)
    except Exception as e:
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
            if '@' in query:
                user = db.session.execute(db.text('SELECT id, name, phone, email, rating FROM users WHERE email LIKE :query'), {'query': f'%{query}%'}).fetchone()
            else:
                user = db.session.execute(db.text('SELECT id, name, phone, email, rating FROM users WHERE name LIKE :query'), {'query': f'%{query}%'}).fetchone()
        
        if not user:
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        return jsonify({
            'id': user[0],
            'name': user[1],
            'phone': user[2],
            'email': user[3] or '',
            'rating': float(user[4]) if user[4] is not None else 5.0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/search-text', methods=['GET'])
def search_rides_text():
    try:
        from_location = request.args.get('from', '').strip()
        to_location = request.args.get('to', '').strip()
        max_price = request.args.get('max_price', type=int)
        user_id = request.args.get('user_id', type=int)
        include_own = request.args.get('include_own', 'true').lower() == 'true'
        
        query = "SELECT r.*, u.name, u.rating FROM rides r LEFT JOIN users u ON r.user_id = u.id"
        conditions = []
        params = {}

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

        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY r.departure_time ASC"

        with db.session.begin():
            rides = db.session.execute(db.text(query), params).fetchall()

        result = []
        for ride in rides:
            departure_time_val = parse_datetime_str(ride[4])
            result.append({
                'id': ride[0],
                'user_id': ride[1],
                'driver_name': (ride[9] if len(ride) > 9 else None) or 'Neznámý řidič',
                'driver_rating': float(ride[10]) if len(ride) > 10 and ride[10] is not None else 5.0,
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': departure_time_val.isoformat() if departure_time_val else None,
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'route_waypoints': json.loads(ride[7]) if ride[7] else []
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/all', methods=['GET'])
def get_all_rides():
    try:
        with db.session.begin():
            rides = db.session.execute(db.text('SELECT r.*, u.name, u.rating FROM rides r LEFT JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC')).fetchall()
        
        result = []
        for ride in rides:
            departure_time_val = parse_datetime_str(ride[4])
            created_at_val = parse_datetime_str(ride[8])
            result.append({
                'id': ride[0],
                'user_id': ride[1],
                'driver_name': (ride[9] if len(ride) > 9 else None) or 'Neznámý řidič',
                'driver_rating': float(ride[10]) if len(ride) > 10 and ride[10] is not None else 5.0,
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': departure_time_val.isoformat() if departure_time_val else None,
                'available_seats': ride[5],
                'price_per_person': ride[6],
                'route_waypoints': json.loads(ride[7]) if ride[7] else [],
                'created_at': created_at_val.isoformat() if created_at_val else None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# SocketIO handlers removed due to compatibility issues

@app.route('/api/reservations/create', methods=['POST'])
def create_reservation():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        passenger_id = data.get('passenger_id')
        
        if not passenger_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        seats_reserved = data.get('seats_reserved', 1)
        
        with db.session.begin():
            ride = db.session.execute(db.text('SELECT available_seats FROM rides WHERE id = :ride_id'), {'ride_id': ride_id}).fetchone()
            
            if not ride or ride[0] < seats_reserved:
                return jsonify({'error': 'Nedostatek volných míst'}), 400
            
            db.session.execute(db.text('INSERT INTO reservations (ride_id, passenger_id, seats_reserved, status) VALUES (:ride_id, :passenger_id, :seats_reserved, \'confirmed\')'),
                             {'ride_id': ride_id, 'passenger_id': passenger_id, 'seats_reserved': seats_reserved})
            
            db.session.execute(db.text('UPDATE rides SET available_seats = available_seats - :seats_reserved WHERE id = :ride_id'), 
                             {'seats_reserved': seats_reserved, 'ride_id': ride_id})
        
        return jsonify({'message': 'Rezervace úspěšně vytvořena'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations/user/<int:user_id>')
def get_user_reservations_simple(user_id):
    try:
        with db.session.begin():
            reservations = db.session.execute(db.text("""
                SELECT res.id, res.seats_reserved, res.status, res.created_at,
                       r.from_location, r.to_location, r.departure_time, r.price_per_person,
                       u.name as driver_name, u.phone as driver_phone, r.id as ride_id
                FROM reservations res
                JOIN rides r ON res.ride_id = r.id
                JOIN users u ON r.user_id = u.id
                WHERE res.passenger_id = :user_id AND res.status = 'confirmed'
                ORDER BY r.departure_time ASC
            """), {'user_id': user_id}).fetchall()
        
            result = []
            for res in reservations:
                payment = db.session.execute(db.text('SELECT status FROM payments WHERE ride_id = :ride_id AND passenger_id = :user_id AND status = \'completed\''), 
                                               {'ride_id': res[10], 'user_id': user_id}).fetchone()
                
                driver_phone = res[9] if payment else "Skryto - zaplaťte nejdříve"
                
                departure_time_val = parse_datetime_str(res[6])
                created_at_val = parse_datetime_str(res[3])

                result.append({
                    'reservation_id': res[0],
                    'seats_reserved': res[1],
                    'status': res[2],
                    'created_at': created_at_val.isoformat() if created_at_val else None,
                    'from_location': res[4],
                    'to_location': res[5],
                    'departure_time': departure_time_val.isoformat() if departure_time_val else None,
                    'price_per_person': res[7],
                    'driver_name': res[8],
                    'driver_phone': driver_phone,
                    'is_paid': bool(payment)
                })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations/<int:reservation_id>')
def get_reservation_details(reservation_id):
    try:
        with db.session.begin():
            reservation = db.session.execute(db.text("""
                SELECT res.id, res.ride_id, res.passenger_id, res.seats_reserved, res.status,
                       r.from_location, r.to_location, r.departure_time, r.price_per_person
                FROM reservations res
                JOIN rides r ON res.ride_id = r.id
                WHERE res.id = :reservation_id
            """), {'reservation_id': reservation_id}).fetchone()
        
        if not reservation:
            return jsonify({'error': 'Rezervace nenalezena'}), 404
        
        departure_time_val = parse_datetime_str(reservation[7])
        
        return jsonify({
            'id': reservation[0],
            'ride_id': reservation[1],
            'passenger_id': reservation[2],
            'seats_reserved': reservation[3],
            'status': reservation[4],
            'from_location': reservation[5],
            'to_location': reservation[6],
            'departure_time': departure_time_val.isoformat() if departure_time_val else None,
            'price_per_person': reservation[8]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations/driver/<int:driver_id>')
def get_driver_reservations(driver_id):
    try:
        with db.session.begin():
            reservations = db.session.execute(db.text("""
                SELECT res.id, res.seats_reserved, res.status, res.created_at,
                       r.from_location, r.to_location, r.departure_time, r.id as ride_id,
                       u.name as passenger_name, u.id as passenger_id
                FROM reservations res
                JOIN rides r ON res.ride_id = r.id
                JOIN users u ON res.passenger_id = u.id
                WHERE r.user_id = :driver_id AND res.status = 'confirmed'
                ORDER BY r.departure_time DESC
            """), {'driver_id': driver_id}).fetchall()
        
        result = []
        for res in reservations:
            departure_time_val = parse_datetime_str(res[6])
            created_at_val = parse_datetime_str(res[3])
            result.append({
                'reservation_id': res[0],
                'seats_reserved': res[1],
                'status': res[2],
                'created_at': created_at_val.isoformat() if created_at_val else None,
                'from_location': res[4],
                'to_location': res[5],
                'departure_time': departure_time_val.isoformat() if departure_time_val else None,
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
        with db.session.begin():
            db.session.execute(db.text('UPDATE reservations SET status = \'cancelled\' WHERE ride_id = :ride_id'), {'ride_id': ride_id})
            db.session.execute(db.text('DELETE FROM rides WHERE id = :ride_id'), {'ride_id': ride_id})
        
        return jsonify({'message': 'Jízda zrušena'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations/cancel/<int:reservation_id>', methods=['DELETE'])
def cancel_reservation_new(reservation_id):
    try:
        with db.session.begin():
            reservation = db.session.execute(db.text('SELECT ride_id, seats_reserved FROM reservations WHERE id = :reservation_id'), 
                                               {'reservation_id': reservation_id}).fetchone()
            
            if not reservation:
                return jsonify({'error': 'Rezervace nenalezena'}), 404
            
            ride_id, seats_reserved = reservation
            
            db.session.execute(db.text('UPDATE reservations SET status = \'cancelled\' WHERE id = :reservation_id'), {'reservation_id': reservation_id})
            db.session.execute(db.text('UPDATE rides SET available_seats = available_seats + :seats_reserved WHERE id = :ride_id'), 
                             {'seats_reserved': seats_reserved, 'ride_id': ride_id})
        
        return jsonify({'message': 'Rezervace zrušena'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        sender_id = data.get('sender_id')
        
        if not sender_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        message = data.get('message')
        
        with db.session.begin():
            db.session.execute(db.text('INSERT INTO messages (ride_id, sender_id, message) VALUES (:ride_id, :sender_id, :message)'),
                             {'ride_id': ride_id, 'sender_id': sender_id, 'message': message})
        
        return jsonify({'message': 'Zpráva odeslána'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    try:
        with db.session.begin():
            user = db.session.execute(db.text('SELECT id, name, phone, email, rating, created_at, home_city FROM users WHERE id = :user_id'), {'user_id': user_id}).fetchone()
            
            if not user:
                return jsonify({'error': 'Uživatel nenalezen'}), 404
            
            # Základní profil
            profile = {
                'id': user[0],
                'name': user[1],
                'phone': user[2],
                'email': user[3] or '',
                'rating': float(user[4]) if user[4] is not None else 5.0,
                'member_since': parse_datetime_str(user[5]).isoformat() if user[5] else None,
                'home_city': user[6] or 'Neznámé',
                'verified': False,
                'bio': ''
            }
            
            # Počet jízd jako řidič
            driver_rides = db.session.execute(db.text('SELECT COUNT(*) FROM rides WHERE user_id = :user_id'), {'user_id': user_id}).fetchone()
            profile['rides_as_driver'] = driver_rides[0] if driver_rides else 0
            
            # Počet jízd jako pasažér
            passenger_rides = db.session.execute(db.text('SELECT COUNT(*) FROM reservations WHERE passenger_id = :user_id AND status = "confirmed"'), {'user_id': user_id}).fetchone()
            profile['rides_as_passenger'] = passenger_rides[0] if passenger_rides else 0
            
            profile['total_rides'] = profile['rides_as_driver'] + profile['rides_as_passenger']
            
            # Načtení recenzí
            reviews_data = db.session.execute(db.text("""
                SELECT r.rating, r.comment, r.created_at, u.name as rater_name
                FROM ratings r
                JOIN users u ON r.rater_id = u.id
                WHERE r.rated_id = :user_id AND r.comment IS NOT NULL AND r.comment != ''
                ORDER BY r.created_at DESC
                LIMIT 10
            """), {'user_id': user_id}).fetchall()
            
            profile['reviews'] = []
            for review in reviews_data:
                profile['reviews'].append({
                    'rating': review[0],
                    'comment': review[1],
                    'date': parse_datetime_str(review[2]).isoformat() if review[2] else None,
                    'reviewer': review[3]
                })
            
            # Načtení posledních jízd
            recent_rides_data = db.session.execute(db.text("""
                SELECT 'driver' as role, from_location, to_location, departure_time as date FROM rides WHERE user_id = :user_id
                UNION ALL
                SELECT 'passenger' as role, r.from_location, r.to_location, r.departure_time as date FROM reservations res JOIN rides r ON res.ride_id = r.id WHERE res.passenger_id = :user_id AND res.status = 'confirmed'
                ORDER BY date DESC
                LIMIT 5
            """), {'user_id': user_id}).fetchall()
            
            profile['recent_rides'] = []
            for ride in recent_rides_data:
                profile['recent_rides'].append({
                    'role': ride[0],
                    'from': ride[1],
                    'to': ride[2],
                    'date': parse_datetime_str(ride[3]).isoformat() if ride[3] else None
                })
            
            print(f"Returning profile for user {user_id}: {json.dumps(profile, indent=2, default=str)}")
        return jsonify(profile), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<user_name>/reviews', methods=['GET'])
def get_user_reviews(user_name):
    try:
        with db.session.begin():
            user = db.session.execute(db.text('SELECT id FROM users WHERE name = :user_name'), {'user_name': user_name}).fetchone()
            
            if not user:
                return jsonify({'error': 'Uživatel nenalezen'}), 404
            
            user_id = user[0]
            
            reviews = db.session.execute(db.text("""
                SELECT r.rating, r.comment, r.created_at, u.name as rater_name
                FROM ratings r
                JOIN users u ON r.rater_id = u.id
                WHERE r.rated_id = :user_id AND r.comment IS NOT NULL AND r.comment != ''
                ORDER BY r.created_at DESC
                LIMIT 5
            """), {'user_id': user_id}).fetchall()
        
        result = []
        for review in reviews:
            created_at_val = parse_datetime_str(review[2])
            result.append({
                'rating': review[0],
                'comment': review[1],
                'created_at': created_at_val.isoformat() if created_at_val else None,
                'rater_name': review[3]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/locations', methods=['GET'])
def get_user_locations():
    try:
        # Vrátí prázdný seznam, protože SocketIO není aktivní
        return jsonify([]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        sender_name = data.get('sender_name')
        message = data.get('message')
        
        if not all([ride_id, sender_name, message]):
            return jsonify({'error': 'Všechna pole jsou povinná'}), 400
        
        # Find sender_id by name
        with db.session.begin():
            user = db.session.execute(db.text('SELECT id FROM users WHERE name = :name'), {'name': sender_name}).fetchone()
            if not user:
                return jsonify({'error': 'Uživatel nenalezen'}), 404
            
            sender_id = user[0]
            db.session.execute(db.text('INSERT INTO messages (ride_id, sender_id, message) VALUES (:ride_id, :sender_id, :message)'),
                             {'ride_id': ride_id, 'sender_id': sender_id, 'message': message})
        
        return jsonify({'message': 'Zpráva odeslána'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<int:ride_id>/messages', methods=['GET'])
def get_chat_messages(ride_id):
    try:
        with db.session.begin():
            messages = db.session.execute(db.text("""
                SELECT m.message, m.created_at, m.sender_id, u.name as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.ride_id = :ride_id
                ORDER BY m.created_at ASC
            """), {'ride_id': ride_id}).fetchall()
        
        result = []
        for msg in messages:
            created_at_val = parse_datetime_str(msg[1])
            result.append({
                'message': msg[0],
                'created_at': created_at_val.isoformat() if created_at_val else None,
                'sender_id': msg[2],
                'sender_name': msg[3]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<user_name>', methods=['GET'])
def get_user_notifications(user_name):
    try:
        with db.session.begin():
            # Najdi user_id podle jména
            user = db.session.execute(db.text('SELECT id FROM users WHERE name = :name'), {'name': user_name}).fetchone()
            if not user:
                print(f"User {user_name} not found")
                return jsonify([]), 200
            
            user_id = user[0]
            print(f"Found user {user_name} with ID {user_id}")
            
            # Najdi zprávy z posledních 30 minut (pro testování)
            thirty_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=30)
            print(f"Looking for messages after {thirty_minutes_ago}")
            
            # Nejdříve zobraz všechny zprávy pro debug
            all_messages = db.session.execute(db.text("""
                SELECT m.ride_id, m.message, m.created_at, u.name as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                ORDER BY m.created_at DESC
                LIMIT 10
            """)).fetchall()
            
            print(f"All recent messages ({len(all_messages)}):")
            for msg in all_messages:
                print(f"  - {msg[3]}: '{msg[1]}' at {msg[2]}")
            
            # Pak filtruj podle času
            messages = db.session.execute(db.text("""
                SELECT m.ride_id, m.message, m.created_at, u.name as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.created_at > :thirty_minutes_ago
                ORDER BY m.created_at DESC
                LIMIT 5
            """), {'thirty_minutes_ago': thirty_minutes_ago}).fetchall()
            
            print(f"Found {len(messages)} messages in last 30 minutes")
        
        result = []
        for msg in messages:
            created_at_val = parse_datetime_str(msg[2])
            result.append({
                'ride_id': msg[0],
                'message': msg[1],
                'created_at': created_at_val.isoformat() if created_at_val else None,
                'sender_name': msg[3]
            })
        
        # Pro testování - přidej vždy jednu testovací notifikaci
        if user_name == "Pokus Pokus":
            result.append({
                'ride_id': 34,
                'message': f'TEST: Kontrola notifikací pro {user_name} - čas: {datetime.datetime.now().strftime("%H:%M:%S")}',
                'created_at': datetime.datetime.now().isoformat(),
                'sender_name': 'TestSystém'
            })
        
        print(f"Final notifications for {user_name}: {len(result)} messages")
        for notif in result:
            print(f"  Notification: {notif['sender_name']} - {notif['message'][:30]}...")
        print(f"Returning: {result}")
        return jsonify(result), 200
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in notifications: {str(e)}")
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
        
        with db.session.begin():
            rated_id = None
            if driver_name:
                user = db.session.execute(db.text('SELECT id FROM users WHERE name = :driver_name'), {'driver_name': driver_name}).fetchone()
                if user:
                    rated_id = user[0]
            
            if not rated_id:
                rated_id = data.get('rated_id', 0)
            
            db.session.execute(db.text('INSERT INTO ratings (ride_id, rater_id, rated_id, rating, comment) VALUES (:ride_id, :rater_id, :rated_id, :rating, :comment)'),
                             {'ride_id': ride_id, 'rater_id': rater_id, 'rated_id': rated_id, 'rating': rating, 'comment': comment})
            
            if rated_id:
                avg_rating_result = db.session.execute(db.text('SELECT AVG(rating) FROM ratings WHERE rated_id = :rated_id'), {'rated_id': rated_id}).fetchone()
                avg_rating = avg_rating_result[0] if avg_rating_result else None
                if avg_rating:
                    db.session.execute(db.text('UPDATE users SET rating = :avg_rating WHERE id = :rated_id'), {'avg_rating': avg_rating, 'rated_id': rated_id})
        
        return jsonify({'message': 'Hodnocení odesláno'}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)