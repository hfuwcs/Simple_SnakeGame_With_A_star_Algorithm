import pygame
import random
import heapq
import noise
import tkinter as tk
from tkinter import messagebox
import numpy as np
import matplotlib.pyplot as plt

# Khởi tạo pygame
pygame.init()
font = pygame.font.Font("Assets/DroidSansMono.ttf", 48)


# Load hình ảnh
cell_image = pygame.image.load('Assets/cell.png')
snake_body_image = pygame.image.load('Assets/snake_body.png')
snake_head_image = pygame.image.load('Assets/snake_head.png')
food_image = pygame.image.load('Assets/food.png')
obstacle_image = pygame.image.load('Assets/obstacle.png')
icon_image = pygame.image.load('Assets/icon.ico')


# Kích thước cửa sổ và thiết lập các biến
WIDTH, HEIGHT = 1200, 1000


# Cho phép nhập số hàng và số cột
n = None
while n is None:
    try:
        n = int(input("Nhập số hàng (n): "))
        if n <= 0:
            print("Vui lòng nhập một số nguyên dương.")
            n = None
    except ValueError:
        print("Vui lòng nhập một số nguyên hợp lệ.")

m = None
while m is None:
    try:
        m = int(input("Nhập số cột (m): "))
        if m <= 0:
            print("Vui lòng nhập một số nguyên dương.")
            m = None
    except ValueError:
        print("Vui lòng nhập một số nguyên hợp lệ.")


# Tính toán kích thước ô dựa trên n và m
CELL_SIZE = min(WIDTH // m, HEIGHT // n)
WIDTH = CELL_SIZE * m
HEIGHT = CELL_SIZE * n

# Thay đổi kích thước hình ảnh theo kích thước của ô
cell_image = pygame.transform.scale(cell_image, (CELL_SIZE, CELL_SIZE))
snake_body_image = pygame.transform.scale(snake_body_image, (CELL_SIZE, CELL_SIZE))
snake_head_image = pygame.transform.scale(snake_head_image, (CELL_SIZE, CELL_SIZE))
food_image = pygame.transform.scale(food_image, (CELL_SIZE, CELL_SIZE))
obstacle_image = pygame.transform.scale(obstacle_image, (CELL_SIZE, CELL_SIZE))

COLS, ROWS = m, n

RED = (255, 0, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_icon(icon_image)
pygame.display.set_caption("Rắn săn mồi với thuật toán A*")



# Tạo các hàm hỗ trợ cho thuật toán A*
class Node:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.g = self.h = self.f = 0
        self.parent = None

    def __lt__(self, other):
        return self.f < other.f

def heuristic(a, b):
    return abs(a.x - b.x) + abs(a.y - b.y)

def a_star(start, goal, snake_body, obstacles):
    open_set = []
    closed_set = set()
    heapq.heappush(open_set, start)

    while open_set:
        current = heapq.heappop(open_set)

        if current.x == goal.x and current.y == goal.y:
            path = []
            while current:
                path.append((current.x, current.y))
                current = current.parent
            return path[::-1]

        closed_set.add((current.x, current.y))

        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            neighbor_x, neighbor_y = current.x + dx, current.y + dy
            if (neighbor_x, neighbor_y) in closed_set:
                continue
            if (neighbor_x, neighbor_y) in snake_body:
                continue
            if (neighbor_x, neighbor_y) in obstacles:
                continue
            if 0 <= neighbor_x < COLS and 0 <= neighbor_y < ROWS:
                neighbor = Node(neighbor_x, neighbor_y)
                neighbor.g = current.g + 1
                neighbor.h = heuristic(neighbor, goal)
                neighbor.f = neighbor.g + neighbor.h
                neighbor.parent = current
                heapq.heappush(open_set, neighbor)

    return None

#noise map
#Hàm control threshold
def adjust_threshold_for_ratio(noise_map, target_ratio):
    """
    Điều chỉnh threshold để đạt được tỷ lệ ô vượt ngưỡng mong muốn.

    Args:
        noise_map: Mảng 2D chứa giá trị noise.
        target_ratio: Tỷ lệ ô vượt ngưỡng mong muốn (0 < target_ratio < 1).

    Returns:
        threshold: Ngưỡng được điều chỉnh.
    """
    flat_values = noise_map.flatten()  # Chuyển noise map thành mảng 1 chiều
    sorted_values = np.sort(flat_values)  # Sắp xếp các giá trị theo thứ tự tăng dần
    index = int(len(sorted_values) * (1 - target_ratio))  # Xác định vị trí ngưỡng
    return sorted_values[index]


# Sử dụng hàm noise map để sinh chướng ngại vật
def generate_obstacles_with_noise(snake, target_ratio=0.2):
    noise_map = generate_noise_map(COLS, ROWS, scale=5)  # Tạo noise map cho kích thước bản đồ
    threshold = adjust_threshold_for_ratio(noise_map, target_ratio)
    obstacles = set()

    for x in range(COLS):
        for y in range(ROWS):
            # Nếu giá trị noise vượt ngưỡng, thêm ô vào chướng ngại vật
            if noise_map[x, y] > threshold and (x, y) not in snake:
                obstacles.add((x, y))
    print("Obstacles:", obstacles)
    return obstacles

# Tạo noise map
def generate_noise_map(width, height, scale=10, seed=None):
    if seed is None:
        seed = random.randint(0, 1000)  # Tạo seed ngẫu nhiên

    noise_map = np.zeros((width, height))
    for i in range(width):
        for j in range(height):
            noise_map[i][j] = noise.pnoise2(i / scale,
                                            j / scale,
                                            octaves=20,
                                            persistence=0.6,
                                            lacunarity=2.0,
                                            base=seed)
    # plt.imshow(noise_map, cmap="gray")
    # plt.title("Noise Map for Snake Game Obstacles")
    # plt.show()
    return noise_map



# Khởi tạo trạng thái trò chơi
def init_game():
    snake = [(COLS // 2, ROWS // 2), (COLS // 2 - 1, ROWS // 2)]  # Rắn có đầu và đuôi
    target_ratio = 0.2
    if(n*m < 20):
        target_ratio = 0.05
    elif (n*m < 50):
        target_ratio = 0.15
    else:
        target_ratio = 0.2
    obstacles = generate_obstacles_with_noise(snake, target_ratio)
    food = generate_food(snake, obstacles)
    score = 0
    return snake, food, obstacles, score

'''
Hàm cũ
def generate_food(snake, obstacles):
    while True:
        food = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        # Kiểm tra nếu thức ăn không nằm trong rắn, chướng ngại vật và có đường đi
        if food not in snake and food not in obstacles:
            return food
'''

def generate_food(snake, obstacles):
    max_attempts = 100  # Giới hạn số lần thử
    for _ in range(max_attempts):
        food = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        # Kiểm tra nếu thức ăn không nằm trong rắn, chướng ngại vật và có đường đi
        if food not in snake and food not in obstacles:
            start = Node(snake[0][0], snake[0][1])
            goal = Node(food[0], food[1])
            path = a_star(start, goal, snake[1:], obstacles)
            if path:  # Đảm bảo có đường đi tới thức ăn
                return food

    # Fallback nếu không tìm được vị trí hợp lệ sau max_attempts
    print("Warning: Could not place food with a valid path. Placing randomly.")
    while True:
        food = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if food not in snake and food not in obstacles:
            return food
        
# tạo chướng ngại vật
#Hàm cũ
def generate_obstacles(snake):
    num_obstacles = random.randint(max(1, (n * m) // 20), max(1, (n * m) // 10))
    obstacles = set()
    while len(obstacles) < num_obstacles:
        obstacle = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if obstacle not in snake:
            obstacles.add(obstacle)
    return obstacles

def draw_grid():
    for x in range(m):
        for y in range(n):
            screen.blit(cell_image, (x * CELL_SIZE, y * CELL_SIZE))

def draw_snake(snake):
    for i, (x, y) in enumerate(snake):
        if i == 0:  # Đầu rắn
            if previous_head:
                dx = snake[0][0] - previous_head[0]
                dy = snake[0][1] - previous_head[1]
                if dx == 1:
                    angle = -90    # Di chuyển sang phải
                elif dx == -1:
                    angle = 90  # Di chuyển sang trái
                elif dy == 1:
                    angle = 180   # Di chuyển xuống
                elif dy == -1:
                    angle = 0  # Di chuyển lên
                else:
                    angle = 0

                # Xoay đầu rắn cho đúng hướng đi
                rotated_head = pygame.transform.rotate(snake_head_image, angle)
            else:
                rotated_head = snake_head_image

            screen.blit(rotated_head, (x * CELL_SIZE, y * CELL_SIZE))
        else:
            screen.blit(snake_body_image, (x * CELL_SIZE, y * CELL_SIZE))


def draw_food(food):
    x, y = food
    screen.blit(food_image, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

def draw_obstacles(obstacles):
    for x, y in obstacles:
        screen.blit(obstacle_image, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

def draw_score(score):
    score_text = font.render(f"Score: {score}", True, (255, 255, 255))  # Màu trắng
    text_rect = score_text.get_rect()
    text_rect.topright = (WIDTH - 10, 10)  # Góc trên bên phải màn hình
    screen.blit(score_text, text_rect)

def show_game_over():
    text = font.render("Game Over! \n Press Space to Restart \n", True, RED)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    
    screen.blit(text, text_rect)
    pygame.display.flip()

# Vòng lặp chính của trò chơi
def main():
    clock = pygame.time.Clock()
    snake, food, obstacles, score = init_game()
    paused = False

    while True:
        screen.fill((0, 0, 0))
        draw_grid()
        global previous_head
        previous_head = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN and paused and event.key == pygame.K_SPACE:
                snake, food, obstacles, score = init_game()  # Khởi động lại trò chơi
                paused = False

        if not paused:
            previous_head = snake[0]
            start = Node(snake[0][0], snake[0][1])
            goal = Node(food[0], food[1])
            path = a_star(start, goal, snake[1:], obstacles)

            if path and len(path) > 1:
                new_head = path[1]
            else:
                paused = True  # Không tìm thấy đường đi => Game over

            if not paused:
                snake.insert(0, new_head)

                if snake[0] == food:
                    food = generate_food(snake, obstacles)  # Sinh mồi mới
                    score += 1  # Tăng điểm
                else:
                    snake.pop()

        draw_snake(snake)
        draw_food(food)
        draw_obstacles(obstacles)
        draw_score(score)
        if paused:
            show_game_over()

        pygame.display.flip()
        if(n*m < 20):
            clock.tick(4)
        elif (n*m < 50):
            clock.tick(10)
        else:
            clock.tick(20)

if __name__ == "__main__":
    main()

