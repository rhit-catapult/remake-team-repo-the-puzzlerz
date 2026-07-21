"""
Word Search Generator & Player  (pygame)
=========================================

Generates solvable word search puzzles across several genres and three
difficulty levels, then lets you play them by dragging across letters.

How it works
------------
1. Pick a genre (word list/topic) and a difficulty.
2. WordSearchGenerator tries to place each word (longest first) at a
   random position/direction, accepting a placement only if every
   overlapping cell already has the same letter (or is empty). Failed
   spots are retried up to 200 times per word before it's skipped.
3. Any cell left empty afterwards is filled with a random letter.
4. Because the generator records exactly which cells each word
   occupies, the puzzle is solvable by construction -- that placement
   list *is* the answer key used to validate your selections.
5. Pygame renders the letter grid and a word list; click-drag in a
   straight line (any of 8 directions, depending on difficulty) over
   letters and release to check your selection against the answer key.

Controls
--------
- Click and drag from the first letter of a word to its last letter,
  then release. A correct straight-line selection highlights the word
  and crosses it off the list (works forwards or backwards).
- Buttons: Reveal (shows all remaining words), New Puzzle (regenerate
  same genre/difficulty), Menu (back to genre/difficulty picker),
  Close (quit). Escape also quits.

Requirements
------------
pip install pygame
"""

import os
import pygame
import random
import string
import subprocess
import sys

# --------------------------------------------------------------------------
# Word banks by genre
# --------------------------------------------------------------------------

WORD_BANKS = {
    "Animals": [
        "LION", "TIGER", "ELEPHANT", "GIRAFFE", "ZEBRA", "MONKEY", "PANDA",
        "KOALA", "RABBIT", "SNAKE", "EAGLE", "SHARK", "WHALE", "DOLPHIN",
        "KANGAROO", "CHEETAH", "GORILLA", "OTTER", "PENGUIN", "FALCON",
        "BEAVER", "CAMEL", "COYOTE", "HEDGEHOG", "OCTOPUS",
    ],
    "Food": [
        "PIZZA", "PASTA", "BURGER", "SALAD", "SUSHI", "TACO", "BREAD",
        "CHEESE", "APPLE", "BANANA", "CHOCOLATE", "COOKIE", "SANDWICH",
        "SOUP", "RICE", "NOODLES", "PANCAKE", "WAFFLE", "YOGURT", "MANGO",
        "BACON", "HONEY", "PEPPER", "AVOCADO", "PRETZEL",
    ],
    "Space": [
        "GALAXY", "PLANET", "COMET", "METEOR", "ROCKET", "ORBIT", "NEBULA",
        "ASTEROID", "SATELLITE", "UNIVERSE", "TELESCOPE", "ECLIPSE",
        "GRAVITY", "ASTRONAUT", "MARS", "JUPITER", "SATURN", "PULSAR",
        "COSMOS", "STARLIGHT", "MOON", "SOLAR", "CRATER", "SHUTTLE", "VENUS",
    ],
    "Sports": [
        "SOCCER", "TENNIS", "HOCKEY", "BASEBALL", "BASKETBALL", "GOLF",
        "RUGBY", "CRICKET", "BOXING", "SWIMMING", "CYCLING", "VOLLEYBALL",
        "SKATING", "WRESTLING", "ARCHERY", "MARATHON", "SURFING", "BOWLING",
        "FENCING", "ROWING", "SPRINT", "REFEREE", "STADIUM", "COACH", "TEAM",
    ],
    "Countries": [
        "FRANCE", "JAPAN", "BRAZIL", "CANADA", "EGYPT", "INDIA", "MEXICO",
        "KENYA", "NORWAY", "GREECE", "SPAIN", "CHINA", "ITALY", "PERU",
        "CHILE", "TURKEY", "POLAND", "SWEDEN", "THAILAND", "IRELAND",
        "PORTUGAL", "VIETNAM", "MOROCCO", "FINLAND", "AUSTRIA",
    ],
    "Technology": [
        "COMPUTER", "INTERNET", "SOFTWARE", "HARDWARE", "ROBOT", "DATABASE",
        "NETWORK", "ALGORITHM", "KEYBOARD", "MONITOR", "SERVER", "WIRELESS",
        "BLUETOOTH", "PROCESSOR", "ENCRYPTION", "INTERFACE", "DOWNLOAD",
        "UPLOAD", "BROWSER", "FIREWALL", "PIXEL", "CODING", "LAPTOP",
        "CLOUD", "SENSOR",
    ],
}

GENRE_ACCENTS = {
    "Animals": (60, 140, 90),
    "Food": (205, 120, 40),
    "Space": (70, 90, 190),
    "Sports": (200, 70, 70),
    "Countries": (150, 100, 190),
    "Technology": (50, 130, 150),
}

DIRECTIONS_ALL = {
    "E": (0, 1), "W": (0, -1), "S": (1, 0), "N": (-1, 0),
    "SE": (1, 1), "SW": (1, -1), "NE": (-1, 1), "NW": (-1, -1),
}

DIFFICULTY_SETTINGS = {
    "Easy":   {"grid_size": 10, "word_count": 6,  "max_len": 7,
               "directions": ["E", "S"]},
    "Medium": {"grid_size": 13, "word_count": 9,  "max_len": 9,
               "directions": ["E", "S", "SE", "NE"]},
    "Hard":   {"grid_size": 16, "word_count": 12, "max_len": 12,
               "directions": list(DIRECTIONS_ALL.keys())},
}

# --------------------------------------------------------------------------
# Word search generation
# --------------------------------------------------------------------------

class WordSearchGenerator:
    """Places words on a grid so that overlapping letters always agree,
    then fills the rest with random letters. Placement records are kept
    as the answer key, so the puzzle is solvable by construction."""

    def __init__(self, words, grid_size, direction_names, seed=None):
        self.grid_size = grid_size
        self.words = [w.upper().strip() for w in words if w.isalpha()]
        self.directions = [DIRECTIONS_ALL[d] for d in direction_names]
        self.rng = random.Random(seed)
        self.grid = {}          # (r, c) -> letter
        self.placements = []    # list of {word, cells: [(r,c), ...]}

    def _fits(self, word, row, col, dr, dc):
        size = self.grid_size
        cells = []
        for i, ch in enumerate(word):
            r, c = row + dr * i, col + dc * i
            if not (0 <= r < size and 0 <= c < size):
                return None
            existing = self.grid.get((r, c))
            if existing is not None and existing != ch:
                return None
            cells.append((r, c))
        return cells

    def _try_place(self, word, tries=200):
        for _ in range(tries):
            dr, dc = self.rng.choice(self.directions)
            row = self.rng.randrange(self.grid_size)
            col = self.rng.randrange(self.grid_size)
            cells = self._fits(word, row, col, dr, dc)
            if cells:
                for (r, c), ch in zip(cells, word):
                    self.grid[(r, c)] = ch
                self.placements.append({"word": word, "cells": cells})
                return True
        return False

    def generate(self, word_count):
        self.grid = {}
        self.placements = []
        pool = list(dict.fromkeys(self.words))  # de-dupe, keep order
        self.rng.shuffle(pool)
        pool.sort(key=lambda w: -len(w))
        placed = 0
        for word in pool:
            if placed >= word_count:
                break
            if len(word) > self.grid_size:
                continue
            if self._try_place(word):
                placed += 1
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                if (r, c) not in self.grid:
                    self.grid[(r, c)] = self.rng.choice(string.ascii_uppercase)
        return placed


def build_puzzle(genre, difficulty, seed=None):
    settings = DIFFICULTY_SETTINGS[difficulty]
    pool = [w for w in WORD_BANKS[genre] if len(w) <= settings["max_len"]]
    gen = WordSearchGenerator(pool, settings["grid_size"], settings["directions"], seed=seed)
    gen.generate(settings["word_count"])
    return gen


# --------------------------------------------------------------------------
# Pygame application
# --------------------------------------------------------------------------

pygame.init()
pygame.display.set_caption("Word Search Generator")

WIDTH, HEIGHT = 1150, 780
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

FONT_SM = pygame.font.SysFont("arial", 15)
FONT_MD = pygame.font.SysFont("arial", 18)
FONT_LG = pygame.font.SysFont("arial", 26, bold=True)
FONT_CELL = pygame.font.SysFont("consolas", 20, bold=True)
if not FONT_CELL.get_bold():
    FONT_CELL = pygame.font.SysFont("couriernew", 20, bold=True)

COL_BG = (245, 244, 238)
COL_GRID_BG = (255, 255, 255)
COL_LINE = (225, 225, 220)
COL_TEXT = (25, 25, 25)
COL_PANEL = (255, 255, 255)
COL_PANEL_BORDER = (210, 210, 205)
COL_BUTTON = (70, 110, 200)
COL_BUTTON_HOVER = (95, 135, 225)
COL_BUTTON_TEXT = (255, 255, 255)
COL_CLOSE = (205, 70, 70)
COL_CLOSE_HOVER = (225, 95, 95)
COL_SELECT_DRAG = (255, 210, 90)
COL_FOUND_STRIKE = (150, 150, 150)

FOUND_PALETTE = [
    (255, 179, 179), (179, 219, 255), (190, 255, 179), (255, 236, 150),
    (223, 179, 255), (255, 200, 150), (150, 235, 235), (240, 179, 220),
]


class Button:
    def __init__(self, rect, text, font=FONT_MD, color=None, hover_color=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.color = color or COL_BUTTON
        self.hover_color = hover_color or COL_BUTTON_HOVER
        self.selected = False

    def draw(self, surf):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.hover_color if (hovered or self.selected) else self.color
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        if self.selected:
            pygame.draw.rect(surf, (30, 30, 30), self.rect, 2, border_radius=8)
        label = self.font.render(self.text, True, COL_BUTTON_TEXT)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


class WordSearchGame:
    CELL = 34

    def __init__(self):
        self.state = "MENU"
        self.genre = None
        self.difficulty = None
        self.gen = None
        self.found_words = {}      # word -> (cells, color)
        self.dragging = False
        self.drag_start = None
        self.drag_path = []
        self.status_msg = ""
        self.status_color = COL_TEXT
        self.status_timer = 0
        self.origin = (60, 130)
        self.start_ticks = 0
        self.elapsed_ms = 0

        self.genre_buttons = {}
        gx, gy = 90, 230
        for i, name in enumerate(WORD_BANKS.keys()):
            row, col = divmod(i, 3)
            btn = Button((gx + col * 260, gy + row * 65, 240, 50), name, FONT_MD)
            self.genre_buttons[name] = btn

        self.difficulty_buttons = {}
        dy = 420
        for i, name in enumerate(["Easy", "Medium", "Hard"]):
            btn = Button((WIDTH // 2 - 400 + i * 280, dy, 240, 50), name, FONT_MD)
            self.difficulty_buttons[name] = btn

        self.btn_start = Button((WIDTH // 2 - 120, 520, 240, 55), "Start Puzzle", FONT_LG)
        self.btn_close_menu = Button((WIDTH - 40 - 90, 20, 90, 34), "Close", FONT_MD,
                                      color=COL_CLOSE, hover_color=COL_CLOSE_HOVER)

        self.btn_new = Button((0, 0, 150, 36), "New Puzzle")
        self.btn_reveal = Button((0, 0, 110, 36), "Reveal")
        self.btn_menu = Button((0, 0, 110, 36), "Menu")
        self.btn_close = Button((0, 0, 90, 36), "Close", FONT_MD,
                                 color=COL_CLOSE, hover_color=COL_CLOSE_HOVER)

    # ---------------------------------------------------------------- setup
    def new_puzzle(self):
        self.gen = build_puzzle(self.genre, self.difficulty)
        self.found_words = {}
        self.dragging = False
        self.drag_start = None
        self.drag_path = []
        self.state = "PLAYING"
        self.start_ticks = pygame.time.get_ticks()
        self.elapsed_ms = 0

        size = self.gen.grid_size
        grid_pixel = size * self.CELL
        ox = 60
        oy = 130 + max(0, (HEIGHT - 200 - grid_pixel) // 2)
        self.origin = (ox, oy)
        self.set_status(f"{self.genre} \u2014 {self.difficulty}: find {len(self.gen.placements)} words.",
                         COL_TEXT)

    def set_status(self, msg, color=COL_TEXT):
        self.status_msg = msg
        self.status_color = color
        self.status_timer = 200

    # -------------------------------------------------------------- helpers
    def cell_to_pixel_center(self, r, c):
        ox, oy = self.origin
        return ox + c * self.CELL + self.CELL // 2, oy + r * self.CELL + self.CELL // 2

    def pixel_to_cell(self, x, y):
        ox, oy = self.origin
        col = (x - ox) // self.CELL
        row = (y - oy) // self.CELL
        return int(row), int(col)

    def in_grid(self, r, c):
        return 0 <= r < self.gen.grid_size and 0 <= c < self.gen.grid_size

    def path_between(self, start, end):
        (r0, c0), (r1, c1) = start, end
        dr, dc = r1 - r0, c1 - c0
        step_r = (dr > 0) - (dr < 0)
        step_c = (dc > 0) - (dc < 0)
        length = max(abs(dr), abs(dc))
        path = [(r0 + step_r * i, c0 + step_c * i) for i in range(length + 1)]
        return [p for p in path if self.in_grid(*p)]

    def next_found_color(self):
        return FOUND_PALETTE[len(self.found_words) % len(FOUND_PALETTE)]

    # ---------------------------------------------------------------- input
    def start_drag(self, pos):
        r, c = self.pixel_to_cell(*pos)
        if self.in_grid(r, c):
            self.dragging = True
            self.drag_start = (r, c)
            self.drag_path = [(r, c)]

    def update_drag(self, pos):
        if not self.dragging:
            return
        r, c = self.pixel_to_cell(*pos)
        r = max(0, min(self.gen.grid_size - 1, r))
        c = max(0, min(self.gen.grid_size - 1, c))
        self.drag_path = self.path_between(self.drag_start, (r, c))

    def end_drag(self):
        if not self.dragging:
            return
        self.dragging = False
        path = self.drag_path
        self.drag_path = []
        if len(path) < 2:
            return
        for p in self.gen.placements:
            word = p["word"]
            if word in self.found_words:
                continue
            if path == p["cells"] or path == list(reversed(p["cells"])):
                self.found_words[word] = (p["cells"], self.next_found_color())
                self.set_status(f'Found "{word}"!', (30, 130, 30))
                if len(self.found_words) == len(self.gen.placements):
                    self.state = "WON"
                    self.elapsed_ms = pygame.time.get_ticks() - self.start_ticks
                    self.set_status("All words found!", (30, 130, 30))
                    try:
                        congrats_path = os.path.join(os.path.dirname(__file__), "CongratsScreen.py")
                        env = os.environ.copy()
                        env["PUZZLER_GAME_TYPE"] = "word_search"
                        subprocess.Popen([sys.executable, congrats_path], env=env)
                    except Exception:
                        pass
                    pygame.quit()
                    sys.exit()
                return

    def reveal(self):
        for p in self.gen.placements:
            if p["word"] not in self.found_words:
                self.found_words[p["word"]] = (p["cells"], (210, 210, 210))
        self.set_status("Remaining words revealed.", COL_TEXT)

    # ---------------------------------------------------------------- draw
    def draw_menu(self):
        screen.fill(COL_BG)
        title = FONT_LG.render("Word Search Generator", True, COL_TEXT)
        screen.blit(title, title.get_rect(center=(WIDTH // 2, 60)))
        sub = FONT_MD.render("1. Pick a genre   2. Pick a difficulty   3. Start",
                              True, (90, 90, 90))
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, 100)))

        genre_hd = FONT_MD.render("Genre", True, COL_TEXT)
        screen.blit(genre_hd, (90, 195))
        for name, btn in self.genre_buttons.items():
            btn.selected = (name == self.genre)
            btn.color = GENRE_ACCENTS.get(name, COL_BUTTON)
            btn.hover_color = tuple(min(255, v + 25) for v in btn.color)
            btn.draw(screen)

        diff_hd = FONT_MD.render("Difficulty", True, COL_TEXT)
        screen.blit(diff_hd, (WIDTH // 2 - 400, 388))
        for name, btn in self.difficulty_buttons.items():
            btn.selected = (name == self.difficulty)
            btn.draw(screen)

        self.btn_start.color = COL_BUTTON if (self.genre and self.difficulty) else (180, 180, 180)
        self.btn_start.hover_color = COL_BUTTON_HOVER if (self.genre and self.difficulty) else (180, 180, 180)
        self.btn_start.draw(screen)

        if not (self.genre and self.difficulty):
            hint = FONT_SM.render("Choose a genre and difficulty to enable Start.",
                                   True, (140, 140, 140))
            screen.blit(hint, hint.get_rect(center=(WIDTH // 2, self.btn_start.rect.bottom + 22)))

        self.btn_close_menu.draw(screen)

    def draw_grid(self):
        size = self.gen.grid_size
        ox, oy = self.origin
        grid_rect = pygame.Rect(ox, oy, size * self.CELL, size * self.CELL)
        pygame.draw.rect(screen, COL_GRID_BG, grid_rect)
        for r in range(size):
            for c in range(size):
                rect = pygame.Rect(ox + c * self.CELL, oy + r * self.CELL, self.CELL, self.CELL)
                pygame.draw.rect(screen, COL_LINE, rect, 1)

        # persistent highlights for found words
        for word, (cells, color) in self.found_words.items():
            self.draw_selection_line(cells, color, width=self.CELL - 6)

        # live drag highlight
        if self.dragging and len(self.drag_path) >= 1:
            self.draw_selection_line(self.drag_path, COL_SELECT_DRAG, width=self.CELL - 10)

        # letters on top
        for r in range(size):
            for c in range(size):
                letter = self.gen.grid[(r, c)]
                x, y = self.cell_to_pixel_center(r, c)
                lbl = FONT_CELL.render(letter, True, COL_TEXT)
                screen.blit(lbl, lbl.get_rect(center=(x, y)))

        pygame.draw.rect(screen, (120, 120, 120), grid_rect, 2)

    def draw_selection_line(self, cells, color, width):
        if len(cells) == 1:
            x, y = self.cell_to_pixel_center(*cells[0])
            pygame.draw.circle(screen, color, (x, y), width // 2)
            return
        start = self.cell_to_pixel_center(*cells[0])
        end = self.cell_to_pixel_center(*cells[-1])
        pygame.draw.line(screen, color, start, end, width)
        pygame.draw.circle(screen, color, start, width // 2)
        pygame.draw.circle(screen, color, end, width // 2)

    def draw_word_panel(self):
        size = self.gen.grid_size
        panel_x = self.origin[0] + size * self.CELL + 40
        panel_w = WIDTH - panel_x - 30
        panel_rect = pygame.Rect(panel_x, 130, panel_w, HEIGHT - 260)
        pygame.draw.rect(screen, COL_PANEL, panel_rect, border_radius=8)
        pygame.draw.rect(screen, COL_PANEL_BORDER, panel_rect, 1, border_radius=8)

        accent = GENRE_ACCENTS.get(self.genre, COL_BUTTON)
        hd = FONT_MD.render(f"Find these words ({len(self.found_words)}/{len(self.gen.placements)})",
                             True, accent)
        screen.blit(hd, (panel_rect.left + 14, panel_rect.top + 12))

        y = panel_rect.top + 46
        for p in sorted(self.gen.placements, key=lambda p: p["word"]):
            word = p["word"]
            found = word in self.found_words
            color = COL_FOUND_STRIKE if found else COL_TEXT
            lbl = FONT_SM.render(word, True, color)
            screen.blit(lbl, (panel_rect.left + 20, y))
            if found:
                pygame.draw.line(screen, COL_FOUND_STRIKE,
                                  (panel_rect.left + 18, y + lbl.get_height() // 2),
                                  (panel_rect.left + 18 + lbl.get_width(), y + lbl.get_height() // 2), 2)
            y += 26
            if y > panel_rect.bottom - 20:
                break

        # timer box below the word list
        timer_rect = pygame.Rect(panel_x, panel_rect.bottom + 16, panel_w, 60)
        pygame.draw.rect(screen, COL_PANEL, timer_rect, border_radius=8)
        pygame.draw.rect(screen, COL_PANEL_BORDER, timer_rect, 1, border_radius=8)
        if self.state != "WON":
            self.elapsed_ms = pygame.time.get_ticks() - self.start_ticks
        secs = self.elapsed_ms // 1000
        time_str = f"{secs // 60:02d}:{secs % 60:02d}"
        t_lbl = FONT_LG.render(time_str, True, COL_TEXT)
        screen.blit(t_lbl, t_lbl.get_rect(center=timer_rect.center))

    def draw_topbar(self):
        title = FONT_LG.render(f"Word Search \u2014 {self.genre} ({self.difficulty})", True, COL_TEXT)
        screen.blit(title, (40, 20))

        bx = WIDTH - 40
        for btn in (self.btn_close, self.btn_menu, self.btn_new, self.btn_reveal):
            btn.rect.right = bx
            btn.rect.top = 30
            bx -= btn.rect.width + 10
        for btn in (self.btn_reveal, self.btn_new, self.btn_menu, self.btn_close):
            btn.draw(screen)

        if self.status_timer > 0:
            self.status_timer -= 1
            msg = FONT_MD.render(self.status_msg, True, self.status_color)
            screen.blit(msg, (40, 68))

    def draw_playing(self):
        screen.fill(COL_BG)
        self.draw_topbar()
        self.draw_grid()
        self.draw_word_panel()
        hint = FONT_SM.render("Click and drag across letters to select a word, then release.",
                               True, (110, 110, 110))
        screen.blit(hint, (40, HEIGHT - 26))


    # --------------------------------------------------------------- events
    def open_launcher(self):
        try:
            launcher_path = os.path.join(os.path.dirname(__file__), "PuzzlerzGame.py")
            subprocess.Popen([sys.executable, launcher_path])
        except Exception:
            pass

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            pygame.quit()
            sys.exit()

        if self.state == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_close_menu.clicked(event.pos):
                    self.open_launcher()
                    pygame.quit()
                    sys.exit()
                for name, btn in self.genre_buttons.items():
                    if btn.clicked(event.pos):
                        self.genre = name
                for name, btn in self.difficulty_buttons.items():
                    if btn.clicked(event.pos):
                        self.difficulty = name
                if self.genre and self.difficulty and self.btn_start.clicked(event.pos):
                    self.new_puzzle()
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.btn_close.clicked(event.pos):
                self.open_launcher()
                pygame.quit()
                sys.exit()
            if self.btn_menu.clicked(event.pos):
                self.state = "MENU"
                return
            if self.btn_new.clicked(event.pos):
                self.new_puzzle()
                return
            if self.btn_reveal.clicked(event.pos):
                self.reveal()
                return
            if self.state == "PLAYING":
                self.start_drag(event.pos)

        elif event.type == pygame.MOUSEMOTION:
            if self.state == "PLAYING":
                self.update_drag(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.state == "PLAYING":
                self.end_drag()

        elif event.type == pygame.KEYDOWN:
            if self.state == "WON":
                if event.key == pygame.K_n:
                    self.new_puzzle()
                elif event.key == pygame.K_m:
                    self.state = "MENU"

    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        else:
            self.draw_playing()



def main():
    game = WordSearchGame()
    while True:
        for event in pygame.event.get():
            game.handle_event(event)
        game.draw()
        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()