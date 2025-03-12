import pygame
import random
import socket
import json
import threading
import time
import sys

# настройки игры
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600 # Настройка разрешения экрана задается толоько здесь!
GRID_WIDTH, GRID_HEIGHT = 10, 20
BLOCK_SIZE = 30
GAME_WIDTH = GRID_WIDTH * BLOCK_SIZE
GAME_HEIGHT = GRID_HEIGHT * BLOCK_SIZE
SIDEBAR_WIDTH = SCREEN_WIDTH - GAME_WIDTH
BG_COLOR = (105, 105, 105)  # #696969
GRID_COLOR = (199, 21, 133)  # #C71585
BLOCK_COLORS = [
    (199, 21, 133),  # I
    (199, 21, 133),  # J
    (199, 21, 133),  # L
    (199, 21, 133),  # O
    (199, 21, 133),  # S
    (199, 21, 133),  # T
    (199, 21, 133)   # Z
]
TEXT_COLOR = (255, 255, 255)  # #FFFFFF
INITIAL_SPEED = 500  # миллисекунда
ACCELERATION = 50    # Сложность увеличения скорости (миллисекунды)

# Определение формы блока
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

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("PyCo-Tetris")
clock = pygame.time.Clock()

# состояние игры
game_grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
current_piece = None
next_piece = None
score = 0
speed = INITIAL_SPEED
game_over = False
paused = False
player_name = "Player"
remaining_time = 120  # Первоначальное оставшееся время составляет 120 секунд.

# Конфигурация сети
HOST = '127.0.0.1'
PORT = 65432
BUFFER_SIZE = 1024
clients = []
player_names = ["Player 1", "Player 2"]

def new_piece():
    global current_piece, next_piece
    if next_piece is None:
        next_piece = random.choice(list(SHAPES.values()))
    current_piece = next_piece
    next_piece = random.choice(list(SHAPES.values()))
    x = GRID_WIDTH // 2 - len(current_piece[0]) // 2
    y = 0
    return current_piece, x, y

def rotate_piece(piece):
    return [list(row) for row in zip(*piece[::-1])]

def collision(piece, offset):
    off_x, off_y = offset
    for y, row in enumerate(piece):
        for x, cell in enumerate(row):
            try:
                if cell and game_grid[y + off_y][x + off_x]:
                    return True
            except IndexError:
                return True
    return False

def clear_rows():
    global score, remaining_time
    full_rows = [i for i, row in enumerate(game_grid) if all(row)]
    for row_index in full_rows:
        del game_grid[row_index]
        game_grid.insert(0, [0] * GRID_WIDTH)
        remaining_time += 3  # Каждый раз, когда линия удаляется, время увеличивается на 3 секунды.
        score += {1: 100, 2: 300, 3: 600, 4: 1000}.get(len(full_rows), 100 * len(full_rows))

def draw_grid():
    for i in range(GRID_HEIGHT):
        for j in range(GRID_WIDTH):
            color = BLOCK_COLORS[game_grid[i][j] - 1] if game_grid[i][j] else GRID_COLOR
            pygame.draw.rect(screen, color, (j * BLOCK_SIZE, i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
            pygame.draw.rect(screen, BG_COLOR, (j * BLOCK_SIZE, i * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

def draw_piece(piece, offset):
    off_x, off_y = offset
    for y, row in enumerate(piece):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(screen, BLOCK_COLORS[SHAPES.index(piece)], 
                                 (off_x + x * BLOCK_SIZE, off_y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
                pygame.draw.rect(screen, BG_COLOR, (off_x + x * BLOCK_SIZE, off_y + y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

def draw_sidebar():
    font = pygame.font.SysFont('Arial', 24)
    text = font.render(f'Score: {score}', True, TEXT_COLOR)
    screen.blit(text, (GAME_WIDTH + 10, 10))
    text = font.render('Next:', True, TEXT_COLOR)
    screen.blit(text, (GAME_WIDTH + 10, 50))
    draw_piece(next_piece, (GAME_WIDTH + 10, 100))
    text = font.render(f'Player: {player_name}', True, TEXT_COLOR)
    screen.blit(text, (GAME_WIDTH + 10, 150))
    minutes = remaining_time // 60
    seconds = remaining_time % 60
    text = font.render(f'Time: {minutes:02d}:{seconds:02d}', True, TEXT_COLOR)
    screen.blit(text, (GAME_WIDTH + 10, 190))

def game_over_screen():
    font = pygame.font.SysFont('Arial', 48)
    text = font.render('Game Over', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(text, text_rect)
    font = pygame.font.SysFont('Arial', 24)
    text = font.render(f'Score: {score}', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(text, text_rect)
    text = font.render('Press R to restart', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
    screen.blit(text, text_rect)

def start_screen():
    screen.fill(BG_COLOR)
    font = pygame.font.SysFont('Arial', 48)
    text = font.render('PyCo-Tetris', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
    screen.blit(text, text_rect)
    font = pygame.font.SysFont('Arial', 24)
    text = font.render('Press any key to start', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(text, text_rect)
    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

def main_menu():
    screen.fill(BG_COLOR)
    font = pygame.font.SysFont('Arial', 48)
    text = font.render('PyCo', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    screen.blit(text, text_rect)
    font = pygame.font.SysFont('Arial', 24)
    text = font.render('Single Player', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    screen.blit(text, text_rect)
    text = font.render('Multiplayer', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
    screen.blit(text, text_rect)
    text = font.render('High Scores', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
    screen.blit(text, text_rect)
    text = font.render('Exit', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 150))
    screen.blit(text, text_rect)
    text = font.render('Fomyak Production Dev 2025', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 20))
    screen.blit(text, text_rect)
    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    single_player_game()
                elif event.key == pygame.K_2:
                    multiplayer_game()
                elif event.key == pygame.K_3:
                    high_scores()
                elif event.key == pygame.K_4:
                    pygame.quit()
                    sys.exit()

def single_player_game():
    global game_grid, current_piece, next_piece, score, speed, game_over, paused, player_name, remaining_time
    game_grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    current_piece, x, y = new_piece()
    next_piece = None
    score = 0
    speed = INITIAL_SPEED
    game_over = False
    paused = False
    player_name = input("Then you're a warrior?: ")
    remaining_time = 120

    while not game_over:
        screen.fill(BG_COLOR)
        draw_grid()
        draw_piece(current_piece, (x * BLOCK_SIZE, y * BLOCK_SIZE))
        draw_sidebar()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if not collision(current_piece, (x - 1, y)):
                        x -= 1
                elif event.key == pygame.K_RIGHT:
                    if not collision(current_piece, (x + 1, y)):
                        x += 1
                elif event.key == pygame.K_DOWN:
                    if not collision(current_piece, (x, y + 1)):
                        y += 1
                elif event.key == pygame.K_UP:
                    rotated_piece = rotate_piece(current_piece)
                    if not collision(rotated_piece, (x, y)):
                        current_piece = rotated_piece
                elif event.key == pygame.K_SPACE:
                    paused = not paused

        if paused:
            pygame.display.update()
            clock.tick(10)
            continue

        current_time = pygame.time.get_ticks()
        if current_time - last_fall_time >= speed:
            if not collision(current_piece, (x, y + 1)):
                y += 1
            else:
                for i, row in enumerate(current_piece):
                    for j, cell in enumerate(row):
                        if cell:
                            game_grid[y + i][x + j] = SHAPES.index(current_piece) + 1
                clear_rows()
                current_piece, x, y = new_piece()
                if collision(current_piece, (x, y)):
                    game_over = True
            last_fall_time = current_time

        pygame.display.update()
        clock.tick(60)

    game_over_screen()
    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                single_player_game()

def multiplayer_game():
    global game_grid, current_piece, next_piece, score, speed, game_over, paused, player_name, remaining_time
    game_grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    current_piece, x, y = new_piece()
    next_piece = None
    score = 0
    speed = INITIAL_SPEED
    game_over = False
    paused = False
    player_name = input("Then you're a warrior?: ")
    remaining_time = 120

    # Запустить сервер
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Подключить клиент
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((HOST, PORT))

    def receive_state():
        global game_grid, current_piece, score, game_over, player_names, remaining_time
        while True:
            try:
                data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                if data:
                    state = json.loads(data)
                    game_grid = state['grid']
                    current_piece = state['current_piece']
                    score = state['score']
                    game_over = state['game_over']
                    player_names = state['player_names']
                    remaining_time = state['remaining_time']
            except Exception as e:
                print(f"Error receiving state: {e}")
                break

    receive_thread = threading.Thread(target=receive_state, daemon=True)
    receive_thread.start()

    while not game_over:
        screen.fill(BG_COLOR)
        draw_grid()
        draw_piece(current_piece, (x * BLOCK_SIZE, y * BLOCK_SIZE))
        draw_sidebar()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if not collision(current_piece, (x - 1, y)):
                        x -= 1
                elif event.key == pygame.K_RIGHT:
                    if not collision(current_piece, (x + 1, y)):
                        x += 1
                elif event.key == pygame.K_DOWN:
                    if not collision(current_piece, (x, y + 1)):
                        y += 1
                elif event.key == pygame.K_UP:
                    rotated_piece = rotate_piece(current_piece)
                    if not collision(rotated_piece, (x, y)):
                        current_piece = rotated_piece
                elif event.key == pygame.K_SPACE:
                    paused = not paused

        if paused:
            pygame.display.update()
            clock.tick(10)
            continue

        current_time = pygame.time.get_ticks()
        if current_time - last_fall_time >= speed:
            if not collision(current_piece, (x, y + 1)):
                y += 1
            else:
                for i, row in enumerate(current_piece):
                    for j, cell in enumerate(row):
                        if cell:
                            game_grid[y + i][x + j] = SHAPES.index(current_piece) + 1
                clear_rows()
                current_piece, x, y = new_piece()
                if collision(current_piece, (x, y)):
                    game_over = True
            last_fall_time = current_time

        pygame.display.update()
        clock.tick(60)

    game_over_screen()
    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                multiplayer_game()

def start_server():
    global game_grid, current_piece, next_piece, score, speed, game_over, paused, player_name, remaining_time
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(2)
    print(f"Server started on {HOST}:{PORT}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connected by {addr}")
        clients.append(client_socket)
        threading.Thread(target=handle_client, args=(client_socket,), daemon=True).start()

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

def broadcast_state():
    state = {
        'grid': game_grid,
        'current_piece': current_piece,
        'score': score,
        'game_over': game_over,
        'player_names': player_names,
        'remaining_time': remaining_time
    }
    message = json.dumps(state).encode('utf-8')
    for client in clients:
        client.send(message)

def high_scores():
    # Показать наивысший балл
    screen.fill(BG_COLOR)
    font = pygame.font.SysFont('Arial', 48)
    text = font.render('High Scores', True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
    screen.blit(text, text_rect)
    font = pygame.font.SysFont('Arial', 24)
    # Список результатов
    high_scores = [(1000, 'Player1'), (800, 'Player2'), (600, 'Player3')]
    for i, (score, name) in enumerate(high_scores):
        text = font.render(f'{name}: {score}', True, TEXT_COLOR)
        screen.blit(text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + i * 30))
    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                waiting = False

if __name__ == "__main__":
    start_screen()
    main_menu()
