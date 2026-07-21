"""
Crossword Puzzle Generator & Player  (pygame)
==============================================

Generates solvable crossword puzzles at three difficulty levels
(Easy / Medium / Hard) and lets you play them interactively.

How it works
------------
1. A word list (word + clue) is chosen for the selected difficulty.
2. CrosswordGenerator places the longest word first, then repeatedly
   tries to place remaining words so that every new word crosses at
   least one already-placed word at a matching letter, with no illegal
   adjacent-letter collisions. Several full attempts are generated and
   the one that successfully places the most words is kept.
3. Because every word is placed letter-for-letter into a shared grid,
   the puzzle is solvable by construction -- the generator itself is
   the solution key.
4. Pygame then renders the (cropped) grid with numbered cells and a
   clue list, and lets you click cells / type letters to solve it.

Controls
--------
- Click a cell to select it (click again to flip between Across/Down).
- Type a letter to fill it in; typing auto-advances to the next cell.
- Backspace clears the current cell and steps back.
- Arrow keys move the selection.
- Click a clue in the side panel to jump to that word.
- Buttons: Check (highlights right/wrong), Reveal (fills the answer),
  Clear (empties your input), New Puzzle (back to the difficulty menu).

Requirements
------------
pip install pygame
"""

import os
import pygame
import random
import subprocess
import sys

# --------------------------------------------------------------------------
# Word banks (word, clue) grouped by difficulty
# --------------------------------------------------------------------------

WORD_BANKS = {
    "Easy": [
        ("CAT", "Purring pet"),
        ("DOG", "Man's best friend"),
        ("SUN", "Star at the center of our solar system"),
        ("MOON", "Earth's only natural satellite"),
        ("STAR", "Twinkling night-sky object"),
        ("TREE", "Tall plant with a trunk"),
        ("BOOK", "You read this"),
        ("FISH", "Swims in water"),
        ("BIRD", "Has feathers and flies"),
        ("RAIN", "Falls from clouds"),
        ("SNOW", "Cold white precipitation"),
        ("CAKE", "Sweet baked dessert"),
        ("MILK", "White drink from a cow"),
        ("DOOR", "You open this to enter a room"),
        ("SHOE", "Worn on your foot"),
        ("HAND", "Has five fingers"),
        ("LAMP", "Lights up a room"),
        ("BALL", "Round toy you throw or kick"),
        ("CLOCK", "Tells the time"),
        ("APPLE", "Red or green fruit, keeps the doctor away"),
        ("HOUSE", "Place where you live"),
        ("WATER", "H2O"),
        ("HAPPY", "Feeling joyful"),
        ("SMILE", "Curve made with your mouth when happy"),
        ("CHAIR", "You sit on it"),
        ("TABLE", "Furniture you eat off of"),
        ("MUSIC", "Sounds arranged pleasingly"),
        ("PIZZA", "Round Italian dish with toppings"),
        ("BEACH", "Sandy shore by the sea"),
        ("CLOUD", "Fluffy white sky object"),
        ("PLANT", "Living thing that grows in soil"),
        ("BREAD", "Baked from flour, sliced for toast"),
        ("PAPER", "You write on this"),
        ("GLASS", "Clear material, or a drinking vessel"),
        ("RIVER", "Flowing body of fresh water"),
    ],
    "Medium": [
        ("PYTHON", "Popular programming language"),
        ("PUZZLE", "Brain teaser like this one"),
        ("GARDEN", "Place to grow flowers and vegetables"),
        ("PLANET", "Earth is one"),
        ("WINTER", "Coldest season"),
        ("SUMMER", "Hottest season"),
        ("CASTLE", "Fortified home of royalty"),
        ("BRIDGE", "Structure crossing a river"),
        ("ISLAND", "Land surrounded by water"),
        ("JACKET", "Worn for warmth outdoors"),
        ("KITCHEN", "Room for cooking"),
        ("LIBRARY", "Building full of books"),
        ("MOUNTAIN", "Very tall landform"),
        ("SCIENCE", "Study of the natural world"),
        ("HISTORY", "Study of the past"),
        ("JOURNEY", "A long trip"),
        ("PICTURE", "An image or photo"),
        ("RAINBOW", "Colorful arc after rain"),
        ("STADIUM", "Large venue for sports events"),
        ("TEACHER", "Person who instructs students"),
        ("VOLCANO", "Mountain that can erupt"),
        ("WEATHER", "Rain, sun, wind and clouds"),
        ("AIRPORT", "Where planes take off and land"),
        ("BICYCLE", "Two-wheeled pedal vehicle"),
        ("CAPTAIN", "Leader of a ship or team"),
        ("DESKTOP", "Computer that stays on a desk"),
        ("ELEPHANT", "Largest land mammal"),
        ("FESTIVAL", "Celebration or cultural event"),
        ("GALLERY", "Room or building showing art"),
        ("HOLIDAY", "A day of celebration or rest"),
        ("KEYBOARD", "Typing input device"),
        ("LANGUAGE", "System of communication"),
        ("MEDICINE", "Treatment for illness"),
        ("NOTEBOOK", "Small book for writing notes"),
        ("ORCHESTRA", "Large group of musicians"),
    ],
    "Hard": [
        ("ALGORITHM", "Step-by-step problem-solving procedure"),
        ("QUARANTINE", "Isolation to prevent disease spread"),
        ("PHILOSOPHY", "Study of fundamental questions"),
        ("ARCHITECTURE", "Art and science of designing buildings"),
        ("ASTRONOMY", "Study of celestial objects"),
        ("BIODIVERSITY", "Variety of life in an ecosystem"),
        ("CHRONOLOGY", "Arrangement of events by time"),
        ("DEMOCRACY", "Government by the people"),
        ("ECOSYSTEM", "Community of interacting organisms"),
        ("FREQUENCY", "Rate at which something occurs"),
        ("GRAVITATIONAL", "Relating to the force of gravity"),
        ("HYPOTHESIS", "Proposed explanation for a phenomenon"),
        ("INFRASTRUCTURE", "Basic physical systems of a society"),
        ("JURISDICTION", "Official power to make legal decisions"),
        ("KILOMETER", "Metric unit of distance"),
        ("LEGISLATION", "Laws made by a governing body"),
        ("METABOLISM", "Chemical processes within a living organism"),
        ("NEGOTIATION", "Discussion aimed at reaching agreement"),
        ("OBSERVATORY", "Building for watching celestial events"),
        ("PARADIGM", "Typical example or pattern"),
        ("QUANTUM", "Smallest discrete unit of a quantity"),
        ("RENAISSANCE", "European cultural rebirth era"),
        ("STATISTICS", "Study of data collection and analysis"),
        ("TELESCOPE", "Instrument for viewing distant objects"),
        ("UNIVERSITY", "Institution of higher education"),
        ("VACCINATION", "Injection that builds immunity"),
        ("WAVELENGTH", "Distance between repeating wave points"),
        ("XENOPHOBIA", "Fear or dislike of foreigners"),
        ("YIELD", "Amount produced, or to give way"),
        ("ZOOLOGY", "Study of animals"),
        ("ENCRYPTION", "Process of encoding information"),
        ("MOLECULE", "Smallest unit of a chemical compound"),
        ("PENINSULA", "Land almost surrounded by water"),
        ("TURBULENCE", "Violent, irregular fluid motion"),
    ],
}

DIFFICULTY_SETTINGS = {
    "Easy":   {"grid_size": 13, "max_words": 9,  "min_len": 3, "max_len": 6},
    "Medium": {"grid_size": 17, "max_words": 13, "min_len": 5, "max_len": 9},
    "Hard":   {"grid_size": 21, "max_words": 15, "min_len": 6, "max_len": 14},
}

# --------------------------------------------------------------------------
# Crossword generation
# --------------------------------------------------------------------------

class CrosswordGenerator:
    """Builds a solvable crossword by placing words on a shared grid so
    that every word (after the first) crosses an already-placed word at
    a matching letter, with no illegal adjacent-letter collisions."""

    def __init__(self, words_clues, grid_size, seed=None):
        self.grid_size = grid_size
        self.words_clues = [(w.upper().strip(), c) for w, c in words_clues if w.isalpha()]
        self.rng = random.Random(seed)
        self.grid = {}      # (row, col) -> letter
        self.placed = []    # list of dicts: word, clue, row, col, dir, number

    def _fits(self, word, row, col, direction):
        size = self.grid_size
        length = len(word)
        if direction == 'H':
            if col < 0 or col + length > size or row < 0 or row >= size:
                return False
            if col - 1 >= 0 and (row, col - 1) in self.grid:
                return False
            if col + length < size and (row, col + length) in self.grid:
                return False
        else:  # 'V'
            if row < 0 or row + length > size or col < 0 or col >= size:
                return False
            if row - 1 >= 0 and (row - 1, col) in self.grid:
                return False
            if row + length < size and (row + length, col) in self.grid:
                return False

        has_intersection = False
        for i, ch in enumerate(word):
            r = row + i if direction == 'V' else row
            c = col + i if direction == 'H' else col
            existing = self.grid.get((r, c))
            if existing is not None:
                if existing != ch:
                    return False
                has_intersection = True
            else:
                # Non-intersection cell: perpendicular neighbours must be
                # empty, otherwise this letter would silently touch an
                # unrelated word and create an unintended entry.
                if direction == 'H':
                    if (r - 1, c) in self.grid or (r + 1, c) in self.grid:
                        return False
                else:
                    if (r, c - 1) in self.grid or (r, c + 1) in self.grid:
                        return False
        return has_intersection

    def _write(self, word, clue, row, col, direction):
        for i, ch in enumerate(word):
            r = row + i if direction == 'V' else row
            c = col + i if direction == 'H' else col
            self.grid[(r, c)] = ch
        self.placed.append({"word": word, "clue": clue, "row": row,
                             "col": col, "dir": direction})

    def _find_placement(self, word):
        candidates = []
        for (r, c), cell in list(self.grid.items()):
            for i, ch in enumerate(word):
                if ch != cell:
                    continue
                if self._fits(word, r, c - i, 'H'):
                    candidates.append((r, c - i, 'H'))
                if self._fits(word, r - i, c, 'V'):
                    candidates.append((r - i, c, 'V'))
        if not candidates:
            return None
        return self.rng.choice(candidates)

    def _generate_once(self, max_words):
        self.grid = {}
        self.placed = []
        words = list(self.words_clues)
        self.rng.shuffle(words)
        words.sort(key=lambda x: -len(x[0]))
        if not words:
            return 0

        first_word, first_clue = words[0]
        row = self.grid_size // 2
        col = max(0, (self.grid_size - len(first_word)) // 2)
        self._write(first_word, first_clue, row, col, 'H')

        rest = words[1:]
        self.rng.shuffle(rest)
        for word, clue in rest:
            if len(self.placed) >= max_words:
                break
            if len(word) < 2 or len(word) > self.grid_size:
                continue
            if any(p["word"] == word for p in self.placed):
                continue
            placement = self._find_placement(word)
            if placement:
                r, c, d = placement
                self._write(word, clue, r, c, d)
        return len(self.placed)

    def generate(self, max_words, attempts=40):
        best_grid, best_placed, best_count = {}, [], -1
        for _ in range(attempts):
            self.rng = random.Random(self.rng.random())
            count = self._generate_once(max_words)
            if count > best_count:
                best_count, best_grid, best_placed = count, dict(self.grid), \
                    [dict(p) for p in self.placed]
            if best_count >= max_words:
                break
        self.grid, self.placed = best_grid, best_placed
        self._number_words()
        return best_count

    def _number_words(self):
        starts = sorted({(p["row"], p["col"]) for p in self.placed})
        coord_number = {coord: i + 1 for i, coord in enumerate(starts)}
        for p in self.placed:
            p["number"] = coord_number[(p["row"], p["col"])]

    def bounding_box(self):
        rows = [r for r, c in self.grid.keys()]
        cols = [c for r, c in self.grid.keys()]
        return min(rows), max(rows), min(cols), max(cols)


def build_puzzle(difficulty, seed=None):
    """Generate a crossword for the given difficulty. Returns the
    CrosswordGenerator instance (grid + placed words are guaranteed
    consistent, so the puzzle is solvable by construction)."""
    settings = DIFFICULTY_SETTINGS[difficulty]
    pool = [(w, c) for w, c in WORD_BANKS[difficulty]
            if settings["min_len"] <= len(w) <= settings["max_len"]]
    gen = CrosswordGenerator(pool, settings["grid_size"], seed=seed)
    gen.generate(max_words=settings["max_words"], attempts=60)
    return gen


# --------------------------------------------------------------------------
# Pygame application
# --------------------------------------------------------------------------

pygame.display.init()
pygame.font.init()
pygame.display.set_caption("Crossword Generator")

info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
clock = pygame.time.Clock()

FONT_SM = pygame.font.SysFont("arial", 14)
FONT_MD = pygame.font.SysFont("arial", 18)
FONT_LG = pygame.font.SysFont("arial", 26, bold=True)
FONT_CELL = pygame.font.SysFont("arial", 22, bold=True)
FONT_NUM = pygame.font.SysFont("arial", 11)

# Colors
COL_BG = (245, 244, 238)
COL_GRID_BG = (255, 255, 255)
COL_BLOCK = (35, 35, 40)
COL_LINE = (70, 70, 70)
COL_SELECT = (255, 226, 120)
COL_WORD_HL = (255, 244, 200)
COL_TEXT = (25, 25, 25)
COL_CORRECT = (150, 220, 150)
COL_WRONG = (240, 140, 140)
COL_PANEL = (255, 255, 255)
COL_PANEL_BORDER = (210, 210, 205)
COL_BUTTON = (70, 110, 200)
COL_BUTTON_HOVER = (95, 135, 225)
COL_BUTTON_TEXT = (255, 255, 255)
COL_ACCENT = (70, 110, 200)
COL_CLOSE = (205, 70, 70)
COL_CLOSE_HOVER = (225, 95, 95)


class Button:
    def __init__(self, rect, text, font=FONT_MD, color=None, hover_color=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.color = color or COL_BUTTON
        self.hover_color = hover_color or COL_BUTTON_HOVER

    def draw(self, surf):
        hovered = self.rect.collidepoint(pygame.mouse.get_pos())
        color = self.hover_color if hovered else self.color
        pygame.draw.rect(surf, color, self.rect, border_radius=8)
        label = self.font.render(self.text, True, COL_BUTTON_TEXT)
        surf.blit(label, label.get_rect(center=self.rect.center))

    def clicked(self, pos):
        return self.rect.collidepoint(pos)


class CrosswordGame:
    CELL = 32

    def __init__(self):
        self.state = "MENU"        # MENU, PLAYING, WON
        self.difficulty = None
        self.gen = None
        self.user_grid = {}        # (row, col) -> letter typed by player
        self.selected = None       # (row, col)
        self.direction = "H"       # current typing direction
        self.status_msg = ""
        self.status_color = COL_TEXT
        self.status_timer = 0
        self.origin = (0, 0)       # pixel origin of the grid on screen
        self.bbox = (0, 0, 0, 0)

        self.menu_buttons = {
            "Easy": Button((info.current_w // 2 - 140, 300, 280, 55), "Easy", FONT_LG),
            "Medium": Button((info.current_w // 2 - 140, 380, 280, 55), "Medium", FONT_LG),
            "Hard": Button((info.current_w // 2 - 140, 460, 280, 55), "Hard", FONT_LG),
        }
        self.btn_close_menu = Button((info.current_w - 40 - 90, 20, 90, 34), "Close", FONT_MD,
                                      color=COL_CLOSE, hover_color=COL_CLOSE_HOVER)

        self.btn_new = Button((0, 0, 150, 36), "New Puzzle")
        self.btn_check = Button((0, 0, 110, 36), "Check")
        self.btn_reveal = Button((0, 0, 110, 36), "Reveal")
        self.btn_clear = Button((0, 0, 110, 36), "Clear")
        self.btn_menu = Button((0, 0, 110, 36), "Menu")
        self.btn_close = Button((0, 0, 90, 36), "Close", FONT_MD,
                                 color=COL_CLOSE, hover_color=COL_CLOSE_HOVER)

        self.check_flash = {}      # (row, col) -> ('ok'/'bad', frames_left)

    # ---------------------------------------------------------------- setup
    def new_puzzle(self, difficulty):
        self.difficulty = difficulty
        self.gen = build_puzzle(difficulty)
        self.user_grid = {}
        self.selected = None
        self.direction = "H"
        self.check_flash = {}
        self.state = "PLAYING"
        r0, r1, c0, c1 = self.gen.bounding_box()
        self.bbox = (r0, r1, c0, c1)
        rows = r1 - r0 + 1
        cols = c1 - c0 + 1
        grid_pixel_w = cols * self.CELL
        grid_pixel_h = rows * self.CELL
        ox = 40
        oy = 100 + max(0, (info.current_h - 160 - grid_pixel_h) // 2)
        self.origin = (ox, oy)
        self.set_status(f"{difficulty} puzzle ready \u2014 {len(self.gen.placed)} words placed.", COL_TEXT)

    def set_status(self, msg, color=COL_TEXT):
        self.status_msg = msg
        self.status_color = color
        self.status_timer = 180

    # -------------------------------------------------------------- helpers
    def cell_to_pixel(self, r, c):
        r0, r1, c0, c1 = self.bbox
        ox, oy = self.origin
        return ox + (c - c0) * self.CELL, oy + (r - r0) * self.CELL

    def pixel_to_cell(self, x, y):
        r0, r1, c0, c1 = self.bbox
        ox, oy = self.origin
        col = (x - ox) // self.CELL + c0
        row = (y - oy) // self.CELL + r0
        return int(row), int(col)

    def word_at(self, row, col, direction):
        """Return the placed-word dict containing (row,col) in the given
        direction, if any."""
        for p in self.gen.placed:
            if p["dir"] != direction:
                continue
            length = len(p["word"])
            if direction == "H" and p["row"] == row and p["col"] <= col < p["col"] + length:
                return p
            if direction == "V" and p["col"] == col and p["row"] <= row < p["row"] + length:
                return p
        return None

    def current_word(self):
        if not self.selected:
            return None
        r, c = self.selected
        w = self.word_at(r, c, self.direction)
        if w:
            return w
        other = "V" if self.direction == "H" else "H"
        return self.word_at(r, c, other)

    def next_cell_in_word(self, word, r, c, step=1):
        if word["dir"] == "H":
            nc = c + step
            if word["col"] <= nc < word["col"] + len(word["word"]):
                return r, nc
        else:
            nr = r + step
            if word["row"] <= nr < word["row"] + len(word["word"]):
                return nr, c
        return None

    # ---------------------------------------------------------------- input
    def handle_click(self, pos):
        r, c = self.pixel_to_cell(*pos)
        if (r, c) not in self.gen.grid:
            return
        if self.selected == (r, c):
            # flip direction if both exist
            other = "V" if self.direction == "H" else "H"
            if self.word_at(r, c, other):
                self.direction = other
        else:
            self.selected = (r, c)
            if not self.word_at(r, c, self.direction):
                other = "V" if self.direction == "H" else "H"
                if self.word_at(r, c, other):
                    self.direction = other

    def handle_key(self, event):
        if self.selected is None:
            return
        r, c = self.selected

        if event.unicode.isalpha() and len(event.unicode) == 1:
            self.user_grid[(r, c)] = event.unicode.upper()
            word = self.current_word()
            if word:
                nxt = self.next_cell_in_word(word, r, c, 1)
                if nxt:
                    self.selected = nxt

        elif event.key == pygame.K_BACKSPACE:
            if (r, c) in self.user_grid and self.user_grid[(r, c)]:
                self.user_grid[(r, c)] = ""
            else:
                word = self.current_word()
                if word:
                    prv = self.next_cell_in_word(word, r, c, -1)
                    if prv:
                        self.selected = prv
                        self.user_grid[prv] = ""

        elif event.key == pygame.K_LEFT:
            self.move_selection(0, -1)
            self.direction = "H"
        elif event.key == pygame.K_RIGHT:
            self.move_selection(0, 1)
            self.direction = "H"
        elif event.key == pygame.K_UP:
            self.move_selection(-1, 0)
            self.direction = "V"
        elif event.key == pygame.K_DOWN:
            self.move_selection(1, 0)
            self.direction = "V"
        elif event.key == pygame.K_TAB:
            self.direction = "V" if self.direction == "H" else "H"

    def move_selection(self, dr, dc):
        if not self.selected:
            return
        r, c = self.selected
        nr, nc = r + dr, c + dc
        if (nr, nc) in self.gen.grid:
            self.selected = (nr, nc)

    def select_word(self, word):
        self.selected = (word["row"], word["col"])
        self.direction = word["dir"]

    # ------------------------------------------------------------- checking
    def check_answers(self):
        self.check_flash = {}
        correct = 0
        total = len(self.gen.grid)
        for (r, c), letter in self.gen.grid.items():
            typed = self.user_grid.get((r, c), "")
            if typed == letter:
                self.check_flash[(r, c)] = "ok"
                correct += 1
            elif typed:
                self.check_flash[(r, c)] = "bad"
        if correct == total:
            self.state = "WON"
            self.set_status("Solved! Great job.", (30, 140, 30))
        else:
            self.set_status(f"{correct}/{total} letters correct so far.", COL_TEXT)

    def reveal(self):
        self.user_grid = dict(self.gen.grid)
        self.check_flash = {(rc): "ok" for rc in self.gen.grid}
        self.set_status("Answers revealed.", COL_TEXT)

    def clear_input(self):
        self.user_grid = {}
        self.check_flash = {}
        self.set_status("Cleared.", COL_TEXT)

    # ---------------------------------------------------------------- draw
    def draw_menu(self):
        screen.fill(COL_BG)
        title = FONT_LG.render("Crossword Generator", True, COL_TEXT)
        screen.blit(title, title.get_rect(center=(info.current_w // 2, 130)))
        subtitle = FONT_MD.render("Choose a difficulty to generate a new solvable puzzle",
                                   True, (90, 90, 90))
        screen.blit(subtitle, subtitle.get_rect(center=(info.current_w // 2, 175)))

        descs = {
            "Easy": "Small grid, short common words, lots of overlap.",
            "Medium": "Bigger grid, everyday vocabulary, moderate overlap.",
            "Hard": "Large grid, long/technical words, sparser overlap.",
        }
        for name, btn in self.menu_buttons.items():
            btn.draw(screen)
            desc = FONT_SM.render(descs[name], True, (90, 90, 90))
            screen.blit(desc, desc.get_rect(center=(info.current_w // 2, btn.rect.bottom + 16)))

        self.btn_close_menu.draw(screen)

    def draw_grid(self):
        r0, r1, c0, c1 = self.bbox
        for r in range(r0, r1 + 1):
            for c in range(c0, c1 + 1):
                x, y = self.cell_to_pixel(r, c)
                rect = pygame.Rect(x, y, self.CELL, self.CELL)
                if (r, c) not in self.gen.grid:
                    pygame.draw.rect(screen, COL_BLOCK, rect)
                    continue

                color = COL_GRID_BG
                word = self.current_word()
                if word:
                    length = len(word["word"])
                    if word["dir"] == "H" and word["row"] == r and word["col"] <= c < word["col"] + length:
                        color = COL_WORD_HL
                    elif word["dir"] == "V" and word["col"] == c and word["row"] <= r < word["row"] + length:
                        color = COL_WORD_HL
                if self.selected == (r, c):
                    color = COL_SELECT
                flash = self.check_flash.get((r, c))
                if flash == "ok":
                    color = COL_CORRECT
                elif flash == "bad":
                    color = COL_WRONG

                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, COL_LINE, rect, 1)

                num = None
                for p in self.gen.placed:
                    if p["row"] == r and p["col"] == c:
                        num = p["number"]
                        break
                if num:
                    num_lbl = FONT_NUM.render(str(num), True, (60, 60, 60))
                    screen.blit(num_lbl, (x + 2, y + 1))

                letter = self.user_grid.get((r, c), "")
                if letter:
                    lbl = FONT_CELL.render(letter, True, COL_TEXT)
                    screen.blit(lbl, lbl.get_rect(center=rect.center))

    def draw_clue_panel(self):
        panel_x = 40 + ((self.bbox[3] - self.bbox[2] + 1) * self.CELL) + 40
        panel_w = info.current_w - panel_x - 30
        panel_rect = pygame.Rect(panel_x, 100, panel_w, info.current_h - 140)
        pygame.draw.rect(screen, COL_PANEL, panel_rect, border_radius=8)
        pygame.draw.rect(screen, COL_PANEL_BORDER, panel_rect, 1, border_radius=8)

        y = panel_rect.top + 12
        x = panel_rect.left + 14
        self.clue_click_areas = []

        for direction, heading in (("H", "Across"), ("V", "Down")):
            hd = FONT_MD.render(heading, True, COL_ACCENT)
            screen.blit(hd, (x, y))
            y += 26
            words = sorted([p for p in self.gen.placed if p["dir"] == direction],
                            key=lambda p: p["number"])
            for w in words:
                is_current = self.current_word() is w
                bg_rect = pygame.Rect(x - 4, y - 2, panel_w - 20, 20)
                if is_current:
                    pygame.draw.rect(screen, COL_WORD_HL, bg_rect, border_radius=4)
                text = f'{w["number"]}. {w["clue"]}  ({len(w["word"])})'
                lbl = FONT_SM.render(text, True, COL_TEXT)
                # wrap manually if too long
                max_w = panel_w - 24
                if lbl.get_width() > max_w:
                    text = text[:int(len(text) * max_w / lbl.get_width()) - 1] + "…"
                    lbl = FONT_SM.render(text, True, COL_TEXT)
                screen.blit(lbl, (x, y))
                self.clue_click_areas.append((bg_rect.move(0, 0), w))
                y += 20
                if y > panel_rect.bottom - 20:
                    break
            y += 14

    def draw_topbar(self):
        title = FONT_LG.render(f"Crossword \u2014 {self.difficulty}", True, COL_TEXT)
        screen.blit(title, (40, 20))

        bx = info.current_w - 40
        for btn in (self.btn_close, self.btn_menu, self.btn_new, self.btn_clear,
                    self.btn_reveal, self.btn_check):
            btn.rect.right = bx
            btn.rect.top = 30
            bx -= btn.rect.width + 10
        for btn in (self.btn_check, self.btn_reveal, self.btn_clear, self.btn_new,
                    self.btn_menu, self.btn_close):
            btn.draw(screen)

        if self.status_timer > 0:
            self.status_timer -= 1
            msg = FONT_MD.render(self.status_msg, True, self.status_color)
            screen.blit(msg, (40, 65))

    def draw_playing(self):
        screen.fill(COL_BG)
        self.draw_topbar()
        self.draw_grid()
        self.draw_clue_panel()
        hint = FONT_SM.render(
            "Click a cell to select \u00b7 type letters \u00b7 Tab flips Across/Down \u00b7 arrows move",
            True, (110, 110, 110))
        screen.blit(hint, (40, info.current_h - 26))

    def draw_won_overlay(self):
        overlay = pygame.Surface((info.current_w, info.current_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))
        box = pygame.Rect(info.current_w // 2 - 220, info.current_h // 2 - 90, 440, 180)
        pygame.draw.rect(screen, COL_PANEL, box, border_radius=12)
        pygame.draw.rect(screen, COL_ACCENT, box, 2, border_radius=12)
        msg = FONT_LG.render("Puzzle Solved!", True, (30, 140, 30))
        screen.blit(msg, msg.get_rect(center=(box.centerx, box.top + 45)))
        sub = FONT_MD.render("Press N for a new puzzle, or M for the menu.", True, COL_TEXT)
        screen.blit(sub, sub.get_rect(center=(box.centerx, box.top + 100)))

    # --------------------------------------------------------------- events
    def open_launcher(self):
        try:
            launcher_path = os.path.join(os.path.dirname(__file__), "PuzzlerzGame.py")
            subprocess.Popen([sys.executable, launcher_path])
        except Exception:
            pass

    def open_congrats_screen(self):
        try:
            congrats_path = os.path.join(os.path.dirname(__file__), "CongratsScreen.py")
            env = os.environ.copy()
            env["PUZZLER_GAME_TYPE"] = "crossword"
            subprocess.Popen([sys.executable, congrats_path], env=env)
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
                for name, btn in self.menu_buttons.items():
                    if btn.clicked(event.pos):
                        self.new_puzzle(name)
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
                self.new_puzzle(self.difficulty)
                return
            if self.btn_check.clicked(event.pos):
                self.check_answers()
                if self.state == "WON":
                    self.open_congrats_screen()
                    pygame.quit()
                    sys.exit()
                return
            if self.btn_reveal.clicked(event.pos):
                self.reveal()
                return
            if self.btn_clear.clicked(event.pos):
                self.clear_input()
                return
            for rect, word in getattr(self, "clue_click_areas", []):
                if rect.collidepoint(event.pos):
                    self.select_word(word)
                    return
            self.handle_click(event.pos)

        elif event.type == pygame.KEYDOWN:
            if self.state == "WON":
                if event.key == pygame.K_n:
                    self.new_puzzle(self.difficulty)
                elif event.key == pygame.K_m:
                    self.state = "MENU"
                return
            self.handle_key(event)

    def draw(self):
        if self.state == "MENU":
            self.draw_menu()
        else:
            self.draw_playing()
            if self.state == "WON":
                self.draw_won_overlay()


def main():
    game = CrosswordGame()
    while True:
        for event in pygame.event.get():
            game.handle_event(event)
        game.draw()
        pygame.display.flip()
        clock.tick(30)


if __name__ == "__main__":
    main()