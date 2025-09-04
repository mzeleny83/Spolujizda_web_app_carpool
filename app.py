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
# Dummy comment to force Heroku rebuild

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

if __name__ == '__main__':
    print("Server se spouští na http://localhost:8080")
    port = int(os.environ.get('PORT', 8080))
    socketio.run(app, debug=False, host='0.0.0.0', port=port)
