import socket               #Tạo và quản lý kết nối
import threading            #Hỗ trợ xử lý đa luồng

clients = {}
reset_requests = { 'X': False, 'O': False } #Biến để kiểm tra yêu cầu reset của 2 client

both_connected = False                      #Biến kiểm tra 2 client đã kết nối chưa
both_connected_lock = threading.Lock()      

def handle_client(client_socket, symbol):
    global reset_requests
    #Lắng nghe sự kiện từ client
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')             #Nhận dữ liệu từ client
            print(f"[RECEIVED from {symbol}] {data}")
            if data.startswith("MOVE") or data.startswith("WIN"):       #Kiểm tra dữ liệu gửi từ client có bắt đầu bằng "MOVE" hay "WiN" không
                other_symbol = 'O' if symbol == 'X' else 'X'            
                clients[other_symbol].send(bytes(data, 'utf-8'))        #Gửi data cho client còn lại
            elif data.startswith("RESET"):                              #Kiểm tra xem dữ liệu gửi từ client có bắt đầu bằng "RESET" không
                reset_requests[symbol] = True                           #Lưu trạng thái client đã gửi yêu cầu reset ván đấu
                #Nếu tất cả client đã gửi yêu cầu reset ván đấu thì gửi thông báo RESET đến các client
                if all(reset_requests.values()):                        
                    reset_requests = { 'X': False, 'O': False }
                    for client in clients.values():
                        client.send(bytes("RESET", 'utf-8'))
            elif data.startswith("CHAT"):                               #Kiểm tra xem dữ liệu gửi từ client có bắt đầu bằng "CHAT" không
                other_symbol = 'O' if symbol == 'X' else 'X'
                clients[other_symbol].send(bytes(data, 'utf-8'))        #Gửi thông báo "CHAT" đến client còn lại
        except ConnectionResetError:                                    #Xử lý ngoại lệ
            print(f"[DISCONNECTED] {symbol} disconnected")
            break

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)          #Tạo đối tượng socket sử dụng IPv4 và giao thức TCP
    server.bind(("0.0.0.0", 12345))                                     #Bắt đầu lắng nghe các kết nối trên địa chỉ IP '0.0.0.0', cổng 12345 (Nghe các kết nối từ tất cả địa chỉ IP)
    server.listen(2)                                                    #Đưa máy chủ vào chế độ lắng nghe, với tối đa 2 kết nối
    print("[STARTED] Server is listening...")

    symbol = 'X'                                                        
    while True:
        client_socket, addr = server.accept()
        print(f"[CONNECTED] {addr} connected as {symbol}")
        clients[symbol] = client_socket
        client_socket.send(bytes(f"SYMBOL{symbol}", 'utf-8'))           #Gửi dữ liệu cho client biết về biểu tượng của mình (X hoặc O)

        # Kiểm tra nếu cả hai người chơi đã kết nối
        if 'X' in clients and 'O' in clients:
            with both_connected_lock:
                both_connected = True  # Cập nhật trạng thái khi cả hai người chơi đã kết nối
            for client in clients.values():
                client.send(bytes("START", 'utf-8'))  # Gửi thông báo "START" đến cả hai client
            print("Both players connected, sending START signal")

        thread = threading.Thread(target=handle_client, args=(client_socket, symbol))
        thread.start()

        symbol = 'O' if symbol == 'X' else 'X'                          #Chuyển symbol thành O nếu đang là X và ngược lại

if __name__ == "__main__":
    start_server()
