import socket
import threading

clients = {}
reset_requests = { 'X': False, 'O': False }

both_connected = False
both_connected_lock = threading.Lock()

def handle_client(client_socket, symbol):
    global reset_requests
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            print(f"[RECEIVED from {symbol}] {data}")
            if data.startswith("MOVE") or data.startswith("WIN"):
                # Forward the data to the other client
                other_symbol = 'O' if symbol == 'X' else 'X'
                clients[other_symbol].send(bytes(data, 'utf-8'))
            elif data.startswith("RESET"):
                reset_requests[symbol] = True
                if all(reset_requests.values()):
                    # Reset the game for both players
                    reset_requests = { 'X': False, 'O': False }
                    for client in clients.values():
                        client.send(bytes("RESET", 'utf-8'))
            elif data.startswith("CHAT"):
                other_symbol = 'O' if symbol == 'X' else 'X'
                clients[other_symbol].send(bytes(data, 'utf-8'))
        except ConnectionResetError:
            print(f"[DISCONNECTED] {symbol} disconnected")
            break

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 12345))
    server.listen(2)
    print("[STARTED] Server is listening...")

    symbol = 'X'
    while True:
        client_socket, addr = server.accept()
        print(f"[CONNECTED] {addr} connected as {symbol}")
        clients[symbol] = client_socket
        client_socket.send(bytes(f"SYMBOL{symbol}", 'utf-8'))

        # Kiểm tra nếu cả hai người chơi đã kết nối
        if 'X' in clients and 'O' in clients:
            with both_connected_lock:
                both_connected = True  # Cập nhật trạng thái khi cả hai người chơi đã kết nối
            for client in clients.values():
                client.send(bytes("START", 'utf-8'))  # Gửi thông báo "START" đến cả hai client
            print("Both players connected, sending START signal")

        thread = threading.Thread(target=handle_client, args=(client_socket, symbol))
        thread.start()

        symbol = 'O' if symbol == 'X' else 'X'

if __name__ == "__main__":
    start_server()
