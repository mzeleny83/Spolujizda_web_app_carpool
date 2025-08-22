from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/rides/search')
def search():
    return jsonify([
        {
            'id': 1,
            'from_location': 'Praha',
            'to_location': 'Brno',
            'departure_time': '14:00',
            'price_per_person': 200,
            'available_seats': 3,
            'driver_name': 'Test Driver'
        }
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)