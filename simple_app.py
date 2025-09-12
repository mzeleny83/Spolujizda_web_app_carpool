from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import hashlib
import datetime
import os
import json
import traceback

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spolujizda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

app.debug = True
CORS(app, resources={'/*': {'origins': '*', 'methods': ['GET', 'POST', 'OPTIONS'], 'allow_headers': ['Content-Type']}})

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

@app.route('/')
def home():
    return render_template('app.html')

@app.route('/api/users/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        phone = data.get('phone')
        password = data.get('password')
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
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        with db.session.begin():
            existing_phone = db.session.execute(db.text('SELECT id FROM users WHERE phone = :phone'), {'phone': phone_full}).fetchone()
            if existing_phone:
                return jsonify({'error': 'Toto telefonní číslo je již registrováno'}), 409
            
            db.session.execute(db.text('INSERT INTO users (name, phone, email, password_hash, rating) VALUES (:name, :phone, :email, :password_hash, :rating)'),
                             {'name': name, 'phone': phone_full, 'email': email if email else None, 'password_hash': password_hash, 'rating': 5.0})
            
            return jsonify({'message': 'Uživatel úspěšně registrován'}), 201
            
    except Exception as e:
        traceback.print_exc()
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
        traceback.print_exc()
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
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/all', methods=['GET'])
def get_all_rides():
    try:
        with db.session.begin():
            rides = db.session.execute(db.text('SELECT r.*, u.name, u.rating FROM rides r LEFT JOIN users u ON r.user_id = u.id ORDER BY r.created_at DESC')).fetchall()
        
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
        traceback.print_exc()
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
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting simple server on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)