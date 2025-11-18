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
    
    # Web browser gets full HTML page
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="cs">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Spolujízda - Sdílení jízd</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
            .header { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 1rem 0; }
            .nav { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; padding: 0 2rem; }
            .logo { color: white; font-size: 1.8rem; font-weight: bold; }
            .nav-links { display: flex; gap: 2rem; }
            .nav-links a { color: white; text-decoration: none; transition: opacity 0.3s; }
            .nav-links a:hover { opacity: 0.8; }
            .hero { text-align: center; padding: 4rem 2rem; color: white; }
            .hero h1 { font-size: 3rem; margin-bottom: 1rem; }
            .hero p { font-size: 1.2rem; margin-bottom: 2rem; opacity: 0.9; }
            .cta-button { background: #ff6b6b; color: white; padding: 1rem 2rem; border: none; border-radius: 50px; font-size: 1.1rem; cursor: pointer; transition: transform 0.3s; }
            .cta-button:hover { transform: translateY(-2px); }
            .features { max-width: 1200px; margin: 0 auto; padding: 4rem 2rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
            .feature { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 2rem; border-radius: 15px; text-align: center; color: white; }
            .feature-icon { font-size: 3rem; margin-bottom: 1rem; }
            .rides-section { background: rgba(255,255,255,0.05); padding: 4rem 2rem; }
            .rides-container { max-width: 800px; margin: 0 auto; }
            .rides-title { text-align: center; color: white; font-size: 2rem; margin-bottom: 2rem; }
            .ride-card { background: rgba(255,255,255,0.1); backdrop-filter: blur(10px); padding: 1.5rem; margin-bottom: 1rem; border-radius: 10px; color: white; }
            .ride-route { font-size: 1.2rem; font-weight: bold; margin-bottom: 0.5rem; }
            .ride-details { opacity: 0.9; }
            .footer { text-align: center; padding: 2rem; color: rgba(255,255,255,0.8); }
        </style>
    </head>
    <body>
        <header class="header">
            <nav class="nav">
                <div class="logo">🚗 Spolujízda</div>
                <div class="nav-links">
                    <a href="#home">Domů</a>
                    <a href="#rides">Jízdy</a>
                    <a href="#about">O nás</a>
                    <a href="#contact">Kontakt</a>
                </div>
            </nav>
        </header>
        
        <section class="hero" id="home">
            <h1>Sdílejte jízdy, šetřete peníze</h1>
            <p>Najděte spolucestující nebo nabídněte volná místa ve svém autě</p>
            <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 2rem;">
                <button class="cta-button" onclick="showSection('search')">Hledat jízdu</button>
                <button class="cta-button" onclick="showSection('offer')">Nabídnout jízdu</button>
                <button class="cta-button" onclick="showSection('login')">Přihlásit se</button>
            </div>
        </section>
        
        <section class="features">
            <div class="feature">
                <div class="feature-icon">📱</div>
                <h3>Mobilní aplikace</h3>
                <p>K dispozici pro Android a iOS</p>
            </div>
            <div class="feature">
                <div class="feature-icon">🗺️</div>
                <h3>GPS navigace</h3>
                <p>Automatické určení polohy a tras</p>
            </div>
            <div class="feature">
                <div class="feature-icon">💬</div>
                <h3>Chat</h3>
                <p>Komunikace mezi řidiči a spolucestujícími</p>
            </div>
        </section>
        
        <!-- Search Section -->
        <section class="rides-section" id="search" style="display: none;">
            <div class="rides-container">
                <h2 class="rides-title">Hledat jízdu</h2>
                <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px; margin-bottom: 2rem;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem;">
                        <input type="text" id="searchFrom" placeholder="Odkud" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <input type="text" id="searchTo" placeholder="Kam" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                    </div>
                    <button onclick="searchRides()" style="width: 100%; padding: 1rem; background: #ff6b6b; color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer;">Hledat</button>
                </div>
                <div id="search-results"></div>
            </div>
        </section>
        
        <!-- Offer Section -->
        <section class="rides-section" id="offer" style="display: none;">
            <div class="rides-container">
                <h2 class="rides-title">Nabídnout jízdu</h2>
                <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px;">
                    <div style="display: grid; gap: 1rem;">
                        <input type="text" id="offerFrom" placeholder="Odkud" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <input type="text" id="offerTo" placeholder="Kam" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <input type="datetime-local" id="offerTime" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <input type="number" id="offerSeats" placeholder="Počet volných míst" min="1" max="8" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <input type="number" id="offerPrice" placeholder="Cena za osobu (Kč)" min="0" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <textarea id="offerDescription" placeholder="Poznámka (volitelné)" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem; min-height: 80px; resize: vertical;"></textarea>
                        <button onclick="offerRide()" style="padding: 1rem; background: #4CAF50; color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer;">Nabídnout jízdu</button>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Login Section -->
        <section class="rides-section" id="login" style="display: none;">
            <div class="rides-container">
                <h2 class="rides-title">Přihlášení</h2>
                <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px; max-width: 400px; margin: 0 auto;">
                    <div style="display: grid; gap: 1rem;">
                        <input type="tel" id="loginPhone" placeholder="Telefon (+420123456789)" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <input type="password" id="loginPassword" placeholder="Heslo" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <button onclick="loginUser()" style="padding: 1rem; background: #2196F3; color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer;">Přihlásit se</button>
                        <button onclick="showSection('register')" style="padding: 1rem; background: transparent; color: white; border: 2px solid white; border-radius: 8px; font-size: 1rem; cursor: pointer;">Registrovat se</button>
                    </div>
                </div>
            </div>
        </section>
        
        <!-- Register Section -->
        <section class="rides-section" id="register" style="display: none;">
            <div class="rides-container">
                <h2 class="rides-title">Registrace</h2>
                <div style="background: rgba(255,255,255,0.1); padding: 2rem; border-radius: 15px; max-width: 400px; margin: 0 auto;">
                    <div style="display: grid; gap: 1rem;">
                        <input type="text" id="registerName" placeholder="Jméno a příjmení" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <input type="tel" id="registerPhone" placeholder="Telefon (+420123456789)" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <input type="password" id="registerPassword" placeholder="Heslo" style="padding: 1rem; border: none; border-radius: 8px; font-size: 1rem;">
                        <button onclick="registerUser()" style="padding: 1rem; background: #4CAF50; color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer;">Registrovat se</button>
                        <button onclick="showSection('login')" style="padding: 1rem; background: transparent; color: white; border: 2px solid white; border-radius: 8px; font-size: 1rem; cursor: pointer;">Zpět na přihlášení</button>
                    </div>
                </div>
            </div>
        </section>
        
        <section class="rides-section" id="rides">
            <div class="rides-container">
                <h2 class="rides-title">Aktuální jízdy</h2>
                <div id="rides-list">Načítám jízdy...</div>
            </div>
        </section>
        
        <footer class="footer">
            <p>&copy; 2025 Spolujízda. Všechna práva vyhrazena.</p>
        </footer>
        
        <script>
            let currentUser = null;
            
            function showSection(sectionId) {
                // Hide all sections
                const sections = ['search', 'offer', 'login', 'register'];
                sections.forEach(id => {
                    const section = document.getElementById(id);
                    if (section) section.style.display = 'none';
                });
                
                // Show selected section
                const targetSection = document.getElementById(sectionId);
                if (targetSection) {
                    targetSection.style.display = 'block';
                    targetSection.scrollIntoView({ behavior: 'smooth' });
                }
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
                            resultsDiv.innerHTML = '<p style="text-align: center; color: white; opacity: 0.7;">Nebyly nalezeny žádné jízdy.</p>';
                            return;
                        }
                        
                        resultsDiv.innerHTML = '<h3 style="color: white; margin-bottom: 1rem;">Výsledky hledání:</h3>' + 
                            rides.map(ride => `
                                <div class="ride-card">
                                    <div class="ride-route">${ride.from_location} → ${ride.to_location}</div>
                                    <div class="ride-details">
                                        Řidič: ${ride.driver_name} | 
                                        Čas: ${ride.departure_time} | 
                                        Cena: ${ride.price_per_person} Kč | 
                                        Volná místa: ${ride.available_seats}
                                    </div>
                                    <button onclick="contactDriver(${ride.id})" style="margin-top: 0.5rem; padding: 0.5rem 1rem; background: #ff6b6b; color: white; border: none; border-radius: 5px; cursor: pointer;">Kontaktovat</button>
                                </div>
                            `).join('');
                    })
                    .catch(() => {
                        document.getElementById('search-results').innerHTML = '<p style="text-align: center; color: white; opacity: 0.7;">Chyba při hledání.</p>';
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
                        ridesList.innerHTML = '<p style="text-align: center; opacity: 0.7;">Momentálně nejsou k dispozici žádné jízdy.</p>';
                        return;
                    }
                    
                    ridesList.innerHTML = rides.map(ride => `
                        <div class="ride-card">
                            <div class="ride-route">${ride.from_location} → ${ride.to_location}</div>
                            <div class="ride-details">
                                Řidič: ${ride.driver_name} | 
                                Čas: ${ride.departure_time} | 
                                Cena: ${ride.price_per_person} Kč | 
                                Volná místa: ${ride.available_seats}
                            </div>
                        </div>
                    `).join('');
                })
                .catch(() => {
                    document.getElementById('rides-list').innerHTML = '<p style="text-align: center; opacity: 0.7;">Chyba při načítání jízd.</p>';
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
        from_location = request.args.get('from', '')
        
        # Mock ride data
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
                'driver_rating': 4.8,
                'route_waypoints': [{'lat': 50.0755, 'lng': 14.4378}, {'lat': 49.1951, 'lng': 16.6068}]
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
                'driver_rating': 4.9,
                'route_waypoints': [{'lat': 49.1951, 'lng': 16.6068}, {'lat': 50.0755, 'lng': 14.4378}]
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
                'driver_rating': 4.7,
                'route_waypoints': [{'lat': 49.1951, 'lng': 16.6068}, {'lat': 49.8209, 'lng': 18.2625}]
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
                'driver_rating': 5.0,
                'route_waypoints': [{'lat': 49.8209, 'lng': 18.2625}, {'lat': 50.0755, 'lng': 14.4378}]
            }
        ]
        
        # Filter by from_location if provided
        if from_location:
            result = [ride for ride in mock_rides if from_location.lower() in ride['from_location'].lower()]
        else:
            result = mock_rides
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)