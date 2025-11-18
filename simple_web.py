from flask import Flask, request, jsonify
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
            .map-placeholder { height: 400px; background: #e9ecef; border: 2px dashed #6c757d; display: flex; align-items: center; justify-content: center; color: #6c757d; font-size: 18px; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 Spolujízda - Sdílení jízd</h1>
            
            <div class="flex-container">
                <div class="section">
                    <h3>👤 Přihlášení</h3>
                    <input type="tel" id="loginPhone" placeholder="Telefon (721745084)">
                    <input type="password" id="loginPassword" placeholder="Heslo (heslo123)">
                    <button onclick="loginUser()">Přihlásit se</button>
                    <button onclick="registerUser()" style="background: #6c757d; margin-left: 10px;">Registrovat se</button>
                    <div id="loginResult" style="margin-top: 10px; font-weight: bold;"></div>
                </div>
                
                <div class="section map-section">
                    <h3>🗺️ Mapa jízd</h3>
                    <div style="position: relative; height: 400px; background: linear-gradient(45deg, #e3f2fd 0%, #bbdefb 50%, #90caf9 100%); border-radius: 8px; overflow: hidden;">
                        <!-- Města na mapě -->
                        <div style="position: absolute; top: 60px; left: 100px; background: #f44336; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold;">Praha</div>
                        <div style="position: absolute; bottom: 100px; left: 150px; background: #2196f3; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold;">Brno</div>
                        <div style="position: absolute; top: 80px; right: 80px; background: #4caf50; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold;">Ostrava</div>
                        <div style="position: absolute; top: 120px; left: 50px; background: #ff9800; color: white; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold;">Plzeň</div>
                        
                        <!-- Trasy -->
                        <svg style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none;">
                            <line x1="110" y1="70" x2="160" y2="300" stroke="#1976d2" stroke-width="3" stroke-dasharray="5,5"/>
                            <line x1="160" y1="300" x2="320" y2="90" stroke="#388e3c" stroke-width="3" stroke-dasharray="5,5"/>
                            <line x1="110" y1="70" x2="60" y2="130" stroke="#f57c00" stroke-width="3" stroke-dasharray="5,5"/>
                        </svg>
                        
                        <!-- Auta na trase -->
                        <div style="position: absolute; top: 180px; left: 130px; font-size: 20px;">🚗</div>
                        <div style="position: absolute; top: 200px; right: 200px; font-size: 20px;">🚙</div>
                        <div style="position: absolute; bottom: 200px; left: 80px; font-size: 20px;">🚕</div>
                        
                        <div style="position: absolute; bottom: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 5px; border-radius: 3px; font-size: 11px;">
                            🗺️ Interaktivní mapa - 8 aktivních jízd
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="flex-container">
                <div class="section">
                    <h3>📋 Aktuální jízdy</h3>
                    <div class="ride">
                        <strong>Praha → Brno</strong><br>
                        Řidič: Jan Novák | Čas: 2025-11-18 15:00<br>
                        Cena: 200 Kč | Volná místa: 3
                    </div>
                    <div class="ride">
                        <strong>Brno → Praha</strong><br>
                        Řidič: Marie Svobodová | Čas: 2025-11-18 17:30<br>
                        Cena: 250 Kč | Volná místa: 2
                    </div>
                    <div class="ride">
                        <strong>Brno → Ostrava</strong><br>
                        Řidič: Tomáš Novotný | Čas: 2025-11-18 16:00<br>
                        Cena: 180 Kč | Volná místa: 4
                    </div>
                    <div class="ride">
                        <strong>Ostrava → Praha</strong><br>
                        Řidič: Petr Dvořák | Čas: 2025-11-18 14:00<br>
                        Cena: 300 Kč | Volná místa: 1
                    </div>
                    <div class="ride">
                        <strong>Praha → Plzeň</strong><br>
                        Řidič: Anna Krásná | Čas: 2025-11-18 18:00<br>
                        Cena: 150 Kč | Volná místa: 2
                    </div>
                </div>
            </div>
            
            <div class="flex-container">
                <div class="section">
                    <h3>🔍 Hledat jízdu</h3>
                    <input type="text" placeholder="Odkud (např. Praha)">
                    <input type="text" placeholder="Kam (např. Brno)">
                    <button>Hledat jízdy</button>
                </div>
                
                <div class="section">
                    <h3>🚗 Nabídnout jízdu</h3>
                    <input type="text" placeholder="Odkud">
                    <input type="text" placeholder="Kam">
                    <input type="datetime-local">
                    <input type="number" placeholder="Počet volných míst" min="1" max="8">
                    <input type="number" placeholder="Cena za osobu (Kč)" min="0">
                    <textarea placeholder="Poznámka (volitelné)"></textarea>
                    <button>Nabídnout jízdu</button>
                </div>
            </div>
            
            <p style="text-align: center; margin-top: 30px; color: #666;">
                Pro plnou funkcionalit si stáhněte mobilní aplikaci pro Android nebo iOS.
            </p>
        </div>
        
        <script>
            function loginUser() {
                const phone = document.getElementById('loginPhone').value;
                const password = document.getElementById('loginPassword').value;
                const resultDiv = document.getElementById('loginResult');
                
                fetch('/api/users/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ phone: phone, password: password })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.user_id) {
                        resultDiv.innerHTML = '<span style="color: green;">✓ Přihlášen jako ' + data.name + '</span>';
                    } else {
                        resultDiv.innerHTML = '<span style="color: red;">✗ ' + (data.error || 'Chyba přihlášení') + '</span>';
                    }
                })
                .catch(error => {
                    resultDiv.innerHTML = '<span style="color: red;">✗ Chyba připojení</span>';
                });
            }
            
            function registerUser() {
                alert('Registrace bude brzy k dispozici!');
            }
        </script>
    </body>
    </html>
    '''

@app.route('/api/users/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        return jsonify({'message': 'Registrace úspěšná', 'user_id': 999}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        
        # Test účty
        if phone in ['+420721745084', '721745084', '+420123456789', '123456789', 'miroslav.zeleny@volny.cz'] and password in ['heslo123', 'password', 'admin']:
            return jsonify({
                'message': 'Přihlášení úspěšné',
                'user_id': 1,
                'name': 'Miroslav Zelený',
                'rating': 5.0
            }), 200
        else:
            return jsonify({'error': 'Neplatné přihlašovací údaje'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/offer', methods=['POST'])
def offer_ride():
    try:
        data = request.get_json()
        return jsonify({'message': 'Jízda nabídnuta', 'ride_id': 123}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/search', methods=['GET'])
def search_rides():
    mock_rides = [
        {
            'id': 1,
            'driver_id': 1,
            'from_location': 'Praha',
            'to_location': 'Brno',
            'departure_time': '2025-11-18 15:00',
            'available_seats': 3,
            'price_per_person': 200,
            'description': 'Pohodová jízda',
            'driver_name': 'Jan Novák',
            'driver_rating': 4.8
        },
        {
            'id': 2,
            'driver_id': 2,
            'from_location': 'Brno',
            'to_location': 'Praha',
            'departure_time': '2025-11-18 17:30',
            'available_seats': 2,
            'price_per_person': 250,
            'description': 'Rychlá jízda',
            'driver_name': 'Marie Svobodová',
            'driver_rating': 4.9
        },
        {
            'id': 3,
            'driver_id': 3,
            'from_location': 'Brno',
            'to_location': 'Ostrava',
            'departure_time': '2025-11-18 16:00',
            'available_seats': 4,
            'price_per_person': 180,
            'description': 'Společná cesta',
            'driver_name': 'Tomáš Novotný',
            'driver_rating': 4.7
        },
        {
            'id': 4,
            'driver_id': 4,
            'from_location': 'Ostrava',
            'to_location': 'Praha',
            'departure_time': '2025-11-18 14:00',
            'available_seats': 1,
            'price_per_person': 300,
            'description': 'Komfortní auto',
            'driver_name': 'Petr Dvořák',
            'driver_rating': 5.0
        },
        {
            'id': 5,
            'driver_id': 5,
            'from_location': 'Praha',
            'to_location': 'Plzeň',
            'departure_time': '2025-11-18 18:00',
            'available_seats': 2,
            'price_per_person': 150,
            'description': 'Večerní jízda',
            'driver_name': 'Anna Krásná',
            'driver_rating': 4.6
        },
        {
            'id': 6,
            'driver_id': 6,
            'from_location': 'Plzeň',
            'to_location': 'Praha',
            'departure_time': '2025-11-19 08:00',
            'available_seats': 3,
            'price_per_person': 140,
            'description': 'Ranní pendlování',
            'driver_name': 'Lukáš Černý',
            'driver_rating': 4.8
        },
        {
            'id': 7,
            'driver_id': 7,
            'from_location': 'České Budějovice',
            'to_location': 'Praha',
            'departure_time': '2025-11-18 19:00',
            'available_seats': 2,
            'price_per_person': 220,
            'description': 'Přímá cesta',
            'driver_name': 'Michaela Nová',
            'driver_rating': 4.9
        },
        {
            'id': 8,
            'driver_id': 8,
            'from_location': 'Praha',
            'to_location': 'Liberec',
            'departure_time': '2025-11-18 16:30',
            'available_seats': 1,
            'price_per_person': 180,
            'description': 'Rychlá jízda',
            'driver_name': 'David Svoboda',
            'driver_rating': 4.7
        }
    ]
    
    from_location = request.args.get('from', '')
    if from_location:
        result = [ride for ride in mock_rides if from_location.lower() in ride['from_location'].lower()]
    else:
        result = mock_rides
    
    return jsonify(result), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)