from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    user_agent = request.headers.get('User-Agent', '').lower()
    accept_header = request.headers.get('Accept', '')
    
    if 'application/json' in accept_header or 'dart' in user_agent or 'flutter' in user_agent:
        return jsonify({
            'message': 'Spolujizda API',
            'status': 'running',
            'endpoints': ['/api/users/register', '/api/users/login', '/api/rides/offer', '/api/rides/search']
        })
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spolujízda</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial; margin: 20px; background: #f0f0f0; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            h1 { color: #333; text-align: center; }
            .flex-container { display: flex; gap: 20px; flex-wrap: wrap; }
            .section { flex: 1; min-width: 300px; margin: 10px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .map-section { flex: 2; min-width: 400px; }
            input, textarea { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ccc; border-radius: 3px; box-sizing: border-box; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }
            .ride { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 Spolujízda - Sdílení jízd</h1>
            
            <div class="flex-container">
                <div class="section" id="loginSection">
                    <h3>👤 Přihlášení</h3>
                    <input type="tel" id="loginPhone" placeholder="Telefon (721745084)" value="721745084">
                    <input type="password" id="loginPassword" placeholder="Heslo (123)" value="123">
                    <button onclick="loginUser()">Přihlásit se</button>
                    <button onclick="registerUser()" style="background: #6c757d; margin-left: 10px;">Registrovat se</button>
                    <div id="loginResult" style="margin-top: 10px; font-weight: bold;"></div>
                </div>
                
                <div class="section" id="userSection" style="display: none;">
                    <h3>👤 Můj profil</h3>
                    <div id="userInfo"></div>
                    <div style="margin: 10px 0;">
                        <button onclick="showMyRides()" style="background: #007bff; margin: 5px;">Moje jízdy</button>
                        <button onclick="showMyReservations()" style="background: #28a745; margin: 5px;">Moje rezervace</button>
                        <button onclick="showAllRides()" style="background: #17a2b8; margin: 5px;">Všechny jízdy</button>
                        <button onclick="logoutUser()" style="background: #dc3545; margin: 5px;">Odhlásit se</button>
                    </div>
                    
                    <div id="myRidesSection" style="display: none;">
                        <h4>🚗 Moje nabízené jízdy</h4>
                        <div id="myOffers"></div>
                    </div>
                    
                    <div id="myReservationsSection" style="display: none;">
                        <h4>🎫 Moje rezervace</h4>
                        <div id="myBookings"></div>
                    </div>
                    
                    <div id="allRidesSection" style="display: none;">
                        <h4>🗺️ Všechny dostupné jízdy</h4>
                        <div id="allRidesList"></div>
                    </div>
                </div>
                
                <div class="section map-section">
                    <h3>🗺️ Mapa České republiky</h3>
                    <div id="map" style="height: 400px; border-radius: 8px; overflow: hidden; border: 2px solid #ddd; position: relative;">
                        <iframe 
                            src="https://www.openstreetmap.org/export/embed.html?bbox=12.0%2C48.5%2C18.9%2C51.1&layer=mapnik&marker=50.0755%2C14.4378" 
                            style="width: 100%; height: 100%; border: none;"
                            title="Mapa České republiky s jízdami">
                        </iframe>
                        
                        <div style="position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.8); color: white; padding: 5px; border-radius: 3px; font-size: 11px;">
                            🗺️ Česká republika - Mapa jízd
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="flex-container">
                <div class="section">
                    <h3>🔍 Hledat jízdu</h3>
                    <input type="text" id="searchFrom" placeholder="Odkud (např. Praha)">
                    <input type="text" id="searchTo" placeholder="Kam (např. Brno)">
                    <button onclick="searchRides()">Hledat jízdy</button>
                    <div id="searchResults" style="margin-top: 15px;"></div>
                </div>
                
                <div class="section">
                    <h3>🚗 Nabídnout jízdu</h3>
                    <input type="text" id="offerFrom" placeholder="Odkud (např. Praha)">
                    <input type="text" id="offerTo" placeholder="Kam (např. Brno)">
                    <input type="datetime-local" id="offerDateTime">
                    <input type="number" id="offerSeats" placeholder="Počet volných míst" min="1" max="8" value="3">
                    <input type="number" id="offerPrice" placeholder="Cena za osobu (Kč)" min="0" value="200">
                    <textarea id="offerNote" placeholder="Poznámka (volitelné)"></textarea>
                    <button onclick="offerRide()">Nabídnout jízdu</button>
                    <div id="offerResult" style="margin-top: 10px; font-weight: bold;"></div>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px;">
                <h3 style="color: #333; margin-bottom: 15px;">📱 Mobilní aplikace</h3>
                <p style="color: #666; margin-bottom: 15px;">Pro plnou funkcionalitu si stáhněte mobilní aplikaci</p>
                <a href="/download/android" style="display: inline-block; background: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 25px; margin: 5px; font-weight: bold;">📱 Stáhnout pro Android</a>
                <p style="font-size: 12px; color: #999; margin-top: 10px;">Velikost: ~15 MB | Verze: 1.0.2</p>
            </div>
        </div>
        
        <script>
            let currentUserId = null;
            
            function loginUser() {
                const phone = document.getElementById('loginPhone').value;
                const password = document.getElementById('loginPassword').value;
                const resultDiv = document.getElementById('loginResult');
                
                resultDiv.innerHTML = '<span style="color: blue;">Přihlašuji...</span>';
                
                fetch('/api/users/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone: phone, password: password })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.user_id) {
                        currentUserId = data.user_id;
                        document.getElementById('loginSection').style.display = 'none';
                        document.getElementById('userSection').style.display = 'block';
                        document.getElementById('userInfo').innerHTML = 
                            '<strong>' + data.name + '</strong><br>' +
                            'Hodnocení: ' + data.rating + '/5 ⭐<br>' +
                            'Telefon: ' + phone;
                        
                        const tomorrow = new Date();
                        tomorrow.setDate(tomorrow.getDate() + 1);
                        document.getElementById('offerDateTime').value = tomorrow.toISOString().slice(0, 16);
                    } else {
                        resultDiv.innerHTML = '<span style="color: red;">✗ ' + (data.error || 'Chyba přihlášení') + '</span>';
                    }
                })
                .catch(error => {
                    resultDiv.innerHTML = '<span style="color: red;">✗ Chyba připojení</span>';
                });
            }
            
            function logoutUser() {
                currentUserId = null;
                document.getElementById('loginSection').style.display = 'block';
                document.getElementById('userSection').style.display = 'none';
                hideAllSections();
            }
            
            function hideAllSections() {
                document.getElementById('myRidesSection').style.display = 'none';
                document.getElementById('myReservationsSection').style.display = 'none';
                document.getElementById('allRidesSection').style.display = 'none';
            }
            
            function registerUser() {
                alert('Registrace bude brzy k dispozici!');
            }
            
            function offerRide() {
                if (!currentUserId) {
                    alert('Nejdříve se přihlaste!');
                    return;
                }
                
                const from = document.getElementById('offerFrom').value;
                const to = document.getElementById('offerTo').value;
                const dateTime = document.getElementById('offerDateTime').value;
                const seats = document.getElementById('offerSeats').value;
                const price = document.getElementById('offerPrice').value;
                const note = document.getElementById('offerNote').value;
                const resultDiv = document.getElementById('offerResult');
                
                if (!from || !to || !dateTime || !seats || !price) {
                    resultDiv.innerHTML = '<span style="color: red;">✗ Vyplněte všechna povinná pole</span>';
                    return;
                }
                
                fetch('/api/rides/offer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        driver_id: currentUserId,
                        from_location: from,
                        to_location: to,
                        departure_time: dateTime,
                        available_seats: parseInt(seats),
                        price: parseInt(price),
                        description: note || 'Jízda nabídnuta přes web'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.ride_id) {
                        resultDiv.innerHTML = '<span style="color: green;">✓ Jízda byla úspěšně nabídnuta!</span>';
                        document.getElementById('offerFrom').value = '';
                        document.getElementById('offerTo').value = '';
                        document.getElementById('offerNote').value = '';
                    } else {
                        resultDiv.innerHTML = '<span style="color: red;">✗ ' + (data.error || 'Chyba při nabídce jízdy') + '</span>';
                    }
                })
                .catch(error => {
                    resultDiv.innerHTML = '<span style="color: red;">✗ Chyba připojení</span>';
                });
            }
            
            function searchRides() {
                const from = document.getElementById('searchFrom').value;
                const to = document.getElementById('searchTo').value;
                const resultsDiv = document.getElementById('searchResults');
                
                let url = '/api/rides/search';
                const params = new URLSearchParams();
                if (from) params.append('from', from);
                if (to) params.append('to', to);
                if (params.toString()) url += '?' + params.toString();
                
                fetch(url)
                .then(response => response.json())
                .then(rides => {
                    displayRides(rides, resultsDiv, true);
                })
                .catch(error => {
                    resultsDiv.innerHTML = '<p style="color: red;">Chyba při hledání jízd</p>';
                });
            }
            
            function showMyRides() {
                if (!currentUserId) return;
                hideAllSections();
                document.getElementById('myRidesSection').style.display = 'block';
                
                fetch('/api/rides/my?user_id=' + currentUserId)
                .then(response => response.json())
                .then(rides => {
                    displayRides(rides, document.getElementById('myOffers'), false);
                })
                .catch(error => {
                    document.getElementById('myOffers').innerHTML = '<p style="color: red;">Chyba při načítání jízd</p>';
                });
            }
            
            function showMyReservations() {
                if (!currentUserId) return;
                hideAllSections();
                document.getElementById('myReservationsSection').style.display = 'block';
                
                fetch('/api/reservations?user_id=' + currentUserId)
                .then(response => response.json())
                .then(reservations => {
                    displayReservations(reservations, document.getElementById('myBookings'));
                })
                .catch(error => {
                    document.getElementById('myBookings').innerHTML = '<p style="color: red;">Chyba při načítání rezervací</p>';
                });
            }
            
            function showAllRides() {
                hideAllSections();
                document.getElementById('allRidesSection').style.display = 'block';
                
                fetch('/api/rides/search')
                .then(response => response.json())
                .then(rides => {
                    displayRides(rides, document.getElementById('allRidesList'), true);
                })
                .catch(error => {
                    document.getElementById('allRidesList').innerHTML = '<p style="color: red;">Chyba při načítání jízd</p>';
                });
            }
            
            function displayRides(rides, container, showReserveButton) {
                if (rides.length === 0) {
                    container.innerHTML = '<p>Žádné jízdy nenalezeny.</p>';
                    return;
                }
                
                let html = '';
                rides.forEach(ride => {
                    const isMyRide = currentUserId && ride.driver_id == currentUserId;
                    html += '<div class="ride">';
                    html += '<strong>' + ride.from_location + ' → ' + ride.to_location + '</strong><br>';
                    html += 'Řidič: ' + ride.driver_name + ' | Čas: ' + ride.departure_time + '<br>';
                    html += 'Cena: ' + ride.price_per_person + ' Kč | Volná místa: ' + ride.available_seats + '<br>';
                    if (ride.description) html += 'Poznámka: ' + ride.description + '<br>';
                    
                    if (showReserveButton && !isMyRide && currentUserId) {
                        html += '<button onclick="reserveRide(' + ride.id + ')" style="background: #28a745; color: white; font-size: 12px; padding: 5px 10px; margin: 5px 5px 0 0;">Rezervovat</button>';
                        html += '<button onclick="openChat(' + "'" + ride.driver_name + "'" + ', ' + "'" + (ride.driver_phone || '+420721745084') + "'" + ')" style="background: #007bff; color: white; font-size: 12px; padding: 5px 10px; margin: 5px 0 0 0;">Chat</button>';
                    } else if (isMyRide) {
                        html += '<span style="color: #28a745; font-weight: bold;">🚗 Vaše jízda</span>';
                    }
                    
                    html += '</div>';
                });
                container.innerHTML = html;
            }
            
            function displayReservations(reservations, container) {
                if (reservations.length === 0) {
                    container.innerHTML = '<p>Nemáte žádné rezervace.</p>';
                    return;
                }
                
                let html = '';
                reservations.forEach(reservation => {
                    html += '<div class="ride">';
                    html += '<strong>' + reservation.from_location + ' → ' + reservation.to_location + '</strong><br>';
                    html += 'Řidič: ' + reservation.driver_name + ' | Čas: ' + reservation.departure_time + '<br>';
                    html += 'Cena: ' + reservation.price_per_person + ' Kč | Rezervovaná místa: ' + reservation.seats_reserved + '<br>';
                    html += '<button onclick="openChat(' + "'" + reservation.driver_name + "'" + ', ' + "'" + (reservation.driver_phone || '+420721745084') + "'" + ')" style="background: #007bff; color: white; font-size: 12px; padding: 5px 10px; margin: 5px 0 0 0;">Kontaktovat řidiče</button>';
                    html += '</div>';
                });
                container.innerHTML = html;
            }
            
            function reserveRide(rideId) {
                if (!currentUserId) {
                    alert('Nejdříve se přihlaste!');
                    return;
                }
                
                fetch('/api/rides/reserve', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ride_id: rideId,
                        passenger_id: currentUserId,
                        seats_reserved: 1
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.reservation_id) {
                        alert('✓ Jízda byla úspěšně zarezervována!');
                        showAllRides();
                    } else {
                        alert('✗ ' + (data.error || 'Chyba při rezervaci'));
                    }
                })
                .catch(error => {
                    alert('✗ Chyba připojení');
                });
            }
            
            function openChat(driverName, driverPhone) {
                alert('Chat s ' + driverName + ' - Telefon: ' + driverPhone);
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/users/login', methods=['POST'])
def login():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'error': 'Neplatná data'}), 400
            
        phone = data.get('phone')
        password = data.get('password')
        
        if not phone or not password:
            return jsonify({'error': 'Telefon a heslo jsou povinné'}), 400
        
        if phone in ['+420721745084', '721745084', '+420123456789', '123456789', 'miroslav.zeleny@volny.cz'] and password in ['123', 'password', 'admin', 'heslo']:
            return jsonify({
                'message': 'Přihlášení úspěšné',
                'user_id': 1,
                'name': 'Miroslav Zelený',
                'rating': 5.0
            }), 200
        else:
            return jsonify({'error': 'Neplatné přihlašovací údaje'}), 401
    except Exception as e:
        return jsonify({'error': f'Chyba serveru: {str(e)}'}), 500

# Globální seznamy pro ukládání dat s testovacími daty
user_rides = [
    {
        'id': 100,
        'driver_id': 1,
        'from_location': 'Brno',
        'to_location': 'Zlín',
        'departure_time': '2025-11-19 14:00',
        'available_seats': 3,
        'price_per_person': 150,
        'description': 'Testovací jízda z aplikace',
        'driver_name': 'Miroslav Zelený',
        'driver_rating': 5.0
    },
    {
        'id': 101,
        'driver_id': 1,
        'from_location': 'Praha',
        'to_location': 'Ostrava',
        'departure_time': '2025-11-20 08:00',
        'available_seats': 2,
        'price_per_person': 300,
        'description': 'Rychlá jízda na východ',
        'driver_name': 'Miroslav Zelený',
        'driver_rating': 5.0
    }
]
reservations = []

@app.route('/api/rides/offer', methods=['POST'])
def offer_ride():
    try:
        data = request.get_json()
        
        new_ride = {
            'id': len(user_rides) + 100,
            'driver_id': data.get('driver_id', 1),
            'from_location': data.get('from_location', ''),
            'to_location': data.get('to_location', ''),
            'departure_time': data.get('departure_time', ''),
            'available_seats': data.get('available_seats', 1),
            'price_per_person': data.get('price', 0),
            'description': data.get('description', 'Jízda nabídnuta přes aplikaci'),
            'driver_name': 'Miroslav Zelený',
            'driver_rating': 5.0
        }
        
        user_rides.append(new_ride)
        
        return jsonify({'message': 'Jízda nabídnuta', 'ride_id': new_ride['id']}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Mock data pro jízdy s různými telefonními čísly
mock_rides = [
    {
        'id': 90,
        'driver_id': 1,
        'from_location': 'Brno',
        'to_location': 'Zlín',
        'departure_time': '2025-11-19 14:00',
        'available_seats': 3,
        'price_per_person': 150,
        'description': 'Pohodová jízda do Zlína',
        'driver_name': 'Miroslav Zelený',
        'driver_phone': '+420721745084',
        'driver_rating': 5.0
    },
    {
        'id': 1,
        'driver_id': 10,
        'from_location': 'Praha',
        'to_location': 'Brno',
        'departure_time': '2025-11-18 15:00',
        'available_seats': 3,
        'price_per_person': 200,
        'description': 'Pohodová jízda',
        'driver_name': 'Jan Novák',
        'driver_phone': '+420602123456',
        'driver_rating': 4.8
    },
    {
        'id': 2,
        'driver_id': 11,
        'from_location': 'Brno',
        'to_location': 'Praha',
        'departure_time': '2025-11-18 17:30',
        'available_seats': 2,
        'price_per_person': 250,
        'description': 'Rychlá jízda',
        'driver_name': 'Marie Svobodová',
        'driver_phone': '+420603234567',
        'driver_rating': 4.9
    },
    {
        'id': 3,
        'driver_id': 12,
        'from_location': 'Brno',
        'to_location': 'Ostrava',
        'departure_time': '2025-11-18 16:00',
        'available_seats': 4,
        'price_per_person': 180,
        'description': 'Společná cesta',
        'driver_name': 'Tomáš Novotný',
        'driver_phone': '+420604345678',
        'driver_rating': 4.7
    },
    {
        'id': 4,
        'driver_id': 13,
        'from_location': 'Ostrava',
        'to_location': 'Praha',
        'departure_time': '2025-11-18 14:00',
        'available_seats': 1,
        'price_per_person': 300,
        'description': 'Komfortní auto',
        'driver_name': 'Petr Dvořák',
        'driver_phone': '+420605456789',
        'driver_rating': 5.0
    },
    {
        'id': 5,
        'driver_id': 14,
        'from_location': 'Praha',
        'to_location': 'Plzeň',
        'departure_time': '2025-11-18 18:00',
        'available_seats': 2,
        'price_per_person': 150,
        'description': 'Večerní jízda',
        'driver_name': 'Anna Krásná',
        'driver_phone': '+420606567890',
        'driver_rating': 4.6
    },
    {
        'id': 6,
        'driver_id': 15,
        'from_location': 'Plzeň',
        'to_location': 'Praha',
        'departure_time': '2025-11-19 08:00',
        'available_seats': 3,
        'price_per_person': 140,
        'description': 'Ranní pendlování',
        'driver_name': 'Lukáš Černý',
        'driver_phone': '+420607678901',
        'driver_rating': 4.8
    },
    {
        'id': 7,
        'driver_id': 16,
        'from_location': 'České Budějovice',
        'to_location': 'Praha',
        'departure_time': '2025-11-18 19:00',
        'available_seats': 2,
        'price_per_person': 220,
        'description': 'Přímá cesta',
        'driver_name': 'Michaela Nová',
        'driver_phone': '+420608789012',
        'driver_rating': 4.9
    },
    {
        'id': 8,
        'driver_id': 17,
        'from_location': 'Praha',
        'to_location': 'Liberec',
        'departure_time': '2025-11-18 16:30',
        'available_seats': 1,
        'price_per_person': 180,
        'description': 'Rychlá jízda',
        'driver_name': 'David Svoboda',
        'driver_phone': '+420609890123',
        'driver_rating': 4.7
    }
]

@app.route('/api/rides/search', methods=['GET'])
def search_rides():
    all_rides = mock_rides + user_rides
    
    from_location = request.args.get('from', '')
    to_location = request.args.get('to', '')
    
    if from_location or to_location:
        result = []
        for ride in all_rides:
            from_match = not from_location or from_location.lower() in ride['from_location'].lower()
            to_match = not to_location or to_location.lower() in ride['to_location'].lower()
            
            if from_match and to_match:
                result.append(ride)
    else:
        result = all_rides
    
    return jsonify(result), 200

@app.route('/api/rides/reserve', methods=['POST'])
def reserve_ride():
    try:
        data = request.get_json(force=True)
        ride_id = data.get('ride_id')
        
        all_rides = mock_rides + user_rides
        ride_info = next((r for r in all_rides if r['id'] == ride_id), None)
        
        new_reservation = {
            'id': len(reservations) + 1,
            'ride_id': ride_id,
            'passenger_id': data.get('passenger_id', 1),
            'passenger_name': 'Miroslav Zelený',
            'seats_reserved': data.get('seats_reserved', 1),
            'status': 'confirmed',
            'created_at': '2025-11-18 12:00:00',
            'from_location': ride_info['from_location'] if ride_info else 'Neznámé',
            'to_location': ride_info['to_location'] if ride_info else 'Neznámé',
            'departure_time': ride_info['departure_time'] if ride_info else 'Neznámý',
            'driver_name': ride_info['driver_name'] if ride_info else 'Neznámý řidič',
            'driver_phone': ride_info.get('driver_phone', '+420721745084') if ride_info else '+420721745084',
            'price_per_person': ride_info['price_per_person'] if ride_info else 0
        }
        
        reservations.append(new_reservation)
        
        return jsonify({
            'message': 'Jízda byla úspěšně zarezervována!',
            'reservation_id': new_reservation['id']
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reservations', methods=['GET'])
def get_reservations():
    try:
        user_id = request.args.get('user_id', 1)
        user_reservations = [r for r in reservations if r['passenger_id'] == int(user_id)]
        return jsonify(user_reservations), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/my', methods=['GET'])
def get_my_rides():
    try:
        user_id = request.args.get('user_id', 1)
        all_rides = mock_rides + user_rides
        my_rides = [r for r in all_rides if r['driver_id'] == int(user_id)]
        return jsonify(my_rides), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/android')
def download_android():
    try:
        return send_from_directory('static', 'spolujizda.apk', as_attachment=True, download_name='Spolujizda.apk')
    except Exception as e:
        return jsonify({'error': 'Soubor nenalezen'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)