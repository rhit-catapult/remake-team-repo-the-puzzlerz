import tkinter as tk
from tkinter import font, messagebox
import random
import string

# Word categories
WORD_GENRES = {
    'Animals': ['ELEPHANT', 'TIGER', 'GIRAFFE', 'ZEBRA', 'LION', 'MONKEY', 'PENGUIN', 'DOLPHIN', 'EAGLE', 'BEAR',
                'WOLF', 'SHARK', 'CHEETAH', 'PANDA', 'KOALA'],
    'Countries': ['FRANCE', 'JAPAN', 'BRAZIL', 'MEXICO', 'CANADA', 'ITALY', 'GERMANY', 'SPAIN', 'CHINA', 'INDIA',
                  'RUSSIA', 'EGYPT', 'KOREA', 'EGYPT', 'TURKEY'],
    'Programming': ['PYTHON', 'JAVA', 'CODE', 'PUZZLE', 'SEARCH', 'GAME', 'ALGORITHM', 'DEBUG', 'COMPILE', 'VARIABLE',
                    'FUNCTION', 'LOOP', 'CLASS', 'SYNTAX', 'LOGIC'],
    'Food': ['PIZZA', 'BURGER', 'PASTA', 'SUSHI', 'TACOS', 'SALAD', 'BREAD', 'CHEESE', 'APPLE', 'CARROT', 'CHICKEN',
             'RICE', 'BEANS', 'STEAK', 'COOKIE'],
    'Sports': ['SOCCER', 'BASKETBALL', 'TENNIS', 'HOCKEY', 'VOLLEYBALL', 'GOLF', 'CRICKET', 'BOXING', 'RUGBY',
               'BASEBALL', 'SWIMMING', 'RUNNING', 'SKIING', 'SKATING', 'ARCHERY'],
    'Colors': ['PURPLE', 'ORANGE', 'GREEN', 'YELLOW', 'BLUE', 'RED', 'PINK', 'BROWN', 'GRAY', 'WHITE', 'BLACK', 'TEAL',
               'GOLD', 'SILVER', 'MAROON'],
    'Vehicles': ['AIRPLANE', 'BICYCLE', 'TRUCK', 'BOAT', 'TRAIN', 'MOTORCYCLE', 'HELICOPTER', 'SUBMARINE', 'TAXI',
                 'BUS', 'SCOOTER', 'WAGON', 'JEEP', 'YACHT', 'ROCKET'],
    'Planets': ['MERCURY', 'VENUS', 'EARTH', 'MARS', 'JUPITER', 'SATURN', 'URANUS', 'NEPTUNE', 'PLUTO', 'MOON', 'SUN',
                'COMET', 'STAR', 'NOVA', 'ORBIT'],
}


class WordSearchMenu:
    def __init__(self, root, initial_genre='Programming', initial_size='12'):
        self.root = root
        self.root.title("Word Search - Game Setup")
        self.root.state('zoomed')  # Maximize window
        self.root.configure(bg='white')

        # Title
        title_label = tk.Label(self.root, text="Word Search Game",
                               font=font.Font(family="Arial", size=24, weight="bold"),
                               bg='white', fg='black')
        title_label.pack(pady=20)

        # Genre selection
        genre_label = tk.Label(self.root, text="Select Genre:",
                               font=font.Font(family="Arial", size=14, weight="bold"),
                               bg='white')
        genre_label.pack(pady=10)

        genre_frame = tk.Frame(self.root, bg='white')
        genre_frame.pack(expand=True)

        self.genre_var = tk.StringVar(value=initial_genre)
        for genre in WORD_GENRES.keys():
            rb = tk.Radiobutton(genre_frame, text=genre, variable=self.genre_var, value=genre,
                                font=font.Font(family="Arial", size=11), bg='white')
            rb.pack(anchor=tk.CENTER)

        # Grid size selection
        size_label = tk.Label(self.root, text="Select Grid Size:",
                              font=font.Font(family="Arial", size=14, weight="bold"),
                              bg='white')
        size_label.pack(pady=20)

        size_frame = tk.Frame(self.root, bg='white')
        size_frame.pack(expand=True)

        self.size_var = tk.StringVar(value=initial_size)
        sizes = ['10', '12', '15', '18']
        for size in sizes:
            rb = tk.Radiobutton(size_frame, text=f"{size}x{size}", variable=self.size_var, value=size,
                                font=font.Font(family="Arial", size=11), bg='white')
            rb.pack(anchor=tk.CENTER)

        # Start button
        start_btn = tk.Button(self.root, text="Start Game",
                              font=font.Font(family="Arial", size=12, weight="bold"),
                              bg='#4CAF50', fg='white', padx=30, pady=10,
                              command=self.start_game)
        start_btn.pack(pady=20)

    def start_game(self):
        genre = self.genre_var.get()
        size = int(self.size_var.get())
        self.root.destroy()

        # Open word search game
        game_root = tk.Tk()
        app = WordSearch(game_root, WORD_GENRES[genre], size, genre=genre, size=size)
        game_root.mainloop()


class WordSearch:
    def __init__(self, root, words, grid_size, genre=None, size=None):
        self.root = root
        self.root.title("Word Search")
        self.root.state('zoomed')  # Maximize window
        self.root.configure(bg='white')

        self.selected_genre = genre if genre is not None else 'Programming'
        self.selected_size = str(size if size is not None else grid_size)

        # Game state
        self.words = words[:min(len(words), 10 + (grid_size // 3))]  # Scale words to grid size (minimum 10)
        self.found_words = set()
        self.grid_size = grid_size
        self.grid = []
        self.cell_size = max(20, 480 // grid_size)  # Scale cell size based on grid
        self.selected_cells = []
        self.start_cell = None

        # Fonts
        self.title_font = font.Font(family="Arial", size=24, weight="bold")
        self.cell_font = font.Font(family="Arial", size=max(8, self.cell_size - 12), weight="bold")
        self.word_font = font.Font(family="Arial", size=10)

        # Colors
        self.normal_color = '#f0f0f0'
        self.selected_color = '#FFD700'
        self.found_color = '#90EE90'

        # Generate puzzle
        self.generate_puzzle()
        self.create_ui()

    def generate_puzzle(self):
        """Generate a word search puzzle"""
        # Keep trying until we successfully place all words
        max_iterations = 1000
        iteration = 0

        while iteration < max_iterations:
            # Create grid with empty cells (None indicates empty)
            self.grid = [[None for _ in range(self.grid_size)]
                         for _ in range(self.grid_size)]
            self.word_positions = {}

            # Try to place all words
            all_placed = True
            for word in self.words:
                placed = False
                attempts = 0
                while not placed and attempts < 100:
                    # Random direction: 0=horizontal, 1=vertical, 2=diagonal, 3=reverse
                    direction = random.randint(0, 3)
                    row = random.randint(0, self.grid_size - 1)
                    col = random.randint(0, self.grid_size - 1)

                    if self.can_place_word(word, row, col, direction):
                        self.place_word(word, row, col, direction)
                        self.word_positions[word] = (row, col, direction)
                        placed = True
                    attempts += 1

                if not placed:
                    all_placed = False
                    break

            # If all words placed successfully, fill remaining cells and exit
            if all_placed and len(self.word_positions) == len(self.words):
                for row in range(self.grid_size):
                    for col in range(self.grid_size):
                        if self.grid[row][col] is None:
                            self.grid[row][col] = random.choice(string.ascii_uppercase)
                break

            iteration += 1

    def can_place_word(self, word, row, col, direction):
        """Check if word can be placed at position"""
        for i, letter in enumerate(word):
            if direction == 0:  # Horizontal
                if col + i >= self.grid_size:
                    return False
                cell = self.grid[row][col + i]
                if cell is not None and cell != letter:
                    return False
            elif direction == 1:  # Vertical
                if row + i >= self.grid_size:
                    return False
                cell = self.grid[row + i][col]
                if cell is not None and cell != letter:
                    return False
            elif direction == 2:  # Diagonal down-right
                if row + i >= self.grid_size or col + i >= self.grid_size:
                    return False
                cell = self.grid[row + i][col + i]
                if cell is not None and cell != letter:
                    return False
            elif direction == 3:  # Horizontal reverse
                if col - i < 0:
                    return False
                cell = self.grid[row][col - i]
                if cell is not None and cell != letter:
                    return False
        return True

    def place_word(self, word, row, col, direction):
        """Place word in grid"""
        for i, letter in enumerate(word):
            if direction == 0:  # Horizontal
                self.grid[row][col + i] = letter
            elif direction == 1:  # Vertical
                self.grid[row + i][col] = letter
            elif direction == 2:  # Diagonal down-right
                self.grid[row + i][col + i] = letter
            elif direction == 3:  # Horizontal reverse
                self.grid[row][col - i] = letter

    def create_ui(self):
        """Create the UI"""
        # Title and close button
        title_frame = tk.Frame(self.root, bg='white')
        title_frame.pack(fill=tk.X, pady=10)

        title_label = tk.Label(title_frame, text="Word Search",
                               font=self.title_font, bg='white', fg='black')
        title_label.pack(side=tk.LEFT, expand=True)

        new_selection_btn = tk.Button(title_frame, text="New Selection", font=font.Font(family="Arial", size=12, weight="bold"),
                                      bg='#5bc0de', fg='white', padx=12, pady=6,
                                      command=self.open_menu)
        new_selection_btn.pack(side=tk.RIGHT, padx=5)

        close_btn = tk.Button(title_frame, text="Close", font=font.Font(family="Arial", size=12, weight="bold"),
                              bg='#d9534f', fg='white', padx=12, pady=6,
                              command=self.close_window)
        close_btn.pack(side=tk.RIGHT, padx=10)

        # Main container
        container = tk.Frame(self.root, bg='white')
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Left side - puzzle grid
        left_frame = tk.Frame(container, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        puzzle_label = tk.Label(left_frame, text="Puzzle",
                                font=font.Font(family="Arial", size=14, weight="bold"),
                                bg='white')
        puzzle_label.pack()

        # Canvas for grid
        canvas_width = self.grid_size * self.cell_size
        canvas_height = self.grid_size * self.cell_size
        self.canvas = tk.Canvas(left_frame, width=canvas_width, height=canvas_height,
                                bg='white', relief='solid', borderwidth=1)
        self.canvas.pack(pady=10)
        self.canvas.bind('<Button-1>', self.on_canvas_press)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)

        # Draw grid
        self.draw_grid()

        # Right side - word bank
        right_frame = tk.Frame(container, bg='white')
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=20)

        words_label = tk.Label(right_frame, text="Words to Find",
                               font=font.Font(family="Arial", size=14, weight="bold"),
                               bg='white')
        words_label.pack()

        # Scrollable word bank
        scroll_frame = tk.Frame(right_frame, bg='white')
        scroll_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.word_canvas = tk.Canvas(scroll_frame, bg='white',
                                     yscrollcommand=scrollbar.set, highlightthickness=0)
        self.word_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.word_canvas.yview)

        self.word_frame = tk.Frame(self.word_canvas, bg='white')
        self.word_canvas.create_window((0, 0), window=self.word_frame, anchor='nw')

        # Word bank
        self.word_labels = {}
        for word in self.words:
            label = tk.Label(self.word_frame, text=word, font=self.word_font,
                             bg='white', justify=tk.LEFT)
            label.pack(anchor=tk.W, pady=3)
            self.word_labels[word] = label

        self.word_frame.update_idletasks()
        self.word_canvas.config(scrollregion=self.word_canvas.bbox('all'))

    def close_window(self):
        """Close the current word search window."""
        self.root.destroy()

    def open_menu(self):
        """Return to the word search menu with the current topic and size selected."""
        self.root.destroy()
        menu_root = tk.Tk()
        WordSearchMenu(menu_root, initial_genre=self.selected_genre, initial_size=self.selected_size)

    def draw_grid(self):
        """Draw the word search grid"""
        self.canvas.delete('all')
        self.cell_coords = {}

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                x = col * self.cell_size
                y = row * self.cell_size

                # Draw cell background
                cell_id = self.canvas.create_rectangle(
                    x, y, x + self.cell_size, y + self.cell_size,
                    fill=self.normal_color, outline='gray', width=1
                )

                # Draw letter
                text_id = self.canvas.create_text(
                    x + self.cell_size // 2, y + self.cell_size // 2,
                    text=self.grid[row][col], font=self.cell_font
                )

                self.cell_coords[(row, col)] = {
                    'cell_id': cell_id,
                    'text_id': text_id,
                    'x': x,
                    'y': y
                }

    def on_canvas_press(self, event):
        """Handle mouse press"""
        row, col = self.get_cell_from_coords(event.x, event.y)
        if row is not None and col is not None:
            self.start_cell = (row, col)
            self.selected_cells = [(row, col)]
            self.highlight_selected_cells()

    def on_canvas_drag(self, event):
        """Handle mouse drag"""
        if self.start_cell is None:
            return

        row, col = self.get_cell_from_coords(event.x, event.y)
        if row is None or col is None:
            return

        start_row, start_col = self.start_cell

        # Determine direction
        row_diff = row - start_row
        col_diff = col - start_col

        # Validate direction (horizontal, vertical, or diagonal)
        if row_diff == 0 and col_diff == 0:
            self.selected_cells = [(start_row, start_col)]
        elif row_diff == 0:  # Horizontal
            if col_diff > 0:
                self.selected_cells = [(start_row, start_col + i) for i in range(col_diff + 1)]
            else:
                self.selected_cells = [(start_row, start_col + i) for i in range(col_diff, 1)]
        elif col_diff == 0:  # Vertical
            if row_diff > 0:
                self.selected_cells = [(start_row + i, start_col) for i in range(row_diff + 1)]
            else:
                self.selected_cells = [(start_row + i, start_col) for i in range(row_diff, 1)]
        elif abs(row_diff) == abs(col_diff):  # Diagonal
            row_step = 1 if row_diff > 0 else -1
            col_step = 1 if col_diff > 0 else -1
            steps = abs(row_diff) + 1
            self.selected_cells = [(start_row + row_step * i, start_col + col_step * i)
                                   for i in range(steps)]

        self.highlight_selected_cells()

    def on_canvas_release(self, event):
        """Handle mouse release - check for valid word"""
        if not self.selected_cells:
            return

        # Get selected letters
        selected_word = ''.join([self.grid[r][c] for r, c in self.selected_cells])
        reversed_word = selected_word[::-1]

        # Check against word list
        for word in self.words:
            if word in self.found_words:
                continue

            if selected_word == word or reversed_word == word:
                self.found_words.add(word)
                self.mark_word_found(word)
                self.highlight_found_word()
                if len(self.found_words) == len(self.words):
                    messagebox.showinfo("Success!", "You found all the words!")
                return

        # Clear selection if no match
        self.selected_cells = []
        self.draw_grid()
        self.draw_found_words()

    def highlight_selected_cells(self):
        """Highlight selected cells on canvas"""
        self.draw_grid()
        self.draw_found_words()

        for row, col in self.selected_cells:
            cell_info = self.cell_coords[(row, col)]
            self.canvas.itemconfig(cell_info['cell_id'], fill=self.selected_color)

    def highlight_found_word(self):
        """Highlight found word in green"""
        for row, col in self.selected_cells:
            cell_info = self.cell_coords[(row, col)]
            self.canvas.itemconfig(cell_info['cell_id'], fill=self.found_color)

    def draw_found_words(self):
        """Draw found words on grid"""
        for word in self.found_words:
            if word not in self.word_positions:
                continue

            row, col, direction = self.word_positions[word]
            for i, letter in enumerate(word):
                if direction == 0:  # Horizontal
                    r, c = row, col + i
                elif direction == 1:  # Vertical
                    r, c = row + i, col
                elif direction == 2:  # Diagonal
                    r, c = row + i, col + i
                elif direction == 3:  # Reverse
                    r, c = row, col - i

                cell_info = self.cell_coords[(r, c)]
                self.canvas.itemconfig(cell_info['cell_id'], fill=self.found_color)

    def mark_word_found(self, word):
        """Cross out word in word bank"""
        label = self.word_labels[word]
        label.config(font=font.Font(family="Arial", size=11, overstrike=True))

    def get_cell_from_coords(self, x, y):
        """Get grid cell from canvas coordinates"""
        col = x // self.cell_size
        row = y // self.cell_size

        if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
            return row, col
        return None, None


def open_word_search():
    """Open word search in a new window"""
    root = tk.Toplevel()
    menu = WordSearchMenu(root)
    return root


if __name__ == "__main__":
    root = tk.Tk()
    menu = WordSearchMenu(root)
    root.mainloop()
