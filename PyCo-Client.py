import socket
import pygame
import json
import threading

# Конфигурация клиента
HOST = '127.0.0.1'
PORT = 65432
BUFFER_SIZE = 1024

# Инициализация Pygame
pygame.init()
screen = pygame.display.set_mode((300, 600))
pygame.display.set_caption("PyCo - tetris")
clock = pygame.time.Clock()

# Определение цвета
BG_COLOR = (0, 0, 0)
GRID_COLOR = (30, 30, 30)
BLOCK_COLOR = (255, 255, 255)
TEXT_COLOR = (255, 255, 255)

# Cостояние игры
grid = [[0 for _ in range(10)] for _ in range(20)]
current_piece = None
score = [0, 0]
game_over = False
player_names = ["Player 1", "Player 2"]
remaining_time = 120

def draw_grid():
    for i in range(20):
        for j in range(10):
            color = BLOCK_COLOR if grid[i][j] else GRID_COLOR
            pygame.draw.rect(screen, color, (j * 30, i * 30, 30, 30), 0)
            pygame.draw.rect(screen, BG_COLOR, (j * 30, i * 30, 30, 30), 1)

def draw_piece(piece, offset):
    off_x, off_y = offset
    for y, row in enumerate(piece):
        for x, cell in enumerate(row):
            if cell:
                pygame.draw.rect(screen, BLOCK_COLOR, (off_x + x * 30, off_y + y * 30, 30, 30), 0)
                pygame.draw.rect(screen, BG_COLOR, (off_x + x * 30, off_y + y * 30, 30, 30), 1)

def draw_player_names():
    font = pygame.font.SysFont('Arial', 24)
    text = font.render(player_names[0], True, TEXT_COLOR)
    screen.blit(text, (10, 10))
    text = font.render(player_names[1], True, TEXT_COLOR)
    screen.blit(text, (10, 560))

def draw_scores():
    font = pygame.font.SysFont('Arial', 24)
    text = font.render(f"Score: {score[0]}", True, TEXT_COLOR)
    screen.blit(text, (10, 40))
    text = font.render(f"Score: {score[1]}", True, TEXT_COLOR)
    screen.blit(text, (10, 590))

def draw_remaining_time():
    font = pygame.font.SysFont('Arial', 24)
    minutes = remaining_time // 60
    seconds = remaining_time % 60
    text = font.render(f"Time: {minutes:02d}:{seconds:02d}", True, TEXT_COLOR)
    screen.blit(text, (10, 30))

def receive_state():
    global grid, current_piece, score, game_over, player_names, remaining_time
    while True:
