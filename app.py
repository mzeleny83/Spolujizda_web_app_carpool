from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
import signal
import sys
import datetime
import json
import hashlib
from datetime import timedelta

from spolujizda_core.database import db
from spolujizda_core.auth.routes import auth_bp
from spolujizda_core.rides.routes import rides_bp
from spolujizda_core.models import Ride, User, Message
from backend_search_api import create_search_routes

app = Flask(__name__, instance_relative_config=True)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'spolujizda.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Add a secret key for session management

db.init_app(app)

# Register Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(rides_bp)

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

# ... (all other routes from app.py remain the same) ...

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
        emit('location_updated', {
            'user_id': user_id,
            'lat': lat,
            'lng': lng
        }, broadcast=True)

# ... (all other socketio handlers from app.py remain the same) ...

if __name__ == '__main__':
    def init_db_and_add_test_data():
        with app.app_context():
            print("Inicializace databáze...")
            db.drop_all()
            db.create_all()
            print("Všechny tabulky vytvořeny")

            # Add test data logic directly here
            print("Přidávám testovací data...")
            try:
                users = [
                    User(name='Jan Novák', phone='+420123456789', email='jan@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=4.8),
                    User(name='Marie Svobodová', phone='+420987654321', email='marie@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=4.9),
                    User(name='Petr Dvořák', phone='+420555666777', email='petr@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=4.7),
                    User(name='Anna Nováková', phone='+420111222333', email='anna@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=5.0),
                    User(name='Tomáš Procházka', phone='+420444555666', email='tomas@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=4.6)
                ]
                db.session.bulk_save_objects(users)
                db.session.commit()

                tomorrow = (datetime.datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
                user1 = User.query.filter_by(name='Jan Novák').first()
                user2 = User.query.filter_by(name='Marie Svobodová').first()
                user3 = User.query.filter_by(name='Petr Dvořák').first()
                user4 = User.query.filter_by(name='Anna Nováková').first()
                user5 = User.query.filter_by(name='Tomáš Procházka').first()

                rides = [
                    Ride(user_id=user1.id, from_location='Praha', to_location='Brno', departure_time=tomorrow, available_seats=3, price_per_person=300, route_waypoints=json.dumps([
                        {'lat': 50.0755, 'lng': 14.4378, 'name': 'Praha centrum'},
                        {'lat': 49.1951, 'lng': 16.6068, 'name': 'Brno centrum'}
                    ])),
                    Ride(user_id=user2.id, from_location='Ostrava', to_location='Praha', departure_time=tomorrow, available_seats=2, price_per_person=400, route_waypoints=json.dumps([
                        {'lat': 49.8209, 'lng': 18.2625, 'name': 'Ostrava centrum'},
                        {'lat': 50.0755, 'lng': 14.4378, 'name': 'Praha centrum'}
                    ])),
                    Ride(user_id=user3.id, from_location='Plzeň', to_location='České Budějovice', departure_time=tomorrow, available_seats=4, price_per_person=250, route_waypoints=json.dumps([
                        {'lat': 49.7384, 'lng': 13.3736, 'name': 'Plzeň centrum'},
                        {'lat': 48.9744, 'lng': 14.4742, 'name': 'České Budějovice centrum'}
                    ])),
                    Ride(user_id=user4.id, from_location='Liberec', to_location='Hradec Králové', departure_time=tomorrow, available_seats=1, price_per_person=200, route_waypoints=json.dumps([
                        {'lat': 50.7663, 'lng': 15.0543, 'name': 'Liberec centrum'},
                        {'lat': 50.2103, 'lng': 15.8327, 'name': 'Hradec Králové centrum'}
                    ])),
                    Ride(user_id=user5.id, from_location='Olomouc', to_location='Zlín', departure_time=tomorrow, available_seats=2, price_per_person=150, route_waypoints=json.dumps([
                        {'lat': 49.5938, 'lng': 17.2509, 'name': 'Olomouc centrum'},
                        {'lat': 49.2238, 'lng': 17.6696, 'name': 'Zlín centrum'}
                    ])),
                    Ride(user_id=user1.id, from_location='Brno', to_location='Praha', departure_time=tomorrow, available_seats=2, price_per_person=300, route_waypoints=json.dumps([
                        {'lat': 49.1951, 'lng': 16.6068, 'name': 'Brno centrum'},
                        {'lat': 50.0755, 'lng': 14.4378, 'name': 'Praha centrum'}
                    ]))
                ]
                db.session.bulk_save_objects(rides)
                db.session.commit()
                print("✅ Testovací data přidána do správné databáze!")
            except Exception as e:
                print(f"Chyba při přidávání testovacích dat: {e}")

    # Run setup
    init_db_and_add_test_data()

    # Activate advanced search routes
    try:
        create_search_routes(app)
        print("Pokročilé vyhledávání aktivováno")
    except Exception as e:
        print(f"Chyba při aktivaci pokročilého vyhledávání: {e}")

    # Add security headers
    @app.after_request
    def after_request(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    print("Server se spouští na http://localhost:8080")
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)