import json
import hashlib
from datetime import datetime, timedelta

def add_test_data():
    # Import app and db here to avoid circular imports
    from app import app, db
    from spolujizda_core.models import User, Ride

    # Use the application context
    with app.app_context():
        # Vymaž existující data
        # Use SQLAlchemy to delete data to ensure it hits the correct database
        db.session.query(Ride).delete()
        db.session.query(User).delete()
        db.session.commit()

        # Přidej testovací uživatele
        users = [
            User(name='Jan Novák', phone='+420123456789', email='jan@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=4.8),
            User(name='Marie Svobodová', phone='+420987654321', email='marie@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=4.9),
            User(name='Petr Dvořák', phone='+420555666777', email='petr@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=4.7),
            User(name='Anna Nováková', phone='+420111222333', email='anna@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=5.0),
            User(name='Tomáš Procházka', phone='+420444555666', email='tomas@email.cz', password_hash=hashlib.sha256('heslo123'.encode()).hexdigest(), rating=4.6)
        ]
        
        db.session.bulk_save_objects(users)
        db.session.commit()

        # Přidej testovací jízdy s GPS souřadnicemi
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
        
        # Get user objects to assign them to rides
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
            ]))
        ]
        
        db.session.bulk_save_objects(rides)
        db.session.commit()

        print("✅ Testovací data přidána do správné databáze!")
        print("📍 Přidáno 5 uživatelů a 5 jízd s GPS souřadnicemi")
        print("🔑 Všichni uživatelé mají heslo: heslo123")

if __name__ == '__main__':
    add_test_data()