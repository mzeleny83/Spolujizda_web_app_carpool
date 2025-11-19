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
                    <div id="loginResult" style="margin-top: 10px; font-weight: bold;"></div>
                </div>
                
                <div class="section" id="userSection" style="display: none;">
                    <h3>👤 Můj profil</h3>
                    <div id="userInfo"></div>
                    <div style="margin: 10px 0;">
                        <button onclick="showAllRides()" style="background: #17a2b8; margin: 5px;">Všechny jízdy</button>
                        <button onclick="logoutUser()" style="background: #dc3545; margin: 5px;">Odhlásit se</button>
                    </div>
                    
                    <div id="allRidesSection" style="display: none;">
                        <h4>🗺️ Všechny dostupné jízdy</h4>
                        <div id="allRidesList"></div>
                    </div>
                </div>
                
                <div class="section map-section">
                    <h3>🗺️ Mapa České republiky</h3>
                    <div id="map" style="height: 400px; border-radius: 8px; overflow: hidden; border: 2px solid #ddd;">
                        <iframe 
                            src="https://www.openstreetmap.org/export/embed.html?bbox=12.0%2C48.5%2C18.9%2C51.1&layer=mapnik&marker=50.0755%2C14.4378" 
                            style="width: 100%; height: 100%; border: none;"
                            title="Mapa České republiky s jízdami">
                        </iframe>
                    </div>
                </div>
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
                document.getElementById('allRidesSection').style.display = 'none';
            }
            
            function showAllRides() {
                document.getElementById('allRidesSection').style.display = 'block';
                
                fetch('/api/rides/search')
                .then(response => response.json())
                .then(rides => {
                    displayRides(rides, document.getElementById('allRidesList'));
                })
                .catch(error => {
                    document.getElementById('allRidesList').innerHTML = '<p style="color: red;">Chyba při načítání jízd</p>';
                });
            }
            
            function displayRides(rides, container) {
                if (rides.length === 0) {
                    container.innerHTML = '<p>Žádné jízdy nenalezeny.</p>';
                    return;
                }
                
                let html = '';
                rides.forEach(ride => {
                    html += '<div class="ride">';
                    html += '<strong>' + ride.from_location + ' → ' + ride.to_location + '</strong><br>';
                    html += 'Řidič: ' + ride.driver_name + ' | Čas: ' + ride.departure_time + '<br>';
                    html += 'Cena: ' + ride.price_per_person + ' Kč | Volná místa: ' + ride.available_seats + '<br>';
                    if (ride.description) html += 'Poznámka: ' + ride.description + '<br>';
                    html += '</div>';
                });
                container.innerHTML = html;
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
        
        if phone in ['721745084', '+420721745084'] and password in ['123', 'password', 'admin', 'heslo']:
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

mock_rides = [
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
    }
]

@app.route('/api/rides/search', methods=['GET'])
def search_rides():
    return jsonify(mock_rides), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)