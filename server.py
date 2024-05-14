import socket
import threading

clients = []
symbols = ['X', 'O']

def handle_client(client_socket, addr, symbol):
    print(f"[NEW CONNECTION] {addr} connected as {symbol}.")
    client_socket.send(f"SYMBOL{symbol}".encode('utf-8'))
    
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            print(f"[RECEIVED] {data}")
            for client in clients:
                if client != client_socket:
                    client.send(data.encode('utf-8'))
        except ConnectionResetError:
            break

    client_socket.close()
    clients.remove(client_socket)
    print(f"[DISCONNECTED] {addr} disconnected.")

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", 12345))
    server_socket.listen(2)

    print("[STARTING] Server is starting...")
    while True:
        client_socket, addr = server_socket.accept()
        if len(clients) < 2:
            symbol = symbols[len(clients)]
            clients.append(client_socket)
            thread = threading.Thread(target=handle_client, args=(client_socket, addr, symbol))
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {len(clients)}")
        else:
            client_socket.send("SERVER_FULL".encode('utf-8'))
            client_socket.close()

start_server()
