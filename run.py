
from main_app import app, socketio, init_db, create_search_routes

if __name__ == '__main__':
    print("Inicializace databáze...")
    init_db()
    print("Databáze inicializována")

    create_search_routes(app)
    print("Pokročilé vyhledávání aktivováno")

    print("Server se spouští na:")
    print("  Lokální: http://localhost:8080")
    print("  Veřejná: http://0.0.0.0:8080")
    print("  Stiskni Ctrl+C pro ukonceni")

    import socket
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"  Síťová: http://{local_ip}:8080")
    except:
        pass

    socketio.run(app, debug=True, host='0.0.0.0', port=8080, allow_unsafe_werkzeug=True)