from flask import Flask, request, jsonify
import sqlite3
import json
import re
from difflib import SequenceMatcher
from typing import List, Dict, Any
import math

class AdvancedSearchAPI:
    def __init__(self, database_path='spolujizda.db'):
        self.database_path = database_path
        
    def fuzzy_match(self, query: str, text: str, threshold: float = 0.6) -> bool:
        """Fuzzy matching algoritmus inspirovaný Waze"""
        similarity = SequenceMatcher(None, query.lower(), text.lower()).ratio()
        
        # Bonus za začátek slova
        if text.lower().startswith(query.lower()):
            similarity += 0.2
            
        # Bonus za obsahování
        if query.lower() in text.lower():
            similarity += 0.1
            
        return similarity >= threshold
    
    def calculate_confidence(self, query: str, text: str) -> float:
        """Výpočet confidence skóre"""
        similarity = SequenceMatcher(None, query.lower(), text.lower()).ratio()
        
        # Bonusy
        starts_with_bonus = 0.2 if text.lower().startswith(query.lower()) else 0
        contains_bonus = 0.1 if query.lower() in text.lower() else 0
        
        return min(1.0, similarity + starts_with_bonus + contains_bonus)
    
    def search_places(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Vyhledávání míst s fuzzy matching"""
        czech_cities = [
            'Praha', 'Brno', 'Ostrava', 'Plzeň', 'Liberec', 'Olomouc', 'Ústí nad Labem',
            'České Budějovice', 'Hradec Králové', 'Pardubice', 'Zlín', 'Havířov',
            'Kladno', 'Most', 'Opava', 'Frýdek-Místek', 'Karviná', 'Jihlava',
            'Děčín', 'Teplice', 'Chomutov', 'Jablonec nad Nisou', 'Mladá Boleslav',
            'Prostějov', 'Přerov', 'Česká Lípa', 'Třebíč', 'Uherské Hradiště',
            'Kolín', 'Písek', 'Trutnov', 'Vsetín', 'Valašské Meziříčí'
        ]
        
        results = []
        for city in czech_cities:
            if self.fuzzy_match(query, city):
                confidence = self.calculate_confidence(query, city)
                results.append({
                    'id': city.lower().replace(' ', '_'),
                    'text': city,
                    'type': 'place',
                    'icon': '🏙️',
                    'confidence': confidence,
                    'subtitle': f'Město v České republice'
                })
        
        # Seřazení podle confidence
        results.sort(key=lambda x: x['confidence'], reverse=True)
        return results[:limit]
    
    def search_rides_text(self, query: str, user_lat: float = None, user_lng: float = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Textové vyhledávání jízd"""
        try:
            conn = sqlite3.connect(self.database_path)
            c = conn.cursor()
            
            # Vyhledávání v from_location
            c.execute('''
                SELECT r.*, u.name, u.rating 
                FROM rides r 
                LEFT JOIN users u ON r.user_id = u.id
                WHERE r.from_location LIKE ?
                ORDER BY r.created_at DESC
                LIMIT ?
            ''', (f'%{query}%', limit * 2))
            
            rides = c.fetchall()
            conn.close()
            
            results = []
            for ride in rides:
                # Fuzzy matching pro lepší výsledky
                from_match = self.fuzzy_match(query, ride[2])  # from_location
                to_match = self.fuzzy_match(query, ride[3])    # to_location
                
                if from_match:
                    confidence = self.calculate_confidence(query, ride[2])
                    
                    results.append({
                        'id': f'ride_{ride[0]}',
                        'text': f'{ride[2]} → {ride[3]}',
                        'subtitle': f'{ride[4]} • {ride[10] or "Neznámý řidič"} • {ride[6]} Kč',
                        'type': 'ride',
                        'icon': '🚗',
                        'confidence': confidence,
                        'data': {
                            'id': ride[0],
                            'from_location': ride[2],
                            'to_location': ride[3],
                            'departure_time': ride[4],
                            'available_seats': ride[5],
                            'price_per_person': ride[6],
                            'driver_name': ride[10] or 'Neznámý řidič',
                            'driver_rating': ride[11] or 5.0
                        }
                    })
            
            # Seřazení podle confidence
            results.sort(key=lambda x: x['confidence'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f'Chyba při hledání jízd: {e}')
            return []
    
    def search_users_text(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Textové vyhledávání uživatelů"""
        try:
            conn = sqlite3.connect(self.database_path)
            c = conn.cursor()
            
            # Vyhledávání podle jména, telefonu nebo emailu
            c.execute('''
                SELECT id, name, phone, email, rating 
                FROM users 
                WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                LIMIT ?
            ''', (f'%{query}%', f'%{query}%', f'%{query}%', limit * 2))
            
            users = c.fetchall()
            conn.close()
            
            results = []
            for user in users:
                # Fuzzy matching
                name_match = self.fuzzy_match(query, user[1])  # name
                phone_match = query in (user[2] or '')         # phone
                email_match = query in (user[3] or '')         # email
                
                if name_match or phone_match or email_match:
                    confidence = self.calculate_confidence(query, user[1])
                    
                    results.append({
                        'id': f'user_{user[0]}',
                        'text': user[1],
                        'subtitle': f'⭐ {user[4] or 5.0:.1f} • {user[2]}',
                        'type': 'user',
                        'icon': '👤',
                        'confidence': confidence,
                        'data': {
                            'id': user[0],
                            'name': user[1],
                            'phone': user[2],
                            'email': user[3],
                            'rating': user[4] or 5.0
                        }
                    })
            
            # Seřazení podle confidence
            results.sort(key=lambda x: x['confidence'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            print(f'Chyba při hledání uživatelů: {e}')
            return []
    
    def get_popular_destinations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Získání populárních destinací"""
        try:
            conn = sqlite3.connect(self.database_path)
            c = conn.cursor()
            
            # Nejčastější cílové destinace
            c.execute('''
                SELECT to_location, COUNT(*) as count
                FROM rides 
                GROUP BY to_location 
                ORDER BY count DESC 
                LIMIT ?
            ''', (limit,))
            
            destinations = c.fetchall()
            conn.close()
            
            results = []
            for dest in destinations:
                results.append({
                    'id': f'popular_{dest[0].lower().replace(" ", "_")}',
                    'text': dest[0],
                    'subtitle': f'{dest[1]} jízd',
                    'type': 'popular',
                    'icon': '🔥',
                    'confidence': 1.0
                })
            
            return results
            
        except Exception as e:
            print(f'Chyba při získávání populárních destinací: {e}')
            return []

# Flask API endpointy
def create_search_routes(app: Flask):
    search_api = AdvancedSearchAPI()
    
    @app.route('/api/search/places', methods=['GET'])
    def search_places():
        query = request.args.get('q', '').strip()
        limit = int(request.args.get('limit', 10))
        
        if len(query) < 2:
            return jsonify([])
        
        results = search_api.search_places(query, limit)
        return jsonify(results)
    
    @app.route('/api/rides/search-text', methods=['GET'])
    def search_rides_text():
        query = request.args.get('q', '').strip()
        user_lat = request.args.get('lat', type=float)
        user_lng = request.args.get('lng', type=float)
        limit = int(request.args.get('limit', 10))
        
        if len(query) < 2:
            return jsonify([])
        
        results = search_api.search_rides_text(query, user_lat, user_lng, limit)
        return jsonify(results)
    
    @app.route('/api/users/search-text', methods=['POST'])
    def search_users_text():
        data = request.get_json()
        query = data.get('query', '').strip()
        limit = int(data.get('limit', 10))
        
        if len(query) < 2:
            return jsonify([])
        
        results = search_api.search_users_text(query, limit)
        return jsonify(results)
    
    @app.route('/api/search/popular', methods=['GET'])
    def get_popular_destinations():
        limit = int(request.args.get('limit', 10))
        results = search_api.get_popular_destinations(limit)
        return jsonify(results)
    
    @app.route('/api/search/unified', methods=['GET'])
    def unified_search():
        """Jednotné vyhledávání napříč všemi typy"""
        query = request.args.get('q', '').strip()
        include_places = request.args.get('places', 'true').lower() == 'true'
        include_rides = request.args.get('rides', 'true').lower() == 'true'
        include_users = request.args.get('users', 'true').lower() == 'true'
        limit = int(request.args.get('limit', 10))
        
        if len(query) < 2:
            # Vrátí návrhy
            popular = search_api.get_popular_destinations(3)
            return jsonify(popular)
        
        all_results = []
        
        if include_places:
            places = search_api.search_places(query, limit // 3)
            all_results.extend(places)
        
        if include_rides:
            rides = search_api.search_rides_text(query, limit=limit // 3)
            all_results.extend(rides)
        
        if include_users:
            users = search_api.search_users_text(query, limit // 3)
            all_results.extend(users)
        
        # Seřazení podle typu a confidence
        type_priority = {'history': 0, 'place': 1, 'ride': 2, 'user': 3, 'popular': 4}
        all_results.sort(key=lambda x: (type_priority.get(x['type'], 99), -x['confidence']))
        
        return jsonify(all_results[:limit])

if __name__ == '__main__':
    # Test
    search_api = AdvancedSearchAPI()
    
    # Test vyhledávání míst
    print("=== Test vyhledávání míst ===")
    results = search_api.search_places("pra")
    for result in results:
        print(f"{result['icon']} {result['text']} (confidence: {result['confidence']:.2f})")
    
    print("\n=== Test fuzzy matching ===")
    test_cases = [
        ("prag", "Praha"),
        ("brn", "Brno"),
        ("ostrav", "Ostrava"),
        ("plzen", "Plzeň")
    ]
    
    for query, text in test_cases:
        match = search_api.fuzzy_match(query, text)
        confidence = search_api.calculate_confidence(query, text)
        print(f"'{query}' vs '{text}': match={match}, confidence={confidence:.2f}")