import threading
import tkinter as tk
import socket

# Kích thước bảng caro
BOARD_SIZE = 15
both_connected = False
both_connected_lock = threading.Lock()  # Khóa để đồng bộ truy cập vào both_connected
current_border_id = None        #ID của khung đánh dấu nước đi

def create_board(size):
    return [[' ' for _ in range(size)] for _ in range(size)]

def check_win(board, row, col, symbol):
    # Kiểm tra hàng
    count = 0
    for c in range(col - 4, col + 5):
        if 0 <= c < BOARD_SIZE and board[row][c] == symbol:
            count += 1
            if count == 5:
                return True
        else:
            count = 0

    # Kiểm tra cột
    count = 0
    for r in range(row - 4, row + 5):
        if 0 <= r < BOARD_SIZE and board[r][col] == symbol:
            count += 1
            if count == 5:
                return True
        else:
            count = 0

    # Kiểm tra đường chéo chính
    count = 0
    for i in range(-4, 5):
        r, c = row + i, col + i
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == symbol:
            count += 1
            if count == 5:
                return True
        else:
            count = 0

    # Kiểm tra đường chéo phụ
    count = 0
    for i in range(-4, 5):
        r, c = row + i, col - i
        if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE and board[r][c] == symbol:
            count += 1
            if count == 5:
                return True
        else:
            count = 0

    return False

#Vẽ bàn đấu
def draw_board():
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            canvas.create_rectangle(j*40, i*40, (j+1)*40, (i+1)*40, outline="black")    #Vẽ khung từng ô
    canvas.bind("<Button-1>", lambda event: on_click(event))        #Gán hàm xử lý sự kiện cho ô


#Xử lý sự kiện khi click chuột
def on_click(event):
    global my_turn, game_over, symbol, both_connected, current_border_id
    print(f"both_connected: {both_connected}, my_turn: {my_turn}, game_over: {game_over}")
    with both_connected_lock:
        if not both_connected:  # Kiểm tra nếu cả hai người chơi chưa kết nối
            label.config(text="Waiting for opponent to connect...")
            return
    #Nếu chưa tới lượt của người chơi thì không thực hiện gì cả
    if not my_turn or game_over:
        return
    #Lấy tọa độ điểm được đánh
    col = event.x // 40
    row = event.y // 40
    #Kiểm tra xem tọa độ đã được đánh chưa
    if board[row][col] == ' ':
        #Xóa khung đánh dấu điểm được đánh trước đó
        if current_border_id:           
            canvas.delete(current_border_id)
        draw_move(row, col, symbol, "blue")             #Gọi hàm draw_move để vẽ ký hiệu X, O lên khung
        current_border_id = draw_border(row, col)       #Lấy id khung đánh dấu lượt đánh
        board[row][col] = symbol
        #Gọi hàm check_win để kiểm tra xem có người chơi nào thắng không
        if check_win(board, row, col, symbol):
            label.config(text=f"Player {symbol} wins!")
            send_data(f"WIN{symbol}{row:02}{col:02}")       #Gửi dữ liệu người thắng cho server
            game_over = True                
            reset_button.pack()  #Hiện nút cho phép chơi lại
        #Nếu chưa có người chơi thắng thì lưu trạng thái đã đến lượt người chơi khác và yêu cầu đợi người chơi khác đánh 
        else:
            send_data(f"MOVE{row:02}{col:02}")      #Gửi tín hiệu Move và vị trí được đánh đến server
            my_turn = False
            label.config(text="Waiting for opponent...")

#Vẽ ký hiệu X, O lên khung
def draw_move(row, col, symbol, color):
    x = col * 40 + 20           #Lấy tọa độ X
    y = row * 40 + 20           #Lấy tọa độ Y
    return canvas.create_text(x, y, text=symbol, font=('Helvetica', 20, 'bold'), fill=color),   #Vẽ

#Vẽ khung đánh dấu vị trí vừa được đánh
def draw_border(row, col):
    #Tính tọa độ
    x1 = col * 40       
    y1 = row * 40
    x2 = (col + 1) * 40
    y2 = (row + 1) * 40
    return canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=2)      #Vẽ

#Gửi message
def send_data(data):
    try:
        client_socket.send(bytes(data, 'utf-8'))
        print(f"[SENT] {data}")
    except ConnectionResetError:
        print("[ERROR] Connection reset error")
        pass

#Lắng nghe sự kiện
def receive_data():
    global my_turn, game_over, symbol, opponent_symbol, both_connected, current_border_id
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')     #Nhận dữ liệu từ server
            if data.startswith("SYMBOL"):
                symbol = data[6]        #Gán symbol bằng ký tự thứ 7 của chuỗi (X hoặc O)
                if symbol == "O":
                    both_connected = True
                    chat_entry.config(state=tk.NORMAL)  #Mở khóa khung chat
                opponent_symbol = 'O' if symbol == 'X' else 'X'
                my_turn = (symbol == 'X') 
                label.config(text="Your turn" if my_turn else "Waiting for opponent...")
            elif data.startswith("MOVE"):
                row = int(data[4:6])        #Lấy tọa độ hàng
                col = int(data[6:8])        #Lấy tọa độ cột
                board[row][col] = opponent_symbol       #Lưu dự liệu X, O vào mảng
                draw_move(row, col, opponent_symbol, "red")     #Vẽ ký hiệu lên khung
                #Xóa đánh dấu vị trí đánh trước đó nếu tồn tại
                if current_border_id:
                    canvas.delete(current_border_id)
                current_border_id = draw_border(row, col)   #Đánh dấu vị trí mới
                #Nếu có người thắng thì thông báo thông tin. Lưu tín hiệu game over
                if check_win(board, row, col, opponent_symbol):
                    label.config(text=f"Player {opponent_symbol} wins!")
                    game_over = True
                    reset_button.pack()  # Hiển thị nút chơi lại
                else:
                    my_turn = True
                    label.config(text="Your turn")
            elif data.startswith("WIN"):   
                row = int(data[4:6])        #Lấy tọa độ hàng
                col = int(data[6:8])        #Lấy tọa độ cột
                draw_move(row, col, opponent_symbol, "red")
                label.config(text=f"Player {data[3]} wins!")
                game_over = True
                reset_button.pack()  # Show reset button
            elif data.startswith("RESET"):
                reset_game()
            elif data.startswith("CHAT"):
                chat_message = data[4:]
                chat_listbox.insert(tk.END, f"Opponent: {chat_message}")
            elif data.startswith("START"):
                with both_connected_lock:
                    both_connected = True  # Cập nhật trạng thái khi cả hai người chơi đã kết nối
                chat_entry.config(state=tk.NORMAL)  # Bật chức năng chat
                label.config(text="Both players connected. You can start chatting!")
        except ConnectionResetError:
            print("[ERROR] Connection reset error")
            break

def reset_game():
    global board, my_turn, game_over, current_border_id
    board = create_board(BOARD_SIZE)
    canvas.delete("all")
    draw_board()
    game_over = False
    my_turn = (symbol == 'X')
    label.config(text="Your turn" if my_turn else "Waiting for opponent...")
    reset_button.pack_forget()  # Hide reset button
    current_border_id = None

def on_reset_click():
    send_data("RESET")

def send_chat_message(event=None):
    message = chat_entry.get()
    chat_listbox.insert(tk.END, f"You: {message}")
    chat_entry.delete(0, tk.END)
    send_data(f"CHAT{message}")

root = tk.Tk()
root.title("Caro Online")

board = create_board(BOARD_SIZE)
my_turn = False
game_over = False
symbol = ''
opponent_symbol = ''

canvas = tk.Canvas(root, width=BOARD_SIZE*40, height=BOARD_SIZE*40)
canvas.pack(side=tk.RIGHT)

draw_board()

label = tk.Label(root, text="Connecting...")
label.pack()

reset_button = tk.Button(root, text="Rematch", command=on_reset_click)

chat_frame = tk.Frame(root)
chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

chat_listbox = tk.Listbox(chat_frame, height=15, width=50)
chat_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

chat_entry = tk.Entry(chat_frame, width=50)
chat_entry.pack(side=tk.BOTTOM, fill=tk.X)
chat_entry.bind("<Return>", send_chat_message)
chat_entry.config(state=tk.DISABLED)

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("127.0.0.1", 12345))  # Nhập địa chỉ IP của server, nếu chạy cùng 1 máy có thể dùng 127.0.0.1
except ConnectionRefusedError:
    label.config(text="Failed to connect to server")
    print("[ERROR] Failed to connect to server")

if client_socket:
    receive_thread = threading.Thread(target=receive_data)
    receive_thread.start()

root.mainloop()
