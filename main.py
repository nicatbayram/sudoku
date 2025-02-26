import pygame
import random
import time
import sys
import math

# Initialize pygame
pygame.init()

# Screen dimensions
WIDTH, HEIGHT = 600, 750
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Modern Sudoku")

# Colors
class Colors:
    def __init__(self, is_dark_mode=False):
        self.update_theme(is_dark_mode)
    
    def update_theme(self, is_dark_mode):
        if is_dark_mode:
            self.bg_primary = (26, 26, 46)
            self.bg_secondary = (35, 35, 56)
            self.text_primary = (224, 224, 224)
            self.text_secondary = (176, 176, 176)
            self.accent = (107, 138, 253)
            self.accent_light = (45, 57, 86)
            self.grid_line_light = (42, 42, 69)
            self.grid_line_dark = (64, 64, 96)
            self.cell_highlight = (45, 55, 72)
            self.shadow = (0, 0, 0, 51)
            self.cell_given = (208, 208, 208)
            self.cell_user = (125, 157, 255)
        else:
            self.bg_primary = (249, 249, 251)
            self.bg_secondary = (255, 255, 255)
            self.text_primary = (51, 51, 51)
            self.text_secondary = (102, 102, 102)
            self.accent = (107, 138, 253)
            self.accent_light = (224, 231, 255)
            self.grid_line_light = (224, 224, 224)
            self.grid_line_dark = (176, 176, 176)
            self.cell_highlight = (240, 244, 255)
            self.shadow = (0, 0, 0, 18)
            self.cell_given = (74, 85, 104)
            self.cell_user = (107, 138, 253)

# Global variables
colors = Colors()
clock = pygame.time.Clock()
FPS = 60

# Fonts
font_large = pygame.font.SysFont('Arial', 36, bold=True)
font_medium = pygame.font.SysFont('Arial', 24)
font_small = pygame.font.SysFont('Arial', 16)
font_title = pygame.font.SysFont('Arial', 48, bold=True)

# Game state
difficulty_levels = ["Easy", "Medium", "Hard", "Expert"]
current_difficulty = 1
is_dark_mode = False
game_time = 0
start_time = time.time()
selected_cell = None
pencil_mode = False
hints_remaining = 3
game_state = "start_screen"  # Can be "start_screen" or "playing"

# Sample board (in a real game, this would be generated)
def generate_board(difficulty):
    # This is a simplified version - a real implementation would generate valid Sudoku puzzles
    # based on the difficulty level
    board = [[0 for _ in range(9)] for _ in range(9)]
    solution = [[0 for _ in range(9)] for _ in range(9)]
    
    # Fill solution with a valid Sudoku
    base = 3
    side = base * base
    
    # Helper function to create a valid solution
    def pattern(r, c):
        return (base * (r % base) + r // base + c) % side
    
    # Create a valid solution
    for r in range(side):
        for c in range(side):
            solution[r][c] = pattern(r, c) + 1
    
    # Shuffle the solution for more randomness
    def shuffle_solution():
        # Shuffle rows within each band
        for band in range(base):
            rows = list(range(band * base, (band + 1) * base))
            random.shuffle(rows)
            solution_copy = [row[:] for row in solution]
            for r1, r2 in enumerate(rows):
                solution[band * base + r1] = solution_copy[r2]
    
    shuffle_solution()
    
    # Copy solution to board
    for r in range(side):
        for c in range(side):
            board[r][c] = solution[r][c]
    
    # Remove numbers based on difficulty
    cells_to_remove = {
        0: 30,    # Easy
        1: 40,    # Medium
        2: 50,    # Hard
        3: 60     # Expert
    }[difficulty]
    
    # Randomly remove cells
    cells = [(r, c) for r in range(side) for c in range(side)]
    random.shuffle(cells)
    
    for i in range(cells_to_remove):
        if i < len(cells):
            r, c = cells[i]
            board[r][c] = 0
    
    return board, solution

board, solution = generate_board(current_difficulty)
original_board = [[board[r][c] for c in range(9)] for r in range(9)]
notes = [[set() for _ in range(9)] for _ in range(9)]

# UI Components
class Button:
    def __init__(self, x, y, width, height, text, action=None, icon=None, is_toggle=False, toggled=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.icon = icon
        self.is_toggle = is_toggle
        self.toggled = toggled
        self.hovered = False
        self.animation_progress = 0
    
    def draw(self):
        # Background with shadow effect
        shadow_rect = self.rect.copy()
        shadow_rect.y += 2
        pygame.draw.rect(screen, (*colors.shadow[:3], 128), shadow_rect, border_radius=12)
        
        # Main button background
        color = colors.accent if self.toggled else colors.bg_secondary
        hover_intensity = min(1.0, self.animation_progress)
        if self.hovered and not self.toggled:
            r = colors.bg_secondary[0] + (colors.accent_light[0] - colors.bg_secondary[0]) * hover_intensity
            g = colors.bg_secondary[1] + (colors.accent_light[1] - colors.bg_secondary[1]) * hover_intensity
            b = colors.bg_secondary[2] + (colors.accent_light[2] - colors.bg_secondary[2]) * hover_intensity
            color = (r, g, b)
        
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        
        # Border
        border_color = colors.accent if self.toggled else colors.grid_line_light
        pygame.draw.rect(screen, border_color, self.rect, width=1, border_radius=12)
        
        # Text
        text_color = colors.bg_primary if self.toggled else colors.text_primary
        text_surf = font_small.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def update(self, mouse_pos, mouse_clicked):
        prev_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        # Animate hover state
        if self.hovered and not prev_hovered:
            self.animation_progress = 0
        elif not self.hovered and prev_hovered:
            self.animation_progress = 1
        
        if self.hovered:
            self.animation_progress = min(1.0, self.animation_progress + 0.1)
        else:
            self.animation_progress = max(0.0, self.animation_progress - 0.1)
        
        if mouse_clicked and self.hovered and self.action:
            if self.is_toggle:
                self.toggled = not self.toggled
            return self.action()
        return False

class StartButton(Button):
    def __init__(self, x, y, width, height, text, difficulty, action=None):
        super().__init__(x, y, width, height, text, action)
        self.difficulty = difficulty
        self.scale_factor = 1.0
        self.original_rect = self.rect.copy()
    
    def draw(self):
        # Animated scaling effect
        scaled_width = int(self.original_rect.width * self.scale_factor)
        scaled_height = int(self.original_rect.height * self.scale_factor)
        self.rect.width = scaled_width
        self.rect.height = scaled_height
        self.rect.centerx = self.original_rect.centerx
        self.rect.centery = self.original_rect.centery
        
        # Shadow
        shadow_rect = self.rect.copy()
        shadow_rect.y += 3
        pygame.draw.rect(screen, (*colors.shadow[:3], 128), shadow_rect, border_radius=15)
        
        # Button background
        color = colors.accent if self.hovered else colors.bg_secondary
        pygame.draw.rect(screen, color, self.rect, border_radius=15)
        
        # Inner gradient effect
        gradient_rect = self.rect.inflate(-10, -10)
        gradient_color = colors.accent_light if self.hovered else colors.bg_primary
        pygame.draw.rect(screen, gradient_color, gradient_rect, border_radius=12)
        
        # Text
        text_color = colors.text_primary
        diff_text = f"{self.text} - {difficulty_levels[self.difficulty]}"
        text_surf = font_medium.render(diff_text, True, text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def update(self, mouse_pos, mouse_clicked):
        prev_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        # Animate hover
        target_scale = 1.05 if self.hovered else 1.0
        self.scale_factor += (target_scale - self.scale_factor) * 0.1
        
        if mouse_clicked and self.hovered and self.action:
            return self.action(self.difficulty)
        return False

# Create UI buttons
new_game_btn = Button(WIDTH - 140, 20, 120, 40, "New Game", action=lambda: new_game())
theme_btn = Button(WIDTH - 140, 70, 120, 40, "Dark Mode", action=lambda: toggle_theme(), is_toggle=is_dark_mode)
hint_btn = Button(WIDTH - 140, 120, 120, 40, f"Hints: {hints_remaining}", action=lambda: use_hint())
pencil_btn = Button(WIDTH - 140, 170, 120, 40, "Pencil Mode", action=lambda: toggle_pencil_mode(), is_toggle=pencil_mode)

difficulty_btns = []
for i, diff in enumerate(difficulty_levels):
    btn = Button(20 + i * 110, HEIGHT - 60, 100, 40, diff, 
                action=lambda d=i: set_difficulty(d), 
                is_toggle=True, 
                toggled=(i == current_difficulty))
    difficulty_btns.append(btn)

# Start screen buttons
start_screen_btns = []
for i, diff in enumerate(range(4)):
    y_pos = HEIGHT // 2 - 100 + i * 120
    btn = StartButton(WIDTH // 2, y_pos, 300, 80, "Start Game", diff, 
                    action=lambda d=diff: start_game_with_difficulty(d))
    start_screen_btns.append(btn)

# Mode toggle for start screen
dark_mode_toggle = Button(WIDTH - 140, 20, 120, 40, "Dark Mode", 
                        action=lambda: toggle_theme(), 
                        is_toggle=is_dark_mode)

# Game functions
def new_game():
    global board, solution, original_board, notes, start_time, game_time, hints_remaining
    board, solution = generate_board(current_difficulty)
    original_board = [[board[r][c] for c in range(9)] for r in range(9)]
    notes = [[set() for _ in range(9)] for _ in range(9)]
    start_time = time.time()
    game_time = 0
    hints_remaining = 3
    hint_btn.text = f"Hints: {hints_remaining}"

def toggle_theme():
    global is_dark_mode
    is_dark_mode = not is_dark_mode
    colors.update_theme(is_dark_mode)
    theme_btn.text = "Light Mode" if is_dark_mode else "Dark Mode"
    dark_mode_toggle.text = "Light Mode" if is_dark_mode else "Dark Mode"
    dark_mode_toggle.toggled = is_dark_mode

def set_difficulty(diff_index):
    global current_difficulty
    if current_difficulty != diff_index:
        current_difficulty = diff_index
        for i, btn in enumerate(difficulty_btns):
            btn.toggled = (i == current_difficulty)
        new_game()

def start_game_with_difficulty(diff_index):
    global current_difficulty, game_state
    current_difficulty = diff_index
    for i, btn in enumerate(difficulty_btns):
        btn.toggled = (i == current_difficulty)
    new_game()
    game_state = "playing"
    return True

def toggle_pencil_mode():
    global pencil_mode
    pencil_mode = not pencil_mode
    pencil_btn.toggled = pencil_mode

def use_hint():
    global hints_remaining, board
    if hints_remaining > 0 and selected_cell:
        row, col = selected_cell
        if board[row][col] == 0:
            board[row][col] = solution[row][col]
            hints_remaining -= 1
            hint_btn.text = f"Hints: {hints_remaining}"
            notes[row][col] = set()

def format_time(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def draw_board():
    # Draw board background with shadow
    board_rect = pygame.Rect(50, 100, 500, 500)
    shadow_rect = board_rect.copy()
    shadow_rect.x += 5
    shadow_rect.y += 5
    pygame.draw.rect(screen, (*colors.shadow[:3], 76), shadow_rect, border_radius=15)
    pygame.draw.rect(screen, colors.bg_secondary, board_rect, border_radius=15)
    
    cell_size = 500 // 9
    for i in range(10):
        line_weight = 3 if i % 3 == 0 else 1
        line_color = colors.grid_line_dark if i % 3 == 0 else colors.grid_line_light
        
        # Horizontal lines
        pygame.draw.line(screen, line_color, 
                        (50, 100 + i * cell_size), 
                        (550, 100 + i * cell_size), line_weight)
        
        # Vertical lines
        pygame.draw.line(screen, line_color, 
                        (50 + i * cell_size, 100), 
                        (50 + i * cell_size, 600), line_weight)
    
    # Draw cells
    for row in range(9):
        for col in range(9):
            cell_rect = pygame.Rect(50 + col * cell_size, 100 + row * cell_size, cell_size, cell_size)
            
            # Highlight selected cell and related cells
            if selected_cell and (row == selected_cell[0] or col == selected_cell[1] or 
                                (row // 3 == selected_cell[0] // 3 and col // 3 == selected_cell[1] // 3)):
                pygame.draw.rect(screen, colors.cell_highlight, cell_rect)
            
            # Highlight selected cell
            if selected_cell and row == selected_cell[0] and col == selected_cell[1]:
                pygame.draw.rect(screen, colors.accent_light, cell_rect)
            
            # Draw number or notes
            if board[row][col] != 0:
                is_original = original_board[row][col] != 0
                number_color = colors.cell_given if is_original else colors.cell_user
                number_surf = font_large.render(str(board[row][col]), True, number_color)
                number_rect = number_surf.get_rect(center=(cell_rect.centerx, cell_rect.centery))
                screen.blit(number_surf, number_rect)
            elif notes[row][col]:
                note_size = cell_size // 3
                for note in notes[row][col]:
                    note_surf = font_small.render(str(note), True, colors.text_secondary)
                    note_x = cell_rect.x + ((note-1) % 3) * note_size + note_size // 2
                    note_y = cell_rect.y + ((note-1) // 3) * note_size + note_size // 2
                    note_rect = note_surf.get_rect(center=(note_x, note_y))
                    screen.blit(note_surf, note_rect)

def draw_ui():
    # Draw game header
    title_surf = font_large.render("Modern Sudoku", True, colors.accent)
    screen.blit(title_surf, (20, 20))
    
    difficulty_surf = font_medium.render(f"Difficulty: {difficulty_levels[current_difficulty]}", True, colors.text_secondary)
    screen.blit(difficulty_surf, (20, 70))
    
    # Draw timer
    time_surf = font_medium.render(f"Time: {format_time(game_time)}", True, colors.text_primary)
    time_rect = time_surf.get_rect(midtop=(WIDTH//2, 40))
    screen.blit(time_surf, time_rect)
    
    # Draw buttons
    new_game_btn.draw()
    theme_btn.draw()
    hint_btn.draw()
    pencil_btn.draw()
    
    for btn in difficulty_btns:
        btn.draw()
    
    # Draw number pad
    pad_width = 400
    pad_rect = pygame.Rect((WIDTH - pad_width) // 2, 620, pad_width, 60)
    pygame.draw.rect(screen, colors.bg_secondary, pad_rect, border_radius=10)
    pygame.draw.rect(screen, colors.grid_line_light, pad_rect, width=1, border_radius=10)
    
    pad_cell_size = pad_width // 9
    for i in range(9):
        cell_rect = pygame.Rect(pad_rect.x + i * pad_cell_size, pad_rect.y, pad_cell_size, 60)
        number_surf = font_medium.render(str(i+1), True, colors.text_primary)
        number_rect = number_surf.get_rect(center=cell_rect.center)
        screen.blit(number_surf, number_rect)

def draw_start_screen():
    # Draw title with animation
    current_time = pygame.time.get_ticks() / 1000
    wave_height = 5
    wave_speed = 2
    
    title_text = "Modern Sudoku"
    base_y = HEIGHT // 4
    
    for i, char in enumerate(title_text):
        # Calculate wavy position
        offset_y = math.sin(current_time * wave_speed + i * 0.3) * wave_height
        char_surf = font_title.render(char, True, colors.accent)
        char_rect = char_surf.get_rect()
        char_rect.x = WIDTH // 2 - len(title_text) * 15 + i * 30
        char_rect.y = base_y + offset_y
        screen.blit(char_surf, char_rect)
    
    # Draw subtitle
    subtitle = "Select Difficulty"
    subtitle_surf = font_large.render(subtitle, True, colors.text_secondary)
    subtitle_rect = subtitle_surf.get_rect(center=(WIDTH // 2, base_y + 80))
    screen.blit(subtitle_surf, subtitle_rect)
    
    # Draw buttons
    for btn in start_screen_btns:
        btn.draw()
    
    # Draw theme toggle
    dark_mode_toggle.draw()
    
    # Draw decorative elements
    # Grid pattern in background
    cell_size = 40
    for row in range(HEIGHT // cell_size + 1):
        for col in range(WIDTH // cell_size + 1):
            if random.random() < 0.1:  # Only draw some cells for a sparse effect
                alpha = random.randint(5, 20)  # Very subtle transparency
                cell_rect = pygame.Rect(col * cell_size, row * cell_size, cell_size, cell_size)
                cell_surface = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                pygame.draw.rect(cell_surface, (*colors.accent, alpha), 
                               (0, 0, cell_size, cell_size), 1, border_radius=3)
                screen.blit(cell_surface, cell_rect)

def check_win():
    for row in range(9):
        for col in range(9):
            if board[row][col] != solution[row][col]:
                return False
    return True

def show_win_message():
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 128))
    screen.blit(overlay, (0, 0))
    
    message_surf = font_large.render("Puzzle Solved!", True, (255, 255, 255))
    time_surf = font_medium.render(f"Time: {format_time(game_time)}", True, (220, 220, 220))
    
    message_rect = message_surf.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
    time_rect = time_surf.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))
    
    screen.blit(message_surf, message_rect)
    screen.blit(time_surf, time_rect)
    
    # Add return to start screen button
    return_btn = Button(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50, "Return to Menu", 
                      action=lambda: return_to_menu())
    return_btn.draw()
    
    pygame.display.flip()
    
    # Wait for user interaction
    btn_clicked = False
    while not btn_clicked:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if return_btn.rect.collidepoint(mouse_pos):
                    btn_clicked = True
                    return_to_menu()
        
        # Update button
        return_btn.update(pygame.mouse.get_pos(), False)
        return_btn.draw()
        pygame.display.flip()
        clock.tick(FPS)

def return_to_menu():
    global game_state
    game_state = "start_screen"
    return True

# Main game loop
running = True
win_shown = False
while running:
    mouse_clicked = False
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_clicked = True
            
            if game_state == "playing":
                # Check if clicked on board
                mouse_pos = pygame.mouse.get_pos()
                board_rect = pygame.Rect(50, 100, 500, 500)
                if board_rect.collidepoint(mouse_pos):
                    cell_size = 500 // 9
                    col = (mouse_pos[0] - 50) // cell_size
                    row = (mouse_pos[1] - 100) // cell_size
                    if 0 <= row < 9 and 0 <= col < 9:
                        selected_cell = (row, col)
                
                # Check if clicked on number pad
                pad_rect = pygame.Rect((WIDTH - 400) // 2, 620, 400, 60)
                if pad_rect.collidepoint(mouse_pos) and selected_cell:
                    pad_cell_size = 400 // 9
                    num = (mouse_pos[0] - pad_rect.x) // pad_cell_size + 1
                    row, col = selected_cell
                    
                    if 1 <= num <= 9 and original_board[row][col] == 0:
                        if pencil_mode:
                            if num in notes[row][col]:
                                notes[row][col].remove(num)
                            else:
                                notes[row][col].add(num)
                        else:
                            if board[row][col] == num:
                                board[row][col] = 0
                            else:
                                board[row][col] = num
                                notes[row][col] = set()  # Clear notes when entering a number
        
        if event.type == pygame.KEYDOWN and game_state == "playing":
            if selected_cell:
                row, col = selected_cell
                if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                    if original_board[row][col] == 0:
                        board[row][col] = 0
                        notes[row][col] = set()
                elif event.key == pygame.K_n:
                    toggle_pencil_mode()
                elif event.key == pygame.K_h:
                    use_hint()
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, 
                                pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9] and original_board[row][col] == 0:
                    num = event.key - pygame.K_0  # Convert key to number
                    if pencil_mode:
                        if num in notes[row][col]:
                            notes[row][col].remove(num)
                        else:
                            notes[row][col].add(num)
                    else:
                        if board[row][col] == num:
                            board[row][col] = 0
                        else:
                            board[row][col] = num
                            notes[row][col] = set()  # Clear notes when entering a number
    
    # Update game time
    if game_state == "playing" and not win_shown:
        game_time = time.time() - start_time
    
    # Update UI button states
    mouse_pos = pygame.mouse.get_pos()
    
    if game_state == "playing":
        for btn in [new_game_btn, theme_btn, hint_btn, pencil_btn] + difficulty_btns:
            btn.update(mouse_pos, mouse_clicked)
    else:  # Start screen
        dark_mode_toggle.update(mouse_pos, mouse_clicked)
        for btn in start_screen_btns:
            btn.update(mouse_pos, mouse_clicked)
    
    # Draw screen
    screen.fill(colors.bg_primary)
    
    if game_state == "playing":
        draw_board()
        draw_ui()
        
        # Check for win
        if check_win() and not win_shown:
            win_shown = True
            show_win_message()
            win_shown = False
    else:
        draw_start_screen()
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()