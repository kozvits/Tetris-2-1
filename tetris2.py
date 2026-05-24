#!/usr/bin/env python3
"""
Tetris 2 (ZX Spectrum, 1990, Fuxoft) Clone
Реализация на Python + Pygame

Особенности:
- Классическая механика тетриса с 7 фигурами
- Вращение, сдвиг, ускоренное падение, мгновенный сброс
- Система очков и уровней, близкая к оригиналу
- Одиночная игра
- Сохранение рекорда в файле
- Простые звуковые эффекты (синтетические, в стиле ZX Spectrum)
- Меню: Новая игра, Рекорд, Выход

Управление:
- ← → : сдвиг фигуры влево/вправо
- ↑ : вращение
- ↓ : ускоренное падение
- Пробел : мгновенное падение вниз
- Esc / P : пауза/меню
"""

import pygame
import random
import json
import os
import math
import numpy as np

# === КОНСТАНТЫ ===
BLOCK_SIZE = 30  # Размер блока в пикселях
BOARD_WIDTH = 10  # Ширина поля в блоках
BOARD_HEIGHT = 20  # Высота поля в блоках
SIDEBAR_WIDTH = 200  # Ширина боковой панели
SCREEN_WIDTH = BOARD_WIDTH * BLOCK_SIZE + SIDEBAR_WIDTH
SCREEN_HEIGHT = BOARD_HEIGHT * BLOCK_SIZE

# Частота дискретизации для звука (как в ZX Spectrum)
SAMPLE_RATE = 22050

# Цвета в стиле ZX Spectrum (яркие, контрастные)
COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'cyan': (0, 255, 255),      # I
    'blue': (0, 0, 255),        # J
    'orange': (255, 165, 0),    # L
    'yellow': (255, 255, 0),    # O
    'green': (0, 255, 0),       # S
    'purple': (128, 0, 128),    # T
    'red': (255, 0, 0),         # Z
    'gray': (128, 128, 128),    # Заблокированные блоки
    'dark_gray': (64, 64, 64),  # Сетка
}

# Ноты для синтеза музыки (частоты в Гц) - октавы 4, 5, 6
NOTES = {
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13, 'E4': 329.63,
    'F4': 349.23, 'F#4': 369.99, 'G4': 392.00, 'G#4': 415.30, 'A4': 440.00,
    'A#4': 466.16, 'B4': 493.88,
    'C5': 523.25, 'C#5': 554.37, 'D5': 587.33, 'D#5': 622.25, 'E5': 659.25,
    'F5': 698.46, 'F#5': 739.99, 'G5': 783.99, 'G#5': 830.61, 'A5': 880.00,
    'A#5': 932.33, 'B5': 987.77,
    'C6': 1046.50,
    None: 0  # Пауза
}


def generate_square_wave(freq, duration, volume=0.3):
    """Генерирует квадратную волну (звук ZX Spectrum)"""
    if freq == 0:
        return np.zeros(int(SAMPLE_RATE * duration), dtype=np.int16)
    
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    # Квадратная волна: sign(sin(2*pi*f*t))
    wave = np.sign(np.sin(2 * np.pi * freq * t))
    wave = (wave * volume * 32767).astype(np.int16)
    return wave


class MusicPlayer:
    """Проигрыватель мелодий в стиле ZX Spectrum"""
    
    def __init__(self):
        self.isPlaying = False
        self.current_track = None
        self.current_track_name = None
        
        # Мелодия A: Korobeiniki (классическая тема Tetris)
        self.melody_a = [
            ('E5', 0.5), ('B4', 0.5), ('C5', 0.5), ('D5', 0.5), ('C5', 0.5), ('B4', 0.5),
            ('A4', 1.0), ('A4', 0.5), ('B4', 0.5), ('C5', 0.5), ('D5', 0.5), ('E5', 0.5),
            ('C5', 0.5), ('A4', 0.5), ('A4', 1.0),
            ('D5', 0.5), ('F5', 0.5), ('A5', 0.5), ('G5', 0.5), ('F5', 0.5), ('E5', 0.5),
            ('D5', 0.5), ('C5', 0.5), ('B4', 0.5), ('C5', 0.5), ('D5', 0.5), ('E5', 0.5),
            ('C5', 0.5), ('A4', 0.5), ('A4', 1.0),
        ]
        
        # Мелодия B: В стиле Баха (Toccata and Fugue упрощённо)
        self.melody_b = [
            ('A4', 0.25), ('B4', 0.25), ('C5', 0.25), ('D5', 0.25), 
            ('E5', 0.25), ('F5', 0.25), ('G5', 0.25), ('A5', 0.25),
            ('A5', 0.25), ('G5', 0.25), ('F5', 0.25), ('E5', 0.25),
            ('D5', 0.25), ('C5', 0.25), ('B4', 0.25), ('A4', 0.25),
            ('E5', 0.25), ('F#5', 0.25), ('G5', 0.25), ('A5', 0.25),
            ('B5', 0.25), ('C6', 0.25), ('B5', 0.25), ('A5', 0.25),
            ('G5', 0.5), ('E5', 0.5), ('A4', 0.5), ('E5', 0.5),
        ]
        
        # Мелодия C: Энергичная тема для высоких уровней
        self.melody_c = [
            ('C5', 0.25), ('E5', 0.25), ('G5', 0.25), ('C6', 0.25),
            ('G5', 0.25), ('E5', 0.25), ('C5', 0.25), ('E5', 0.25),
            ('F5', 0.25), ('A5', 0.25), ('C6', 0.25), ('F6', 0.25) if 'F6' in NOTES else ('F5', 0.25),
            ('C6', 0.25), ('A5', 0.25), ('F5', 0.25), ('A5', 0.25),
        ]
        
        self.tempo_a = 0.35  # Длительность четверти для мелодии A
        self.tempo_b = 0.20  # Длительность для мелодии B (быстрее)
        self.tempo_c = 0.18  # Длительность для мелодии C (ещё быстрее)

    def play_track(self, track_name, loop=True):
        """Воспроизвести трек по имени"""
        if not hasattr(pygame.mixer, 'get_init') or not pygame.mixer.get_init():
            return
            
        melody_map = {'A': self.melody_a, 'B': self.melody_b, 'C': self.melody_c}
        tempo_map = {'A': self.tempo_a, 'B': self.tempo_b, 'C': self.tempo_c}
        
        melody = melody_map.get(track_name, self.melody_a)
        tempo = tempo_map.get(track_name, self.tempo_a)
        
        # Генерируем весь трек заранее
        samples = []
        for note, duration in melody:
            freq = NOTES.get(note, 0)
            chunk = generate_square_wave(freq, duration * tempo, volume=0.12)
            samples.append(chunk)
            
        full_track = np.concatenate(samples)
        
        # Создаем звук из массива numpy
        sound = pygame.sndarray.make_sound(full_track)
        sound.set_volume(0.25)
        
        if loop:
            sound.play(-1)  # Бесконечный повтор
        else:
            sound.play()
            
        self.current_track = sound
        self.current_track_name = track_name
        self.isPlaying = True

    def stop(self):
        """Остановить воспроизведение"""
        if self.current_track:
            self.current_track.stop()
        self.isPlaying = False
        self.current_track = None

    def update_music(self, level):
        """Переключает музыку в зависимости от уровня"""
        # Выбор мелодии по уровню: 0-4 -> A, 5-9 -> B, 10+ -> C
        if level < 5:
            track = 'A'
        elif level < 10:
            track = 'B'
        else:
            track = 'C'
        
        # Если играет другая мелодия или ничего не играет - запускаем нужную
        if not self.isPlaying or self.current_track_name != track:
            self.stop()
            self.play_track(track)

# Фигуры (тетрамино) - каждая фигура представлена как список координат относительно центра
FIGURES = {
    'I': [(0, -1), (0, 0), (0, 1), (0, 2)],
    'J': [(-1, -1), (-1, 0), (0, 0), (1, 0)],
    'L': [(-1, 0), (0, 0), (1, 0), (1, -1)],
    'O': [(0, 0), (1, 0), (0, 1), (1, 1)],
    'S': [(0, 0), (1, 0), (-1, 1), (0, 1)],
    'T': [(-1, 0), (0, 0), (1, 0), (0, -1)],
    'Z': [(-1, 0), (0, 0), (0, 1), (1, 1)],
}

FIGURE_COLORS = {
    'I': 'cyan',
    'J': 'blue',
    'L': 'orange',
    'O': 'yellow',
    'S': 'green',
    'T': 'purple',
    'Z': 'red',
}

# Состояния игры
STATE_MENU = 0
STATE_PLAYING = 1
STATE_PAUSED = 2
STATE_GAME_OVER = 3

# Файл для сохранения рекорда
HIGHSCORE_FILE = "tetris2_highscore.json"


class SoundManager:
    """Простой менеджер звуков в стиле ZX Spectrum (синтетические звуки)"""
    
    def __init__(self):
        self.enabled = True
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.initialized = True
        except:
            self.initialized = False
            self.enabled = False
    
    def play_tone(self, frequency, duration_ms, volume=0.3):
        """Воспроизвести простой тон (синусоида)"""
        if not self.enabled or not self.initialized:
            return
        
        try:
            sample_rate = 22050
            n_samples = int(sample_rate * duration_ms / 1000)
            buf = bytes([
                int(127 + 127 * math.sin(2 * math.pi * frequency * t / sample_rate) * volume)
                for t in range(n_samples)
            ])
            sound = pygame.mixer.Sound(buffer=buf)
            sound.play()
        except:
            pass
    
    def play_move(self):
        """Звук перемещения фигуры"""
        self.play_tone(440, 50, 0.1)
    
    def play_rotate(self):
        """Звук вращения фигуры"""
        self.play_tone(660, 60, 0.15)
    
    def play_drop(self):
        """Звук приземления фигуры"""
        self.play_tone(220, 100, 0.2)
    
    def play_clear_line(self):
        """Звук очистки линии"""
        self.play_tone(880, 150, 0.3)
        pygame.time.delay(50)
        self.play_tone(1100, 150, 0.3)
    
    def play_game_over(self):
        """Звук конца игры"""
        for freq in [440, 392, 349, 294]:
            self.play_tone(freq, 200, 0.3)
            pygame.time.delay(150)


class Figure:
    """Класс фигуры (тетрамино)"""
    
    def __init__(self, figure_type=None):
        if figure_type is None:
            figure_type = random.choice(list(FIGURES.keys()))
        
        self.type = figure_type
        self.color = FIGURE_COLORS[figure_type]
        # Копируем координаты фигуры
        self.blocks = list(FIGURES[figure_type])
        self.x = BOARD_WIDTH // 2 - 1  # Начальная позиция по X
        self.y = 0  # Начальная позиция по Y (сверху)
    
    def get_positions(self):
        """Получить абсолютные координаты всех блоков фигуры"""
        return [(self.x + dx, self.y + dy) for dx, dy in self.blocks]
    
    def rotate(self):
        """Вращение фигуры по часовой стрелке"""
        # Для фигуры O вращение не нужно
        if self.type == 'O':
            return
        
        # Поворот на 90 градусов: (x, y) -> (-y, x)
        self.blocks = [(-dy, dx) for dx, dy in self.blocks]
    
    def move(self, dx, dy):
        """Перемещение фигуры"""
        self.x += dx
        self.y += dy


class Board:
    """Игровое поле"""
    
    def __init__(self):
        self.width = BOARD_WIDTH
        self.height = BOARD_HEIGHT
        # Поле: None для пустых клеток, цвет для заполненных
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]
    
    def is_valid_position(self, figure):
        """Проверка, находится ли фигура в допустимой позиции"""
        for x, y in figure.get_positions():
            # Проверка границ
            if x < 0 or x >= self.width or y >= self.height:
                return False
            # Проверка на столкновение с другими блоками (только если блок уже на поле)
            if y >= 0 and self.grid[y][x] is not None:
                return False
        return True
    
    def lock_figure(self, figure):
        """Зафиксировать фигуру на поле"""
        for x, y in figure.get_positions():
            if 0 <= y < self.height and 0 <= x < self.width:
                self.grid[y][x] = figure.color
    
    def clear_lines(self):
        """Очистить заполненные линии, вернуть количество очищенных линий"""
        lines_cleared = 0
        y = self.height - 1
        
        while y >= 0:
            # Если линия полностью заполнена
            if all(self.grid[y][x] is not None for x in range(self.width)):
                # Удаляем линию и сдвигаем всё вниз
                for move_y in range(y, 0, -1):
                    self.grid[move_y] = self.grid[move_y - 1][:]
                self.grid[0] = [None for _ in range(self.width)]
                lines_cleared += 1
            else:
                y -= 1
        
        return lines_cleared
    
    def check_game_over(self, figure):
        """Проверка условия проигрыша (новая фигура не помещается)"""
        return not self.is_valid_position(figure)
    
    def reset(self):
        """Очистить поле"""
        self.grid = [[None for _ in range(self.width)] for _ in range(self.height)]


class Game:
    """Основной класс игры"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Tetris 2 (ZX Spectrum Clone)")
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.sound = SoundManager()
        self.music = MusicPlayer()  # Добавляем проигрыватель музыки
        
        self.state = STATE_MENU
        self.board = Board()
        self.current_figure = None
        self.next_figure = None
        
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        self.high_score = self.load_high_score()
        
        # Таймер падения фигуры
        self.drop_timer = 0
        self.drop_interval = self.get_drop_interval()
        
        # Для режима двух игроков (если будет реализован)
        self.two_player_mode = False
    
    def get_drop_interval(self):
        """Получить интервал падения в зависимости от уровня (как в оригинале)"""
        # Уменьшаем интервал с ростом уровня (увеличиваем скорость)
        # Базовый интервал ~1000ms, уменьшается с уровнем
        base_interval = 1000
        return max(50, base_interval - (self.level - 1) * 80)
    
    def load_high_score(self):
        """Загрузить рекорд из файла"""
        try:
            if os.path.exists(HIGHSCORE_FILE):
                with open(HIGHSCORE_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('high_score', 0)
        except:
            pass
        return 0
    
    def save_high_score(self):
        """Сохранить рекорд в файл"""
        try:
            with open(HIGHSCORE_FILE, 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except:
            pass
    
    def new_game(self):
        """Начать новую игру"""
        self.board.reset()
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        self.drop_interval = self.get_drop_interval()
        self.current_figure = Figure()
        self.next_figure = Figure()
        self.drop_timer = 0
        self.state = STATE_PLAYING
        
        # Запуск музыки
        self.music.stop()
        self.music.update_music(self.level)
    
    def spawn_figure(self):
        """Создать новую фигуру"""
        self.current_figure = self.next_figure
        self.next_figure = Figure()
        
        # Проверка на game over сразу после появления
        if not self.board.is_valid_position(self.current_figure):
            self.state = STATE_GAME_OVER
            self.sound.play_game_over()
            
            # Обновление рекорда
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
    
    def calculate_score(self, lines):
        """Расчет очков за очистку линий (как в классическом тетрисе)"""
        # Очки за количество линий (классическая система)
        points = {1: 40, 2: 100, 3: 300, 4: 1200}
        return points.get(lines, 0) * self.level
    
    def update(self, dt):
        """Обновление игрового состояния"""
        if self.state != STATE_PLAYING:
            return
        
        # Обновление таймера падения
        self.drop_timer += dt
        
        if self.drop_timer >= self.drop_interval:
            self.drop_timer = 0
            self.try_move_figure(0, 1)
    
    def try_move_figure(self, dx, dy):
        """Попытка переместить фигуру"""
        if self.current_figure is None:
            return False
        
        old_x, old_y = self.current_figure.x, self.current_figure.y
        self.current_figure.move(dx, dy)
        
        if self.board.is_valid_position(self.current_figure):
            if dx != 0 or dy != 0:
                self.sound.play_move()
            return True
        else:
            # Возвращаем назад
            self.current_figure.x, self.current_figure.y = old_x, old_y
            return False
    
    def try_rotate_figure(self):
        """Попытка вращать фигуру"""
        if self.current_figure is None:
            return
        
        old_blocks = self.current_figure.blocks[:]
        self.current_figure.rotate()
        
        if self.board.is_valid_position(self.current_figure):
            self.sound.play_rotate()
        else:
            # Wall kick - попытка сдвинуть фигуру для вращения
            for offset in [(1, 0), (-1, 0), (0, -1), (2, 0), (-2, 0)]:
                self.current_figure.x += offset[0]
                self.current_figure.y += offset[1]
                if self.board.is_valid_position(self.current_figure):
                    self.sound.play_rotate()
                    return
                self.current_figure.x -= offset[0]
                self.current_figure.y -= offset[1]
            
            # Возвращаем исходное состояние
            self.current_figure.blocks = old_blocks
    
    def hard_drop(self):
        """Мгновенное падение фигуры вниз"""
        if self.current_figure is None:
            return
        
        drop_distance = 0
        while self.try_move_figure(0, 1):
            drop_distance += 1
        
        # Очки за жесткое падение
        self.score += drop_distance * 2
        
        self.lock_current_figure()
    
    def soft_drop(self):
        """Ускоренное падение"""
        if self.try_move_figure(0, 1):
            self.score += 1  # Очко за каждое мягкое падение
    
    def lock_current_figure(self):
        """Зафиксировать текущую фигуру и создать новую"""
        self.board.lock_figure(self.current_figure)
        self.sound.play_drop()
        
        # Очистка линий
        lines = self.board.clear_lines()
        if lines > 0:
            self.sound.play_clear_line()
            self.score += self.calculate_score(lines)
            self.lines_cleared_total += lines
            
            # Повышение уровня каждые 10 линий
            new_level = self.lines_cleared_total // 10 + 1
            if new_level > self.level:
                self.level = new_level
                self.drop_interval = self.get_drop_interval()
                # Обновление музыки при смене уровня
                self.music.update_music(self.level)
        
        # Создание новой фигуры
        self.spawn_figure()
    
    def handle_input(self):
        """Обработка ввода"""
        keys = pygame.key.get_pressed()
        
        if self.state == STATE_PLAYING:
            if keys[pygame.K_LEFT]:
                self.try_move_figure(-1, 0)
                pygame.time.delay(100)  # Задержка для предотвращения слишком быстрого движения
            elif keys[pygame.K_RIGHT]:
                self.try_move_figure(1, 0)
                pygame.time.delay(100)
            elif keys[pygame.K_DOWN]:
                self.soft_drop()
                pygame.time.delay(50)
    
    def process_event(self, event):
        """Обработка событий"""
        if event.type == pygame.KEYDOWN:
            if self.state == STATE_MENU:
                if event.key == pygame.K_RETURN:
                    self.new_game()
                elif event.key == pygame.K_ESCAPE:
                    return False  # Выход из игры
                elif event.key == pygame.K_2:
                    self.two_player_mode = not self.two_player_mode
            
            elif self.state == STATE_PLAYING:
                if event.key == pygame.K_LEFT:
                    self.try_move_figure(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self.try_move_figure(1, 0)
                elif event.key == pygame.K_UP:
                    self.try_rotate_figure()
                elif event.key == pygame.K_DOWN:
                    self.soft_drop()
                elif event.key == pygame.K_SPACE:
                    self.hard_drop()
                elif event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.state = STATE_PAUSED
                    self.music.stop()  # Остановить музыку на паузе
            
            elif self.state == STATE_PAUSED:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    self.state = STATE_PLAYING
                    self.music.update_music(self.level)  # Возобновить музыку
                elif event.key == pygame.K_m:
                    self.state = STATE_MENU
                    self.music.stop()
            
            elif self.state == STATE_GAME_OVER:
                if event.key == pygame.K_RETURN:
                    self.new_game()
                elif event.key == pygame.K_m:
                    self.state = STATE_MENU
                    self.music.stop()
                elif event.key == pygame.K_ESCAPE:
                    self.music.stop()
                    return False
        
        return True
    
    def draw_block(self, x, y, color_name, surface=None):
        """Нарисовать блок"""
        if surface is None:
            surface = self.screen
        
        color = COLORS.get(color_name, COLORS['white'])
        rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
        
        # Основной цвет
        pygame.draw.rect(surface, color, rect)
        
        # Рамка для эффекта объема
        pygame.draw.rect(surface, COLORS['white'], rect, 2)
        pygame.draw.rect(surface, COLORS['dark_gray'], rect, 1)
    
    def draw_board(self):
        """Нарисовать игровое поле"""
        # Фон поля
        board_rect = pygame.Rect(0, 0, BOARD_WIDTH * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE)
        pygame.draw.rect(self.screen, COLORS['black'], board_rect)
        
        # Сетка
        for x in range(BOARD_WIDTH + 1):
            pygame.draw.line(self.screen, COLORS['dark_gray'],
                           (x * BLOCK_SIZE, 0),
                           (x * BLOCK_SIZE, BOARD_HEIGHT * BLOCK_SIZE))
        for y in range(BOARD_HEIGHT + 1):
            pygame.draw.line(self.screen, COLORS['dark_gray'],
                           (0, y * BLOCK_SIZE),
                           (BOARD_WIDTH * BLOCK_SIZE, y * BLOCK_SIZE))
        
        # Заблокированные блоки
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                if self.board.grid[y][x] is not None:
                    self.draw_block(x, y, self.board.grid[y][x])
        
        # Текущая фигура
        if self.current_figure is not None and self.state == STATE_PLAYING:
            for x, y in self.current_figure.get_positions():
                if y >= 0:  # Рисуем только видимые блоки
                    self.draw_block(x, y, self.current_figure.color)
    
    def draw_sidebar(self):
        """Нарисовать боковую панель"""
        sidebar_x = BOARD_WIDTH * BLOCK_SIZE
        
        # Фон панели
        pygame.draw.rect(self.screen, COLORS['dark_gray'],
                        (sidebar_x, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT))
        
        # Текст информации
        y_offset = 20
        
        # Заголовок
        title = self.font.render("TETRIS 2", True, COLORS['white'])
        self.screen.blit(title, (sidebar_x + 20, y_offset))
        y_offset += 50
        
        # Счет
        score_text = self.small_font.render(f"Score: {self.score}", True, COLORS['white'])
        self.screen.blit(score_text, (sidebar_x + 10, y_offset))
        y_offset += 40
        
        # Уровень
        level_text = self.small_font.render(f"Level: {self.level}", True, COLORS['white'])
        self.screen.blit(level_text, (sidebar_x + 10, y_offset))
        y_offset += 40
        
        # Линии
        lines_text = self.small_font.render(f"Lines: {self.lines_cleared_total}", True, COLORS['white'])
        self.screen.blit(lines_text, (sidebar_x + 10, y_offset))
        y_offset += 60
        
        # Следующая фигура
        next_text = self.small_font.render("Next:", True, COLORS['white'])
        self.screen.blit(next_text, (sidebar_x + 10, y_offset))
        y_offset += 30
        
        if self.next_figure is not None:
            # Рисуем следующую фигуру в миниатюре
            mini_block_size = 20
            center_x = sidebar_x + SIDEBAR_WIDTH // 2
            center_y = y_offset + 40
            
            for dx, dy in self.next_figure.blocks:
                block_x = center_x + dx * mini_block_size - mini_block_size
                block_y = center_y + dy * mini_block_size - mini_block_size
                rect = pygame.Rect(block_x, block_y, mini_block_size, mini_block_size)
                pygame.draw.rect(self.screen, COLORS[self.next_figure.color], rect)
                pygame.draw.rect(self.screen, COLORS['white'], rect, 1)
        
        y_offset += 120
        
        # Рекорд
        highscore_text = self.small_font.render(f"High: {self.high_score}", True, COLORS['yellow'])
        self.screen.blit(highscore_text, (sidebar_x + 10, y_offset))
        y_offset += 50
        
        # Управление
        controls_title = self.small_font.render("Controls:", True, COLORS['white'])
        self.screen.blit(controls_title, (sidebar_x + 10, y_offset))
        y_offset += 30
        
        controls = [
            "← → : Move",
            "↑ : Rotate",
            "↓ : Soft Drop",
            "Space : Hard Drop",
            "P/Esc : Pause",
        ]
        
        for control in controls:
            ctrl_text = self.small_font.render(control, True, COLORS['white'])
            self.screen.blit(ctrl_text, (sidebar_x + 10, y_offset))
            y_offset += 22
    
    def draw_menu(self):
        """Нарисовать меню"""
        self.screen.fill(COLORS['black'])
        
        # Заголовок
        title = self.font.render("TETRIS 2", True, COLORS['cyan'])
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 100))
        self.screen.blit(title, title_rect)
        
        subtitle = self.small_font.render("ZX Spectrum Clone", True, COLORS['white'])
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 140))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Опции меню
        y_offset = 250
        
        menu_items = [
            ("Press ENTER for New Game", COLORS['white']),
            ("", COLORS['black']),
            (f"High Score: {self.high_score}", COLORS['yellow']),
            ("", COLORS['black']),
            ("Controls:", COLORS['white']),
            ("← → : Move left/right", COLORS['gray']),
            ("↑ : Rotate", COLORS['gray']),
            ("↓ : Soft drop", COLORS['gray']),
            ("Space : Hard drop", COLORS['gray']),
            ("P/Esc : Pause", COLORS['gray']),
            ("", COLORS['black']),
            ("ESC to Quit", COLORS['red']),
        ]
        
        for text, color in menu_items:
            if text:
                rendered = self.small_font.render(text, True, color)
                rect = rendered.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
                self.screen.blit(rendered, rect)
            y_offset += 30
    
    def draw_pause(self):
        """Нарисовать экран паузы"""
        # Полупрозрачный оверлей
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(COLORS['black'])
        self.screen.blit(overlay, (0, 0))
        
        # Текст паузы
        pause_text = self.font.render("PAUSED", True, COLORS['white'])
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30))
        self.screen.blit(pause_text, pause_rect)
        
        resume_text = self.small_font.render("Press P or ESC to Resume", True, COLORS['gray'])
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(resume_text, resume_rect)
        
        menu_text = self.small_font.render("Press M for Menu", True, COLORS['gray'])
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(menu_text, menu_rect)
    
    def draw_game_over(self):
        """Нарисовать экран конца игры"""
        # Полупрозрачный оверлей
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(COLORS['black'])
        self.screen.blit(overlay, (0, 0))
        
        # Текст Game Over
        go_text = self.font.render("GAME OVER", True, COLORS['red'])
        go_rect = go_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(go_text, go_rect)
        
        # Счет
        score_text = self.small_font.render(f"Final Score: {self.score}", True, COLORS['white'])
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(score_text, score_rect)
        
        # Новый рекорд?
        if self.score >= self.high_score and self.score > 0:
            new_record = self.small_font.render("NEW HIGH SCORE!", True, COLORS['yellow'])
            nr_rect = new_record.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
            self.screen.blit(new_record, nr_rect)
        
        # Инструкции
        restart_text = self.small_font.render("Press ENTER to Restart", True, COLORS['white'])
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(restart_text, restart_rect)
        
        menu_text = self.small_font.render("Press M for Menu", True, COLORS['gray'])
        menu_rect = menu_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 110))
        self.screen.blit(menu_text, menu_rect)
    
    def draw(self):
        """Отрисовка игры"""
        if self.state == STATE_MENU:
            self.draw_menu()
        else:
            self.draw_board()
            self.draw_sidebar()
            
            if self.state == STATE_PAUSED:
                self.draw_pause()
            elif self.state == STATE_GAME_OVER:
                self.draw_game_over()
        
        pygame.display.flip()
    
    def run(self):
        """Главный игровой цикл"""
        running = True
        
        while running:
            dt = self.clock.tick(60)  # 60 FPS
            
            # Обработка событий
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    result = self.process_event(event)
                    if result is False:
                        running = False
            
            # Постоянная обработка клавиш (для перемещения)
            self.handle_input()
            
            # Обновление
            self.update(dt)
            
            # Отрисовка
            self.draw()
        
        pygame.quit()


def main():
    """Точка входа"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
