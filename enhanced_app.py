from flask import Flask, request, jsonify, render_template, send_from_directory, redirect, Response
from flask_cors import CORS
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
import bcrypt
import secrets
from markupsafe import escape
import re
from collections import defaultdict
from time import time

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Configure SQLAlchemy
db_url = os.environ.get('DATABASE_URL')
if db_url and db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+psycopg2://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///spolujizda_enhanced.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Security configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=3600
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Enhanced Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_verified = db.Column(db.Boolean, default=False)
    profile_photo = db.Column(db.String(255))
    id_verified = db.Column(db.Boolean, default=False)
    license_verified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=5.0)
    total_rides = db.Column(db.Integer, default=0)
    home_city = db.Column(db.String(100))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class Ride(db.Model):
    __tablename__ = 'rides'
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_location = db.Column(db.String(200), nullable=False)
    to_location = db.Column(db.String(200), nullable=False)
    from_lat = db.Column(db.Float)
    from_lng = db.Column(db.Float)
    to_lat = db.Column(db.Float)
    to_lng = db.Column(db.Float)
    departure_time = db.Column(db.DateTime, nullable=False)
    available_seats = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    car_model = db.Column(db.String(100))
    car_color = db.Column(db.String(50))
    smoking_allowed = db.Column(db.Boolean, default=False)
    pets_allowed = db.Column(db.Boolean, default=False)
    recurring = db.Column(db.Boolean, default=False)
    recurring_days = db.Column(db.String(20))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    passenger_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seats_booked = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='unpaid')
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class Rating(db.Model):
    __tablename__ = 'ratings'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    rater_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rated_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='CZK')
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class FavoriteRoute(db.Model):
    __tablename__ = 'favorite_routes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    from_location = db.Column(db.String(200), nullable=False)
    to_location = db.Column(db.String(200), nullable=False)
    from_lat = db.Column(db.Float)
    from_lng = db.Column(db.Float)
    to_lat = db.Column(db.Float)
    to_lng = db.Column(db.Float)
    name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'
    id = db.Column(db.Integer, primary_key=True)
    ride_id = db.Column(db.Integer, db.ForeignKey('rides.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sender_name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(20), default='text')
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now)

# Rate limiting
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

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_placeholder')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_placeholder')

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

# Enhanced API Endpoints

@app.route('/')
def home():
    return render_template('enhanced_app.html')

@app.route('/api/users/register', methods=['POST'])
@rate_limit(max_requests=5, window=300)
def register():
    try:
        data = request.get_json()
        name = escape(data.get('name', '').strip())
        phone = escape(data.get('phone', '').strip())
        password = data.get('password')
        email = data.get('email', '').strip()
        
        # Validation
        if len(name) < 2:
            return jsonify({'error': 'Jméno musí mít alespoň 2 znaky'}), 400
            
        forbidden_names = ['neznámý', 'unknown', 'test', 'admin', 'null']
        if any(forbidden in name.lower() for forbidden in forbidden_names):
            return jsonify({'error': 'Zadejte platné jméno'}), 400
        
        phone_clean = re.sub(r'[^\d]', '', phone)
        if phone_clean.startswith('420'):
            phone_clean = phone_clean[3:]
        
        if len(phone_clean) != 9:
            return jsonify({'error': 'Neplatný formát telefonu'}), 400
        
        phone_full = f'+420{phone_clean}'
        
        if email and '@' not in email:
            return jsonify({'error': 'Neplatný formát emailu'}), 400
        
        # Check existing users
        if User.query.filter_by(phone=phone_full).first():
            return jsonify({'error': 'Telefon již registrován'}), 409
        
        if email and User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email již registrován'}), 409
        
        # Create user
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        user = User(
            name=name,
            phone=phone_full,
            email=email if email else None,
            password_hash=password_hash
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'Registrace úspěšná', 'user_id': user.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/login', methods=['POST'])
@rate_limit(max_requests=10, window=300)
def login():
    try:
        data = request.get_json()
        login_field = data.get('phone')
        password = data.get('password')
        
        if not all([login_field, password]):
            return jsonify({'error': 'Telefon/email a heslo jsou povinné'}), 400
        
        # Find user
        if '@' in login_field:
            user = User.query.filter_by(email=login_field).first()
        else:
            phone_clean = re.sub(r'[^\d]', '', login_field)
            if phone_clean.startswith('420'):
                phone_clean = phone_clean[3:]
            phone_full = f'+420{phone_clean}'
            user = User.query.filter_by(phone=phone_full).first()
        
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return jsonify({
                'message': 'Přihlášení úspěšné',
                'user_id': user.id,
                'name': user.name,
                'rating': user.rating,
                'phone_verified': user.phone_verified,
                'id_verified': user.id_verified
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
            return jsonify({'error': 'Přihlášení vyžadováno'}), 401
        
        ride = Ride(
            driver_id=user_id,
            from_location=data.get('from_location'),
            to_location=data.get('to_location'),
            from_lat=data.get('from_lat'),
            from_lng=data.get('from_lng'),
            to_lat=data.get('to_lat'),
            to_lng=data.get('to_lng'),
            departure_time=datetime.datetime.fromisoformat(data.get('departure_time')),
            available_seats=data.get('available_seats'),
            price=data.get('price'),
            description=data.get('description', ''),
            car_model=data.get('car_model', ''),
            car_color=data.get('car_color', ''),
            smoking_allowed=data.get('smoking_allowed', False),
            pets_allowed=data.get('pets_allowed', False),
            recurring=data.get('recurring', False),
            recurring_days=data.get('recurring_days', '')
        )
        
        db.session.add(ride)
        db.session.commit()
        
        return jsonify({'message': 'Jízda nabídnuta', 'ride_id': ride.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/search', methods=['GET'])
def search_rides():
    try:
        # Enhanced search parameters
        from_location = request.args.get('from', '').strip()
        to_location = request.args.get('to', '').strip()
        max_price = request.args.get('max_price', type=float)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        smoking_allowed = request.args.get('smoking_allowed', type=bool)
        pets_allowed = request.args.get('pets_allowed', type=bool)
        min_rating = request.args.get('min_rating', type=float)
        car_model = request.args.get('car_model', '').strip()
        
        query = db.session.query(Ride).join(User, Ride.driver_id == User.id)
        
        if from_location:
            query = query.filter(Ride.from_location.contains(from_location))
        if to_location:
            query = query.filter(Ride.to_location.contains(to_location))
        if max_price:
            query = query.filter(Ride.price <= max_price)
        if date_from:
            query = query.filter(Ride.departure_time >= datetime.datetime.fromisoformat(date_from))
        if date_to:
            query = query.filter(Ride.departure_time <= datetime.datetime.fromisoformat(date_to))
        if smoking_allowed is not None:
            query = query.filter(Ride.smoking_allowed == smoking_allowed)
        if pets_allowed is not None:
            query = query.filter(Ride.pets_allowed == pets_allowed)
        if min_rating:
            query = query.filter(User.rating >= min_rating)
        if car_model:
            query = query.filter(Ride.car_model.contains(car_model))
        
        query = query.filter(Ride.status == 'active')
        rides = query.all()
        
        result = []
        for ride in rides:
            driver = User.query.get(ride.driver_id)
            result.append({
                'id': ride.id,
                'driver_id': ride.driver_id,
                'driver_name': driver.name,
                'driver_rating': driver.rating,
                'driver_verified': driver.id_verified,
                'from_location': ride.from_location,
                'to_location': ride.to_location,
                'departure_time': ride.departure_time.isoformat(),
                'available_seats': ride.available_seats,
                'price': ride.price,
                'car_model': ride.car_model,
                'car_color': ride.car_color,
                'smoking_allowed': ride.smoking_allowed,
                'pets_allowed': ride.pets_allowed,
                'description': ride.description
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bookings/create', methods=['POST'])
def create_booking():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        passenger_id = data.get('passenger_id')
        seats_booked = data.get('seats_booked', 1)
        
        if not passenger_id:
            return jsonify({'error': 'Přihlášení vyžadováno'}), 401
        
        ride = Ride.query.get(ride_id)
        if not ride or ride.available_seats < seats_booked:
            return jsonify({'error': 'Nedostatek volných míst'}), 400
        
        booking = Booking(
            ride_id=ride_id,
            passenger_id=passenger_id,
            seats_booked=seats_booked,
            status='confirmed'
        )
        
        ride.available_seats -= seats_booked
        
        db.session.add(booking)
        db.session.commit()
        
        return jsonify({'message': 'Rezervace vytvořena', 'booking_id': booking.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/payments/create', methods=['POST'])
def create_payment():
    try:
        data = request.get_json()
        booking_id = data.get('booking_id')
        amount = data.get('amount')
        
        booking = Booking.query.get(booking_id)
        if not booking:
            return jsonify({'error': 'Rezervace nenalezena'}), 404
        
        # Create Stripe payment intent
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency='czk',
            metadata={'booking_id': booking_id}
        )
        
        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            transaction_id=intent.id,
            status='pending'
        )
        
        db.session.add(payment)
        db.session.commit()
        
        return jsonify({
            'client_secret': intent.client_secret,
            'payment_id': payment.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ratings/create', methods=['POST'])
def create_rating():
    try:
        data = request.get_json()
        
        rating = Rating(
            ride_id=data.get('ride_id'),
            rater_id=data.get('rater_id'),
            rated_id=data.get('rated_id'),
            rating=data.get('rating'),
            comment=data.get('comment', '')
        )
        
        db.session.add(rating)
        
        # Update user's average rating
        user = User.query.get(data.get('rated_id'))
        if user:
            avg_rating = db.session.query(db.func.avg(Rating.rating)).filter_by(rated_id=user.id).scalar()
            user.rating = avg_rating or 5.0
        
        db.session.commit()
        
        return jsonify({'message': 'Hodnocení odesláno'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/send', methods=['POST'])
def send_chat_message():
    try:
        data = request.get_json()
        
        message = ChatMessage(
            ride_id=data.get('ride_id'),
            sender_id=data.get('sender_id'),
            sender_name=data.get('sender_name'),
            message=escape(data.get('message')),
            message_type=data.get('message_type', 'text')
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({'message': 'Zpráva odeslána'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/<int:ride_id>/messages', methods=['GET'])
def get_chat_messages(ride_id):
    try:
        messages = ChatMessage.query.filter_by(ride_id=ride_id).order_by(ChatMessage.timestamp).all()
        
        result = []
        for msg in messages:
            result.append({
                'id': msg.id,
                'sender_id': msg.sender_id,
                'sender_name': msg.sender_name,
                'message': msg.message,
                'message_type': msg.message_type,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/favorites', methods=['GET'])
def get_favorite_routes(user_id):
    try:
        favorites = FavoriteRoute.query.filter_by(user_id=user_id).all()
        
        result = []
        for fav in favorites:
            result.append({
                'id': fav.id,
                'name': fav.name,
                'from_location': fav.from_location,
                'to_location': fav.to_location,
                'from_lat': fav.from_lat,
                'from_lng': fav.from_lng,
                'to_lat': fav.to_lat,
                'to_lng': fav.to_lng
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/favorites', methods=['POST'])
def add_favorite_route(user_id):
    try:
        data = request.get_json()
        
        favorite = FavoriteRoute(
            user_id=user_id,
            name=data.get('name'),
            from_location=data.get('from_location'),
            to_location=data.get('to_location'),
            from_lat=data.get('from_lat'),
            from_lng=data.get('from_lng'),
            to_lat=data.get('to_lat'),
            to_lng=data.get('to_lng')
        )
        
        db.session.add(favorite)
        db.session.commit()
        
        return jsonify({'message': 'Oblíbená trasa přidána', 'favorite_id': favorite.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/verify-phone', methods=['POST'])
def verify_phone(user_id):
    try:
        data = request.get_json()
        verification_code = data.get('code')
        
        # In production, verify with SMS service
        if verification_code == '123456':  # Demo code
            user = User.query.get(user_id)
            if user:
                user.phone_verified = True
                db.session.commit()
                return jsonify({'message': 'Telefon ověřen'}), 200
        
        return jsonify({'error': 'Neplatný kód'}), 400
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"Starting enhanced server on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)