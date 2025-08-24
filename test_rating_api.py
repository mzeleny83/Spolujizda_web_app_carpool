import sqlite3
import json

DATABASE = 'spolujizda.db'

def test_rides_with_rating():
    print("=== TEST JÍZD S HODNOCENÍM ===")
    
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    
    # Simulace API dotazu pro všechny jízdy
    c.execute('''SELECT r.*, u.name, u.rating FROM rides r 
                 LEFT JOIN users u ON r.user_id = u.id
                 ORDER BY r.created_at DESC LIMIT 3''')
    rides = c.fetchall()
    
    result = []
    for ride in rides:
        ride_data = {
            'id': ride[0],
            'user_id': ride[1],
            'driver_name': ride[9] if len(ride) > 9 else 'Neznámý řidič',
            'driver_rating': ride[10] if len(ride) > 10 else 5.0,
            'from_location': ride[2],
            'to_location': ride[3],
            'departure_time': ride[4],
            'available_seats': ride[5],
            'price_per_person': ride[6],
            'created_at': ride[8]
        }
        result.append(ride_data)
        
        print(f"Jízda {ride_data['id']}:")
        print(f"  Řidič: {ride_data['driver_name']}")
        print(f"  Hodnocení: {ride_data['driver_rating']}")
        print(f"  Trasa: {ride_data['from_location']} → {ride_data['to_location']}")
        print()
    
    conn.close()
    return result

if __name__ == "__main__":
    test_rides_with_rating()