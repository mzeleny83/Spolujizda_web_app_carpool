import sqlite3
import json

DATABASE = 'spolujizda.db'

def simulate_api_all_rides():
    print("=== SIMULACE API /api/rides/all ===")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''SELECT r.*, u.name, u.rating FROM rides r 
                 LEFT JOIN users u ON r.user_id = u.id
                 ORDER BY r.created_at DESC LIMIT 3''')
    rides = c.fetchall()
    conn.close()
    
    result = []
    for ride in rides:
        ride_data = {
            'id': ride[0],
            'user_id': ride[1],
            'driver_name': (ride[9] if len(ride) > 9 else None) or 'Neznamy ridic',
            'driver_rating': (ride[10] if len(ride) > 10 else None) or 5.0,
            'from_location': ride[2],
            'to_location': ride[3],
            'departure_time': ride[4],
            'available_seats': ride[5],
            'price_per_person': ride[6],
            'route_waypoints': json.loads(ride[7]) if ride[7] else [],
            'created_at': ride[8]
        }
        result.append(ride_data)
        
        print(f"Jizda {ride_data['id']}:")
        print(f"  Ridic: {ride_data['driver_name']}")
        print(f"  Hodnoceni: {ride_data['driver_rating']}")
        print(f"  Trasa: {ride_data['from_location']} -> {ride_data['to_location']}")
        print()
    
    return result

if __name__ == "__main__":
    simulate_api_all_rides()