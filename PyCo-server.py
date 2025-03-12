import socket
import threading
import json
import random
import time

# Конфигурация сервера
HOST = '127.0.0.1'
PORT = 65432
BUFFER_SIZE = 1024

# Форма блока
SHAPES = {
    'I': [[1, 1, 1, 1]],
    'J': [[1, 0, 0],
          [1, 1, 1]],
    'L': [[0, 0, 1],
          [1, 1, 1]],
    'O': [[1, 1],
          [1, 1]],
    'S': [[0, 1, 1],
          [1, 1, 0]],
    'T': [[0, 1, 0],
          [1, 1, 1]],
    'Z': [[1, 1, 0],
          [0, 1, 1]]
}

# Состояние игры
grid = [[0 for _ in range(10)] for _ in range(20)]
current_piece = None
next_piece = None
score = [0, 0]  # — это очки игрока 1 и игрока 2 соответственно.
game_over = False
clients = []
player_names = ["Player 1", "Player 2"]
remaining_time = 120  # Первоначальное оставшееся время составляет 120 секунд.

def new_piece():
    global current_piece, next_piece
    if next_piece is None:
        next_piece = random.choice(list(SHAPES.values()))
    current_piece = next_piece
    next_piece = random.choice(list(SHAPES.values()))
    return current_piece

def rotate_piece(piece):
    return [list(row) for row in zip(*piece[::-1])]

def collision(piece, offset):
    off_x, off_y = offset
    for y, row in enumerate(piece):
        for x, cell in enumerate(row):
            try:
                if cell and grid[y + off_y][x + off_x]:
                    return True
            except IndexError:
                return True
    return False

def clear_rows():
    global score, remaining_time
    full_rows = [i for i, row in enumerate(grid) if all(row)]
    for row_index in full_rows:
        del grid[row_index]
        grid.insert(0, [0] * 10)
        remaining_time += 3  # Каждый раз, когда удаляется строка, время увеличивается на 3 секунды...
        score[0] += 100  # Предположим, что игрок 1 забивает
        score[1] += 100  # Предположим, что игрок 2 набирает очки

def game_loop():
    global grid, current_piece, score, game_over
    current_piece = new_piece()
    x, y = 4, 0

    while not game_over and remaining_time > 0:
        time.sleep(0.5)
        if not collision(current_piece, (x, y + 1)):
            y += 1
        else:
            for i, row in enumerate(current_piece):
                for j, cell in enumerate(row):
                    if cell:
                        grid[y + i][x + j] = 1
            clear_rows()
            current_piece = new_piece()
            x, y = 4, 0
            if collision(current_piece, (x, y)):
                game_over = True
        broadcast_state()
        remaining_time -= 1  # Уменьшение на 1 секунду каждые 0,5 секунды

def broadcast_state():
    state = {
        'grid': grid,
        'current_piece': current_piece,
        'score': score,
        'game_over': game_over,
        'player_names': player_names,
        'remaining_time': remaining_time
    }
    message = json.dumps(state).encode('utf-8')
    for client in clients:
        client.send(message)

def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
            if data:
                action = json.loads(data)
                if action['type'] == 'move':
                    global x, y
                    if action['direction'] == 'left' and not collision(current_piece, (x - 1, y)):
                        x -= 1
                    elif action['direction'] == 'right' and not collision(current_piece, (x + 1, y)):
                        x += 1
                    elif action['direction'] == 'down' and not collision(current_piece, (x, y + 1)):
                        y += 1
                    elif action['direction'] == 'rotate':
                        rotated_piece = rotate_piece(current_piece)
                        if not collision(rotated_piece, (x, y)):
                            current_piece = rotated_piece
                    broadcast_state()
                elif action['type'] == 'player_name':
                    player_names[action['player_id']] = action['name']
                    broadcast_state()
        except Exception as e:
            print(f"Error handling client: {e}")
            break

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(2)
    print(f"Server started on {HOST}:{PORT}")

    threading.Thread(target=game_loop, daemon=True).start()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connected by {addr}")
        clients.append(client_socket)
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

if __name__ == "__main__":
    start_server()
