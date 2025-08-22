from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

@app.route('/api/reservations/user/<int:user_id>')
def get_reservations(user_id):
    return jsonify([])

@app.route('/test')
def test():
    return "Test funguje!"

if __name__ == '__main__':
    app.run(port=8082, debug=True)