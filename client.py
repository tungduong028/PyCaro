import tkinter as tk
import socket
import threading

# Kích thước bảng caro
BOARD_SIZE = 15

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

def draw_board():
    for i in range(BOARD_SIZE):
        for j in range(BOARD_SIZE):
            canvas.create_rectangle(j*40, i*40, (j+1)*40, (i+1)*40, outline="black")
    canvas.bind("<Button-1>", lambda event: on_click(event))

def on_click(event):
    global my_turn, game_over, symbol
    if not my_turn or game_over:
        return
    col = event.x // 40
    row = event.y // 40
    if board[row][col] == ' ':
        draw_move(row, col, symbol)
        board[row][col] = symbol
        if check_win(board, row, col, symbol):
            label.config(text=f"Player {symbol} wins!")
            send_data(f"WIN{symbol}")
            game_over = True
        else:
            send_data(f"MOVE{row:02}{col:02}")
            my_turn = False
            label.config(text="Waiting for opponent...")

def draw_move(row, col, symbol):
    x = col * 40 + 20
    y = row * 40 + 20
    canvas.create_text(x, y, text=symbol, font=('Helvetica', 20, 'bold'))

def send_data(data):
    try:
        client_socket.send(bytes(data, 'utf-8'))
        print(f"[SENT] {data}")
    except ConnectionResetError:
        print("[ERROR] Connection reset error")
        pass

def receive_data():
    global my_turn, game_over, symbol, opponent_symbol
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            print(f"[RECEIVED] {data}")
            if data.startswith("SYMBOL"):
                symbol = data[6]
                opponent_symbol = 'O' if symbol == 'X' else 'X'
                my_turn = (symbol == 'X')
                label.config(text="Your turn" if my_turn else "Waiting for opponent...")
            elif data.startswith("MOVE"):
                row = int(data[4:6])
                col = int(data[6:8])
                board[row][col] = opponent_symbol
                draw_move(row, col, opponent_symbol)
                if check_win(board, row, col, opponent_symbol):
                    label.config(text=f"Player {opponent_symbol} wins!")
                    game_over = True
                else:
                    my_turn = True
                    label.config(text="Your turn")
            elif data.startswith("WIN"):
                label.config(text=f"Player {data[3]} wins!")
                game_over = True
        except ConnectionResetError:
            print("[ERROR] Connection reset error")
            break

root = tk.Tk()
root.title("Caro Online")

board = create_board(BOARD_SIZE)
my_turn = False
game_over = False
symbol = ''
opponent_symbol = ''

canvas = tk.Canvas(root, width=BOARD_SIZE*40, height=BOARD_SIZE*40)
canvas.pack()

draw_board()

label = tk.Label(root, text="Connecting...")
label.pack()

try:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(("192.168.244.129", 12345))  # Nhập địa chỉ IP của mạng đang dùng, nếu chạy cùng 1 máy có thể dùng 127.0.0.1
except ConnectionRefusedError:
    label.config(text="Failed to connect to server")
    print("[ERROR] Failed to connect to server")

if client_socket:
    receive_thread = threading.Thread(target=receive_data)
    receive_thread.start()

root.mainloop()
