from flask import Blueprint, request, jsonify
from spolujizda_core.database import db
from spolujizda_core.models import Ride, User, Reservation, Message, Rating, RecurringRide
import json

rides_bp = Blueprint('rides', __name__, url_prefix='/api')

@rides_bp.route('/rides/offer', methods=['POST'])
def offer_ride():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        
        new_ride = Ride(
            user_id=user_id,
            from_location=data.get('from_location'),
            to_location=data.get('to_location'),
            departure_time=data.get('departure_time'),
            available_seats=data.get('available_seats'),
            price_per_person=data.get('price_per_person'),
            route_waypoints=json.dumps(data.get('route_waypoints', []))
        )
        db.session.add(new_ride)
        db.session.commit()
        
        return jsonify({
            'message': 'Jízda úspěšně nabídnuta',
            'ride_id': new_ride.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@rides_bp.route('/rides/search', methods=['GET'])
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
        
        query = Ride.query.join(User).filter(User.id == Ride.user_id)

        if max_price and str(max_price).isdigit():
            query = query.filter(Ride.price_per_person <= int(max_price))

        rides = query.all()
        
        reservations = []
        if user_id > 0:
            reservations = [r.ride_id for r in Reservation.query.filter_by(passenger_id=user_id, status='confirmed').all()]

        import math
        
        def calculate_distance(lat1, lng1, lat2, lng2):
            R = 6371
            dlat = math.radians(lat2 - lat1)
            dlng = math.radians(lng2 - lng1)
            a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        result = []
        print(f"[Debug] Searching with location: ({user_lat}, {user_lng}) and range: {search_range}km")
        for ride in rides:
            try:
                waypoints = json.loads(ride.route_waypoints) if ride.route_waypoints else []
            except json.JSONDecodeError:
                print(f"Chyba dekódování JSON pro jízdu ID: {ride.id}. Waypoints budou ignorovány.")
                waypoints = []
            
            distance = search_range + 1
            
            if user_lat and user_lng:
                min_distance = float('inf')
                if waypoints:
                    for waypoint in waypoints:
                        if isinstance(waypoint, dict) and 'lat' in waypoint and 'lng' in waypoint:
                            wp_distance = calculate_distance(user_lat, user_lng, waypoint['lat'], waypoint['lng'])
                            min_distance = min(min_distance, wp_distance)
                
                if min_distance != float('inf'):
                    distance = min_distance
                print(f"[Debug] Ride ID: {ride.id}, Min distance to waypoints: {distance:.2f}km")
            else:
                distance = 0
            
            if user_lat and user_lng and distance > search_range:
                print(f"[Debug] Skipping Ride ID: {ride.id}, Name: {ride.from_location} -> {ride.to_location}. Distance {distance:.2f}km > Range {search_range}km")
                continue
            
            is_own = (user_id > 0 and ride.user_id == user_id)
            is_reserved = (ride.id in reservations)
            
            result.append({
                'id': ride.id,
                'user_id': ride.user_id,
                'driver_name': ride.user.name,
                'driver_rating': ride.user.rating or 5.0,
                'from_location': ride.from_location,
                'to_location': ride.to_location,
                'departure_time': ride.departure_time,
                'available_seats': ride.available_seats,
                'price_per_person': ride.price_per_person,
                'route_waypoints': waypoints,
                'distance': round(distance, 1),
                'is_own': is_own,
                'is_reserved': is_reserved
            })
        
        result.sort(key=lambda x: x['distance'])
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Chyba v search_rides: {e}")
        return jsonify({'error': str(e)}), 500

@rides_bp.route('/rides/all', methods=['GET'])
def get_all_rides():
    try:
        user_id = int(request.args.get('user_id', 0))

        rides = Ride.query.join(User).order_by(Ride.created_at.desc()).all()
        
        reservations = []
        if user_id > 0:
            reservations = [r.ride_id for r in Reservation.query.filter_by(passenger_id=user_id, status='confirmed').all()]

        result = []
        for ride in rides:
            try:
                waypoints = json.loads(ride.route_waypoints) if ride.route_waypoints else []
            except json.JSONDecodeError:
                waypoints = []

            is_own = (user_id > 0 and ride.user_id == user_id)
            is_reserved = (ride.id in reservations)

            result.append({
                'id': ride.id,
                'user_id': ride.user_id,
                'driver_name': ride.user.name or 'Neznámý řidič',
                'driver_rating': ride.user.rating or 5.0,
                'from_location': ride.from_location,
                'to_location': ride.to_location,
                'departure_time': ride.departure_time,
                'available_seats': ride.available_seats,
                'price_per_person': ride.price_per_person,
                'route_waypoints': waypoints,
                'distance': 0, # Default distance
                'is_own': is_own,
                'is_reserved': is_reserved,
                'created_at': ride.created_at.isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@rides_bp.route('/reservations/create', methods=['POST'])
def create_reservation():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        passenger_id = data.get('passenger_id')
        
        if not passenger_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        seats_reserved = data.get('seats_reserved', 1)
        
        ride = Ride.query.get(ride_id)
        
        if not ride or ride.available_seats < seats_reserved:
            return jsonify({'error': 'Nedostatek volných míst'}), 400
        
        new_reservation = Reservation(
            ride_id=ride_id,
            passenger_id=passenger_id,
            seats_reserved=seats_reserved,
            status='confirmed'
        )
        
        ride.available_seats -= seats_reserved
        
        db.session.add(new_reservation)
        db.session.commit()
        
        return jsonify({'message': 'Rezervace úspěšně vytvořena'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@rides_bp.route('/messages/send', methods=['POST'])
def send_message():
    try:
        data = request.get_json()
        ride_id = data.get('ride_id')
        sender_id = data.get('sender_id')
        
        if not sender_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        message = data.get('message')
        
        new_message = Message(
            ride_id=ride_id,
            sender_id=sender_id,
            message=message
        )
        db.session.add(new_message)
        db.session.commit()
        
        return jsonify({'message': 'Zpráva odeslána'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@rides_bp.route('/ratings/create', methods=['POST'])
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
        
        new_rating = Rating(
            ride_id=ride_id,
            rater_id=rater_id,
            rated_id=rated_id,
            rating=rating,
            comment=comment
        )
        db.session.add(new_rating)
        
        # Aktualizace průměrného hodnocení
        avg_rating = db.session.query(db.func.avg(Rating.rating)).filter_by(rated_id=rated_id).scalar()
        user_to_update = User.query.get(rated_id)
        if user_to_update and avg_rating:
            user_to_update.rating = avg_rating
        
        db.session.commit()
        
        return jsonify({'message': 'Hodnocení odesláno'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@rides_bp.route('/rides/recurring', methods=['POST'])
def create_recurring_ride():
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        
        new_recurring_ride = RecurringRide(
            user_id=user_id,
            from_location=data.get('from_location'),
            to_location=data.get('to_location'),
            departure_time=data.get('departure_time'),
            days_of_week=','.join(data.get('days_of_week', [])),
            available_seats=data.get('available_seats'),
            price_per_person=data.get('price_per_person')
        )
        db.session.add(new_recurring_ride)
        db.session.commit()
        
        return jsonify({'message': 'Pravidelná jízda vytvořena'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@rides_bp.route('/rides/recurring', methods=['GET'])
def get_recurring_rides():
    try:
        user_id = request.args.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        
        query = RecurringRide.query.join(User).filter(RecurringRide.active == True)
        if user_id != '0':
            query = query.filter(RecurringRide.user_id == user_id)
            
        rides = query.all()
        
        result = []
        for ride in rides:
            result.append({
                'id': ride.id,
                'driver_name': ride.user.name or 'Neznámý řidič',
                'from_location': ride.from_location,
                'to_location': ride.to_location,
                'departure_time': ride.departure_time,
                'days_of_week': ride.days_of_week.split(','),
                'available_seats': ride.available_seats,
                'price_per_person': ride.price_per_person,
                'active': ride.active
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500