#!/usr/bin/env python3
"""
Mobile-optimized Flask app for Spolujizda
Includes PWA features, mobile-first design, and enhanced functionality
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import json
import datetime
from enhanced_app import *

app = Flask(__name__)
CORS(app)

# PWA Configuration
@app.route('/manifest.json')
def manifest():
    return jsonify({
        "name": "Spolujízda Enhanced",
        "short_name": "Spolujízda",
        "description": "Pokročilá aplikace pro sdílení jízd",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#2196F3",
        "theme_color": "#2196F3",
        "orientation": "portrait-primary",
        "icons": [
            {
                "src": "/static/icons/icon-72x72.png",
                "sizes": "72x72",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-96x96.png",
                "sizes": "96x96",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-128x128.png",
                "sizes": "128x128",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-144x144.png",
                "sizes": "144x144",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-152x152.png",
                "sizes": "152x152",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-384x384.png",
                "sizes": "384x384",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "categories": ["travel", "transportation", "social"],
        "lang": "cs",
        "dir": "ltr"
    })

@app.route('/mobile')
def mobile_app():
    return render_template('mobile_app.html')

# Enhanced API endpoints for mobile

@app.route('/api/rides/nearby', methods=['GET'])
def get_nearby_rides():
    """Get rides near user's location"""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', 10, type=int)  # km
        
        if not lat or not lng:
            return jsonify({'error': 'Poloha je vyžadována'}), 400
        
        # Calculate distance using Haversine formula
        query = """
        SELECT r.*, u.name, u.rating,
               (6371 * acos(cos(radians(?)) * cos(radians(r.from_lat)) * 
               cos(radians(r.from_lng) - radians(?)) + 
               sin(radians(?)) * sin(radians(r.from_lat)))) AS distance
        FROM rides r
        JOIN users u ON r.driver_id = u.id
        WHERE r.status = 'active'
        HAVING distance < ?
        ORDER BY distance
        """
        
        with db.session.begin():
            rides = db.session.execute(db.text(query), 
                                     (lat, lng, lat, radius)).fetchall()
        
        result = []
        for ride in rides:
            result.append({
                'id': ride[0],
                'driver_name': ride[-3],
                'driver_rating': ride[-2],
                'from_location': ride[2],
                'to_location': ride[3],
                'departure_time': ride[6].isoformat() if ride[6] else None,
                'available_seats': ride[7],
                'price': ride[8],
                'distance': round(ride[-1], 1)
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/location', methods=['POST'])
def update_user_location_enhanced(user_id):
    """Enhanced location update with accuracy and speed"""
    try:
        data = request.get_json()
        
        location_data = {
            'user_id': user_id,
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'accuracy': data.get('accuracy'),
            'speed': data.get('speed'),
            'heading': data.get('heading'),
            'timestamp': datetime.datetime.now()
        }
        
        # Store in Redis for real-time tracking
        # redis_client.setex(f"location:{user_id}", 300, json.dumps(location_data))
        
        return jsonify({'message': 'Poloha aktualizována'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/<int:ride_id>/track', methods=['GET'])
def track_ride(ride_id):
    """Real-time ride tracking"""
    try:
        # Get ride participants
        with db.session.begin():
            ride = db.session.execute(db.text(
                'SELECT driver_id FROM rides WHERE id = ?'
            ), (ride_id,)).fetchone()
            
            if not ride:
                return jsonify({'error': 'Jízda nenalezena'}), 404
            
            passengers = db.session.execute(db.text(
                'SELECT passenger_id FROM bookings WHERE ride_id = ? AND status = "confirmed"'
            ), (ride_id,)).fetchall()
        
        # Get current locations from Redis
        locations = {}
        participant_ids = [ride[0]] + [p[0] for p in passengers]
        
        for user_id in participant_ids:
            # location_data = redis_client.get(f"location:{user_id}")
            # if location_data:
            #     locations[user_id] = json.loads(location_data)
            pass
        
        return jsonify(locations), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat/translate', methods=['POST'])
def translate_message():
    """Translate chat messages"""
    try:
        data = request.get_json()
        text = data.get('text')
        target_lang = data.get('target', 'cs')
        
        # Use Google Translate API or similar service
        # For demo, return original text
        translated_text = text  # Replace with actual translation
        
        return jsonify({
            'original': text,
            'translated': translated_text,
            'target_language': target_lang
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/emergency/alert', methods=['POST'])
def emergency_alert():
    """Emergency alert system"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        ride_id = data.get('ride_id')
        message = data.get('message', 'Nouzová situace!')
        
        # Send alert to emergency contacts and ride participants
        # Implementation would include SMS, push notifications, etc.
        
        return jsonify({'message': 'Nouzové upozornění odesláno'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/recurring', methods=['POST'])
def create_recurring_ride():
    """Create recurring rides for daily commuting"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení vyžadováno'}), 401
        
        # Create multiple rides based on recurring pattern
        days = data.get('recurring_days', [])  # ['monday', 'tuesday', ...]
        start_date = datetime.datetime.fromisoformat(data.get('start_date'))
        end_date = datetime.datetime.fromisoformat(data.get('end_date'))
        
        created_rides = []
        current_date = start_date
        
        while current_date <= end_date:
            day_name = current_date.strftime('%A').lower()
            if day_name in days:
                ride_time = datetime.datetime.combine(
                    current_date.date(),
                    datetime.time.fromisoformat(data.get('departure_time'))
                )
                
                ride = Ride(
                    driver_id=user_id,
                    from_location=data.get('from_location'),
                    to_location=data.get('to_location'),
                    departure_time=ride_time,
                    available_seats=data.get('available_seats'),
                    price=data.get('price'),
                    recurring=True,
                    recurring_days=','.join(days)
                )
                
                db.session.add(ride)
                created_rides.append(ride)
            
            current_date += datetime.timedelta(days=1)
        
        db.session.commit()
        
        return jsonify({
            'message': f'Vytvořeno {len(created_rides)} opakujících se jízd',
            'rides_created': len(created_rides)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<int:user_id>/preferences', methods=['GET', 'POST'])
def user_preferences(user_id):
    """User preferences for notifications, privacy, etc."""
    if request.method == 'GET':
        try:
            # Get user preferences from database
            preferences = {
                'notifications': {
                    'new_messages': True,
                    'ride_updates': True,
                    'marketing': False
                },
                'privacy': {
                    'show_phone': False,
                    'show_location': True,
                    'auto_accept_bookings': False
                },
                'language': 'cs',
                'currency': 'CZK'
            }
            
            return jsonify(preferences), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            # Save preferences to database
            
            return jsonify({'message': 'Nastavení uloženo'}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    print(f"Starting mobile-optimized server on port {port}")
    app.run(debug=True, host='0.0.0.0', port=port)