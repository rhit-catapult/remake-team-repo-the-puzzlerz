import tkinter as tk
from tkinter import font, messagebox
from sudoku_gen import SudokuGen


class SudokuPopup:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku Puzzle")
        self.root.geometry("550x600")
        self.root.configure(bg='white')

        # Generator
        self.generator = SudokuGen()
        self.puzzle = self.generator.generate('medium')

        # Fonts
        self.title_font = font.Font(family="Arial", size=20, weight="bold")
        self.cell_font = font.Font(family="Arial", size=24, weight="bold")
        self.button_font = font.Font(family="Arial", size=12)

        # Colors
        self.bg_color = 'white'
        self.cell_color = '#f0f0f0'
        self.border_color = 'black'

        # Create UI
        self.create_ui()

    def create_ui(self):
        """Create the popup UI"""
        # Title
        title_label = tk.Label(self.root, text="Sudoku Puzzle",
                               font=self.title_font, bg='white', fg='black')
        title_label.pack(pady=10)

        # Puzzle frame
        puzzle_frame = tk.Frame(self.root, bg=self.bg_color)
        puzzle_frame.pack(pady=10)

        # Create grid buttons
        self.cells = {}
        CELL_SIZE = 40

        for row in range(9):
            for col in range(9):
                # Determine border width
                border_width = 3 if (row % 3 == 0 or row == 8) and (col % 3 == 0 or col == 8) else 1

                # Get value from puzzle
                value = self.puzzle[row][col]
                display_text = str(value) if value != 0 else ""

                # Create button
                btn = tk.Label(
                    puzzle_frame,
                    text=display_text,
                    font=self.cell_font,
                    width=4,
                    height=2,
                    bg=self.cell_color,
                    fg='black',
                    relief='solid',
                    borderwidth=border_width
                )
                btn.grid(row=row, column=col, padx=0, pady=0)
                self.cells[(row, col)] = btn

        # Button frame
        button_frame = tk.Frame(self.root, bg='white')
        button_frame.pack(pady=15)

        # New puzzle button
        new_btn = tk.Button(button_frame, text="New Puzzle",
                            font=self.button_font, command=self.new_puzzle,
                            bg='#4CAF50', fg='white', padx=15, pady=5)
        new_btn.pack(side=tk.LEFT, padx=5)

        # Close button
        close_btn = tk.Button(button_frame, text="Close",
                              font=self.button_font, command=self.root.quit,
                              bg='#f44336', fg='white', padx=15, pady=5)
        close_btn.pack(side=tk.LEFT, padx=5)

    def new_puzzle(self):
        """Generate and display a new puzzle"""
        self.puzzle = self.generator.generate('medium')

        # Update all cells
        for row in range(9):
            for col in range(9):
                value = self.puzzle[row][col]
                display_text = str(value) if value != 0 else ""
                self.cells[(row, col)].config(text=display_text)

    def update_display(self):
        """Update the puzzle display"""
        for row in range(9):
            for col in range(9):
                value = self.puzzle[row][col]
                display_text = str(value) if value != 0 else ""
                self.cells[(row, col)].config(text=display_text)


# Create and run popup
if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuPopup(root)
    root.mainloop()