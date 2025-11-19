from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import hashlib
import os
import datetime
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    import sqlite3

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    # Detect if request is from mobile app or web browser
    user_agent = request.headers.get('User-Agent', '').lower()
    accept_header = request.headers.get('Accept', '')
    
    # Mobile app sends JSON requests
    if 'application/json' in accept_header or 'dart' in user_agent or 'flutter' in user_agent:
        return jsonify({
            'message': 'Spolujizda API',
            'status': 'running',
            'endpoints': ['/api/users/register', '/api/users/login', '/api/rides/offer', '/api/rides/search']
        })
    
    # Web browser gets simple HTML page
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spolujízda</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial; margin: 20px; background: #f0f0f0; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            h1 { color: #333; text-align: center; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .form-group { margin: 10px 0; }
            input, textarea, select { width: 100%; padding: 8px; margin: 5px 0; border: 1px solid #ccc; border-radius: 3px; }
            button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .ride { background: #f8f9fa; padding: 10px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
            .tabs { display: flex; margin-bottom: 20px; }
            .tab { padding: 10px 20px; background: #e9ecef; margin-right: 5px; cursor: pointer; border-radius: 5px 5px 0 0; }
            .tab.active { background: #007bff; color: white; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚗 Spolujízda - Sdílení jízd</h1>
            
            <div class="tabs">
                <div class="tab active" onclick="showTab('search')">Hledat jízdu</div>
                <div class="tab" onclick="showTab('offer')">Nabídnout jízdu</div>
                <div class="tab" onclick="showTab('login')">Přihlášení</div>
                <div class="tab" onclick="showTab('rides')">Všechny jízdy</div>
            </div>
        
            <!-- Search Tab -->
            <div id="search" class="tab-content active">
                <div class="section">
                    <h3>Hledat jízdu</h3>
                    <div class="form-group">
                        <input type="text" id="searchFrom" placeholder="Odkud (např. Praha)">
                    </div>
                    <div class="form-group">
                        <input type="text" id="searchTo" placeholder="Kam (např. Brno)">
                    </div>
                    <button onclick="searchRides()">Hledat jízdy</button>
                    <div id="search-results"></div>
                </div>
            </div>
        
            <!-- Offer Tab -->
            <div id="offer" class="tab-content">
                <div class="section">
                    <h3>Nabídnout jízdu</h3>
                    <div class="form-group">
                        <input type="text" id="offerFrom" placeholder="Odkud">
                    </div>
                    <div class="form-group">
                        <input type="text" id="offerTo" placeholder="Kam">
                    </div>
                    <div class="form-group">
                        <input type="datetime-local" id="offerTime">
                    </div>
                    <div class="form-group">
                        <input type="number" id="offerSeats" placeholder="Počet volných míst" min="1" max="8">
                    </div>
                    <div class="form-group">
                        <input type="number" id="offerPrice" placeholder="Cena za osobu (Kč)" min="0">
                    </div>
                    <div class="form-group">
                        <textarea id="offerDescription" placeholder="Poznámka (volitelné)"></textarea>
                    </div>
                    <button onclick="offerRide()">Nabídnout jízdu</button>
                </div>
            </div>
        
            <!-- Login Tab -->
            <div id="login" class="tab-content">
                <div class="section">
                    <h3>Přihlášení</h3>
                    <div class="form-group">
                        <input type="tel" id="loginPhone" placeholder="Telefon (+420123456789)">
                    </div>
                    <div class="form-group">
                        <input type="password" id="loginPassword" placeholder="Heslo">
                    </div>
                    <button onclick="loginUser()">Přihlásit se</button>
                    <button onclick="showRegister()" style="background: #6c757d; margin-left: 10px;">Registrovat se</button>
                    
                    <div id="register-form" style="display: none; margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                        <h4>Registrace nového uživatele</h4>
                        <div class="form-group">
                            <input type="text" id="registerName" placeholder="Jméno a příjmení">
                        </div>
                        <div class="form-group">
                            <input type="tel" id="registerPhone" placeholder="Telefon (+420123456789)">
                        </div>
                        <div class="form-group">
                            <input type="password" id="registerPassword" placeholder="Heslo">
                        </div>
                        <button onclick="registerUser()">Registrovat se</button>
                    </div>
                </div>
            </div>
        
            <!-- Rides Tab -->
            <div id="rides" class="tab-content">
                <div class="section">
                    <h3>Všechny dostupné jízdy</h3>
                    <div id="rides-list">Načítám jízdy...</div>
                </div>
            </div>
        </div>
        
        <script>
            let currentUser = null;
            
            function showTab(tabId) {
                // Hide all tabs
                const tabs = document.querySelectorAll('.tab-content');
                tabs.forEach(tab => tab.classList.remove('active'));
                
                const tabButtons = document.querySelectorAll('.tab');
                tabButtons.forEach(btn => btn.classList.remove('active'));
                
                // Show selected tab
                document.getElementById(tabId).classList.add('active');
                event.target.classList.add('active');
            }
            
            function showRegister() {
                const form = document.getElementById('register-form');
                form.style.display = form.style.display === 'none' ? 'block' : 'none';
            }
            
            function searchRides() {
                const from = document.getElementById('searchFrom').value;
                const to = document.getElementById('searchTo').value;
                
                let url = '/api/rides/search';
                if (from) url += '?from=' + encodeURIComponent(from);
                
                fetch(url)
                    .then(response => response.json())
                    .then(rides => {
                        const resultsDiv = document.getElementById('search-results');
                        if (rides.length === 0) {
                            resultsDiv.innerHTML = '<p>Nebyly nalezeny žádné jízdy.</p>';
                            return;
                        }
                        
                        resultsDiv.innerHTML = '<h4>Výsledky hledání:</h4>' + 
                            rides.map(ride => 
                                '<div class="ride">' +
                                '<strong>' + ride.from_location + ' → ' + ride.to_location + '</strong><br>' +
                                'Řidič: ' + ride.driver_name + ' | Čas: ' + ride.departure_time + '<br>' +
                                'Cena: ' + ride.price_per_person + ' Kč | Volná místa: ' + ride.available_seats + '<br>' +
                                '<button onclick="contactDriver(' + ride.id + ')" style="margin-top: 5px;">Kontaktovat řidiče</button>' +
                                '</div>'
                            ).join('');
                    })
                    .catch(() => {
                        document.getElementById('search-results').innerHTML = '<p>Chyba při hledání.</p>';
                    });
            }
            
            function offerRide() {
                if (!currentUser) {
                    alert('Pro nabízení jízdy se musíte přihlásit.');
                    showSection('login');
                    return;
                }
                
                const rideData = {
                    driver_id: currentUser.id,
                    from_location: document.getElementById('offerFrom').value,
                    to_location: document.getElementById('offerTo').value,
                    departure_time: document.getElementById('offerTime').value,
                    available_seats: parseInt(document.getElementById('offerSeats').value),
                    price: parseFloat(document.getElementById('offerPrice').value),
                    description: document.getElementById('offerDescription').value
                };
                
                fetch('/api/rides/offer', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(rideData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.message) {
                        alert('Jízda byla úspěšně nabídnuta!');
                        // Clear form
                        document.getElementById('offerFrom').value = '';
                        document.getElementById('offerTo').value = '';
                        document.getElementById('offerTime').value = '';
                        document.getElementById('offerSeats').value = '';
                        document.getElementById('offerPrice').value = '';
                        document.getElementById('offerDescription').value = '';
                        loadRides(); // Refresh rides list
                    } else {
                        alert('Chyba: ' + (data.error || 'Neznámá chyba'));
                    }
                })
                .catch(() => alert('Chyba při nabízení jízdy.'));
            }
            
            function loginUser() {
                const loginData = {
                    phone: document.getElementById('loginPhone').value,
                    password: document.getElementById('loginPassword').value
                };
                
                fetch('/api/users/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(loginData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.user_id) {
                        currentUser = { id: data.user_id, name: data.name };
                        alert('Přihlášení úspěšné! Vítejte, ' + data.name);
                        updateUI();
                    } else {
                        alert('Chyba: ' + (data.error || 'Neplatné přihlašovací údaje'));
                    }
                })
                .catch(() => alert('Chyba při přihlášení.'));
            }
            
            function registerUser() {
                const registerData = {
                    name: document.getElementById('registerName').value,
                    phone: document.getElementById('registerPhone').value,
                    password: document.getElementById('registerPassword').value
                };
                
                fetch('/api/users/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(registerData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.user_id) {
                        alert('Registrace úspěšná! Můžete se přihlásit.');
                        showSection('login');
                    } else {
                        alert('Chyba: ' + (data.error || 'Registrace se nezdařila'));
                    }
                })
                .catch(() => alert('Chyba při registraci.'));
            }
            
            function contactDriver(rideId) {
                alert('Funkce chatu bude brzy k dispozici! ID jízdy: ' + rideId);
            }
            
            function updateUI() {
                // Update navigation or user info if needed
            }
            
            function loadRides() {
            
            }
            
            // Load rides from API on page load
            loadRides();
            
            function loadRides() {
                fetch('/api/rides/search')
                .then(response => response.json())
                .then(rides => {
                    const ridesList = document.getElementById('rides-list');
                    if (rides.length === 0) {
                        ridesList.innerHTML = '<p>Momentálně nejsou k dispozici žádné jízdy.</p>';
                        return;
                    }
                    
                    ridesList.innerHTML = rides.map(ride => 
                        '<div class="ride">' +
                        '<strong>' + ride.from_location + ' → ' + ride.to_location + '</strong><br>' +
                        'Řidič: ' + ride.driver_name + ' | Čas: ' + ride.departure_time + '<br>' +
                        'Cena: ' + ride.price_per_person + ' Kč | Volná místa: ' + ride.available_seats +
                        '</div>'
                    ).join('');
                })
                .catch(() => {
                    document.getElementById('rides-list').innerHTML = '<p>Chyba při načítání jízd.</p>';
                });
        </script>
    </body>
    </html>
    ''')

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    else:
        import sqlite3
        return sqlite3.connect('simple_app.db')

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id SERIAL PRIMARY KEY, name TEXT, phone TEXT UNIQUE, password_hash TEXT, rating REAL DEFAULT 5.0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS rides
                     (id SERIAL PRIMARY KEY, driver_id INTEGER, from_location TEXT, to_location TEXT, 
                      departure_time TIMESTAMP, available_seats INTEGER, price REAL, description TEXT,
                      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    else:
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY, name TEXT, phone TEXT UNIQUE, password_hash TEXT, rating REAL DEFAULT 5.0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS rides
                     (id INTEGER PRIMARY KEY, driver_id INTEGER, from_location TEXT, to_location TEXT, 
                      departure_time TEXT, available_seats INTEGER, price REAL, description TEXT,
                      created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

@app.route('/api/users/register', methods=['POST'])
def register():
    init_db()  # Ensure DB exists
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        password = data.get('password')
        
        # Simple hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Check if user exists
        c.execute("SELECT id FROM users WHERE phone = %s" if os.environ.get('DATABASE_URL') else "SELECT id FROM users WHERE phone = ?", (phone,))
        if c.fetchone():
            return jsonify({'error': 'Telefon již registrován'}), 409
        
        # Insert user
        if os.environ.get('DATABASE_URL'):
            c.execute("INSERT INTO users (name, phone, password_hash) VALUES (%s, %s, %s) RETURNING id",
                      (name, phone, password_hash))
            user_id = c.fetchone()[0]
        else:
            c.execute("INSERT INTO users (name, phone, password_hash) VALUES (?, ?, ?)",
                      (name, phone, password_hash))
            user_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Registrace úspěšná', 'user_id': user_id}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    init_db()  # Ensure DB exists
    try:
        data = request.get_json()
        phone = data.get('phone')
        password = data.get('password')
        
        # Simple hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        conn = get_db_connection()
        c = conn.cursor()
        if os.environ.get('DATABASE_URL'):
            c.execute("SELECT id, name, rating FROM users WHERE phone = %s AND password_hash = %s",
                      (phone, password_hash))
        else:
            c.execute("SELECT id, name, rating FROM users WHERE phone = ? AND password_hash = ?",
                      (phone, password_hash))
        user = c.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'message': 'Přihlášení úspěšné',
                'user_id': user[0],
                'name': user[1],
                'rating': float(user[2]) if user[2] is not None else 5.0
            }), 200
        else:
            return jsonify({'error': 'Neplatné přihlašovací údaje'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/offer', methods=['POST'])
def offer_ride():
    init_db()
    try:
        data = request.get_json()
        conn = get_db_connection()
        c = conn.cursor()
        
        if os.environ.get('DATABASE_URL'):
            c.execute("INSERT INTO rides (driver_id, from_location, to_location, departure_time, available_seats, price, description) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                      (data.get('driver_id'), data.get('from_location'), data.get('to_location'), 
                       data.get('departure_time'), data.get('available_seats'), data.get('price'), data.get('description', '')))
        else:
            c.execute("INSERT INTO rides (driver_id, from_location, to_location, departure_time, available_seats, price, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (data.get('driver_id'), data.get('from_location'), data.get('to_location'), 
                       data.get('departure_time'), data.get('available_seats'), data.get('price'), data.get('description', '')))
        
        conn.commit()
        conn.close()
        return jsonify({'message': 'Jízda nabídnuta', 'ride_id': c.lastrowid}), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/rides/search', methods=['GET'])
def search_rides():
    try:
        from_location_query = request.args.get('from', '')
        to_location_query = request.args.get('to', '')
        
        conn = get_db_connection()
        c = conn.cursor()
        
        if os.environ.get('DATABASE_URL'):
            c.execute("""
                SELECT 
                    r.id, r.driver_id, r.from_location, r.to_location, 
                    r.departure_time, r.available_seats, r.price, r.description,
                    u.name as driver_name, u.rating as driver_rating
                FROM rides r
                JOIN users u ON r.driver_id = u.id
                WHERE (r.from_location ILIKE %s OR %s = '')
                  AND (r.to_location ILIKE %s OR %s = '')
                ORDER BY r.departure_time ASC
            """, (f'%{from_location_query}%', from_location_query, f'%{to_location_query}%', to_location_query))
            rides = c.fetchall()
            
            # Convert psycopg2.Row objects to dictionaries
            rides_list = []
            for ride in rides:
                rides_list.append({
                    'id': ride[0],
                    'driver_id': ride[1],
                    'from_location': ride[2],
                    'to_location': ride[3],
                    'departure_time': ride[4].isoformat() if isinstance(ride[4], datetime.datetime) else ride[4],
                    'available_seats': ride[5],
                    'price_per_person': ride[6],
                    'description': ride[7],
                    'driver_name': ride[8],
                    'driver_rating': float(ride[9]) if ride[9] is not None else 5.0
                })
        else:
            c.execute("""
                SELECT 
                    r.id, r.driver_id, r.from_location, r.to_location, 
                    r.departure_time, r.available_seats, r.price, r.description,
                    u.name as driver_name, u.rating as driver_rating
                FROM rides r
                JOIN users u ON r.driver_id = u.id
                WHERE (r.from_location LIKE ? OR ? = '')
                  AND (r.to_location LIKE ? OR ? = '')
                ORDER BY r.departure_time ASC
            """, (f'%{from_location_query}%', from_location_query, f'%{to_location_query}%', to_location_query))
            rides = c.fetchall()
            
            rides_list = []
            for ride in rides:
                rides_list.append({
                    'id': ride[0],
                    'driver_id': ride[1],
                    'from_location': ride[2],
                    'to_location': ride[3],
                    'departure_time': ride[4],
                    'available_seats': ride[5],
                    'price_per_person': ride[6],
                    'description': ride[7],
                    'driver_name': ride[8],
                    'driver_rating': float(ride[9]) if ride[9] is not None else 5.0
                })
        
        conn.close()
        return jsonify(rides_list), 200
        
    except Exception as e:
        print(f"Error in search_rides: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)