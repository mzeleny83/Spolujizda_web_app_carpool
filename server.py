import socket
import threading
import sys

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    server.bind((HOST, PORT))
    server.listen()
except OSError as e:
    print(f"Chyba při spuštění serveru: {e}. Ujistěte se, že port {PORT} není již používán.")
    sys.exit(1)

clients = []
nicknames = []

print(f"Server spuštěn a naslouchá na {HOST}:{PORT}")

def broadcast(message, _client=None):
    """Odešle zprávu všem připojeným klientům, kromě odesílatele."""
    for client in clients:
        try:
            # Pokud je zpráva od konkrétního klienta, neposílejte ji zpět jemu samotnému
            if client != _client:
                client.send(message)
        except:
            # Pokud dojde k chybě při odesílání, klient se pravděpodobně odpojil
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                nicknames.remove(nickname)
                print(f"{nickname} se odpojil (během broadcastu).")
                broadcast(f"{nickname} opustil chat.".encode('utf-8'))

def handle_client(client):
    """Stará se o komunikaci s jedním klientem."""
    while True:
        try:
            message = client.recv(1024) # Přijme zprávu od klienta
            if not message: # Klient se odpojil (prázdná zpráva)
                raise Exception("Klient se odpojil")
            
            # Zprávy přijaté serverem jsou rovnou broadcastovány ostatním
            broadcast(message, client)
        except:
            # Zpracování odpojení klienta
            if client in clients:
                index = clients.index(client)
                clients.remove(client)
                client.close()
                nickname = nicknames[index]
                nicknames.remove(nickname)
                print(f"{nickname} se odpojil.")
                broadcast(f"{nickname} opustil chat.".encode('utf-8'))
            break

def receive():
    """Přijímá připojení od klientů."""
    while True:
        client, address = server.accept()
        print(f"Připojeno s {str(address)}")

        client.send('NICK'.encode('utf-8'))
        nickname = client.recv(1024).decode('utf-8')
        nicknames.append(nickname)
        clients.append(client)

        print(f"Přezdívka klienta je {nickname}")
        broadcast(f"{nickname} se připojil do chatu!".encode('utf-8'))
        client.send('Připojeno k serveru!'.encode('utf-8'))

        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

print("Server běží...")
receive()
