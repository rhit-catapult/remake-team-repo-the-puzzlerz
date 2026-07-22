import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import font, messagebox, simpledialog
from sudoku_gen import SudokuGen
from process_utils import launch_detached


class SudokuPopup:
    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku")
        self.root.state('zoomed')  # Maximize window

        # -- Shared palette (matches Word Search / Crossword) --
        self.bg_color = '#F5F4EE'
        self.panel_color = '#FFFFFF'
        self.panel_border = '#D2D2CD'
        self.text_color = '#191919'
        self.line_color = '#E1E1DC'
        self.thick_line_color = '#787878'
        self.clue_color = '#DCE6FA'      # light blue tint, derived from button blue
        self.input_color = '#FFFFFF'
        self.button_color = '#466EC8'
        self.button_hover = '#5F87E1'
        self.close_color = '#CD4646'
        self.close_hover = '#E15F5F'
        self.button_text_color = '#FFFFFF'

        self.root.configure(bg=self.bg_color)

        # Generator
        self.generator = SudokuGen()
        self.current_difficulty = 'medium'
        self.puzzle = self.generator.generate(self.current_difficulty)
        self.user_grid = [[self.puzzle[r][c] for c in range(9)] for r in range(9)]  # User input grid
        self.original_puzzle = [[self.puzzle[r][c] for c in range(9)] for r in range(9)]  # Original puzzle

        # Timer state
        self.start_time = time.time()
        self.timer_visible = True

        # Fonts (Arial for UI text, Consolas bold for grid digits -- matches Word Search)
        self.title_font = font.Font(family="Arial", size=26, weight="bold")
        self.timer_font = font.Font(family="Arial", size=18, weight="bold")
        self.cell_font = font.Font(family="Consolas", size=20, weight="bold")
        if not self.cell_font.actual("family").lower().startswith("consolas"):
            self.cell_font = font.Font(family="Courier New", size=20, weight="bold")
        self.button_font = font.Font(family="Arial", size=12)

        # Register validation command
        self.validate_cmd = (self.root.register(self.validate_digit), '%P', '%d')
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

        # Create UI
        self.create_ui()

        # Start the recurring timer tick
        self.tick_timer()

    def validate_digit(self, value, action):
        """Validate that only single digits 1-9 are entered"""
        if action == '0':  # Allow deletion
            return True
        if value == '':
            return True
        if len(value) == 1 and value.isdigit() and '1' <= value <= '9':
            return True
        return False

    def create_ui(self):
        """Create the popup UI"""
        # Title
        title_label = tk.Label(self.root, text="Sudoku",
                               font=self.title_font, bg=self.bg_color, fg=self.text_color)
        title_label.pack(pady=(20, 6))

        # Timer label (directly under the title, above the grid)
        self.timer_var = tk.StringVar(value="00:00")
        self.timer_label = tk.Label(self.root, textvariable=self.timer_var,
                                     font=self.timer_font, bg=self.bg_color, fg=self.text_color)
        self.timer_label.pack(pady=(0, 10))

        # Puzzle frame (acts as the thick outer/section border, like the word-search grid outline)
        self.puzzle_frame = tk.Frame(self.root, bg=self.thick_line_color,
                                      highlightbackground=self.panel_border,
                                      highlightthickness=1)
        self.puzzle_frame.pack(pady=20)
        puzzle_frame = self.puzzle_frame

        # Create grid with Entry widgets
        self.cells = {}
        self.cell_entries = {}
        self.cell_frames = {}

        for row in range(9):
            for col in range(9):
                is_clue = self.original_puzzle[row][col] != 0
                cell_bg = self.clue_color if is_clue else self.input_color

                border_top = 3 if row in [0, 3, 6] else 1
                border_bottom = 3 if row in [2, 5, 8] else 1
                border_left = 3 if col in [0, 3, 6] else 1
                border_right = 3 if col in [2, 5, 8] else 1

                container = tk.Frame(
                    puzzle_frame,
                    bg=self.thick_line_color if (border_top == 3 or border_left == 3
                                                  or border_bottom == 3 or border_right == 3)
                        else self.line_color,
                    width=44 + border_left + border_right,
                    height=44 + border_top + border_bottom
                )
                container.grid(row=row, column=col, padx=0, pady=0, sticky='nsew')
                container.grid_propagate(False)
                self.cell_frames[(row, col)] = container

                entry = tk.Entry(
                    container,
                    font=self.cell_font,
                    width=3,
                    justify='center',
                    bg=cell_bg,
                    fg=self.text_color,
                    relief='flat',
                    borderwidth=0,
                    validate='key',
                    validatecommand=self.validate_cmd
                )

                entry.place(x=border_left, y=border_top, width=44, height=44)

                if self.user_grid[row][col] != 0:
                    entry.insert(0, str(self.user_grid[row][col]))

                if is_clue:
                    entry.config(state='readonly', readonlybackground=cell_bg)
                else:
                    entry.bind('<KeyRelease>', lambda e, r=row, c=col: self.on_cell_change(r, c, e))

                self.cell_entries[(row, col)] = entry
                self.cells[(row, col)] = entry

        # Button frame
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(pady=20)

        new_btn = self._make_button(button_frame, "New Puzzle", self.new_puzzle_dialog,
                                     self.button_color, self.button_hover)
        new_btn.pack(side=tk.LEFT, padx=10)

        clear_btn = self._make_button(button_frame, "Clear Entries", self.clear_entries,
                                       self.button_color, self.button_hover)
        clear_btn.pack(side=tk.LEFT, padx=10)

        check_btn = self._make_button(button_frame, "Check Solution", self.check_solution,
                                       self.button_color, self.button_hover)
        check_btn.pack(side=tk.LEFT, padx=10)

        self.timer_toggle_btn = self._make_button(button_frame, "Hide Timer", self.toggle_timer,
                                                    self.button_color, self.button_hover)
        self.timer_toggle_btn.pack(side=tk.LEFT, padx=10)

        close_btn = self._make_button(button_frame, "Close", self.close_window,
                                       self.close_color, self.close_hover)
        close_btn.pack(side=tk.LEFT, padx=10)

    def _make_button(self, parent, text, command, color, hover_color):
        """Flat, rounded-feel button styled to match Word Search / Crossword buttons."""
        btn = tk.Button(
            parent, text=text, font=self.button_font, command=command,
            bg=color, fg=self.button_text_color,
            activebackground=hover_color, activeforeground=self.button_text_color,
            relief='flat', bd=0, padx=18, pady=10, cursor='hand2',
            highlightthickness=0
        )
        btn.bind('<Enter>', lambda e: btn.config(bg=hover_color))
        btn.bind('<Leave>', lambda e: btn.config(bg=color))
        return btn

    # ---------------------------------------------------------------- timer
    def tick_timer(self):
        """Recurring 1-second tick that updates the elapsed-time label."""
        elapsed = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed, 60)
        self.timer_var.set(f"{mins:02d}:{secs:02d}")
        self.root.after(1000, self.tick_timer)

    def toggle_timer(self):
        """Show/hide the timer label -- the clock keeps running in the
        background either way, only the display is affected."""
        self.timer_visible = not self.timer_visible
        if self.timer_visible:
            self.timer_label.pack(pady=(0, 10), before=self.puzzle_frame)
            self.timer_toggle_btn.config(text="Hide Timer")
        else:
            self.timer_label.pack_forget()
            self.timer_toggle_btn.config(text="Show Timer")

    def close_window(self):
        """Close the Sudoku window and reopen the main launcher interface."""
        self.root.destroy()
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            launcher_path = os.path.join(here, "PuzzlerzGame.py")
            launch_detached([sys.executable, launcher_path], cwd=here)
        except Exception as e:
            print(f"Failed to relaunch PuzzlerzGame.py: {e}")

    def new_puzzle_dialog(self):
        """Show difficulty selection dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Difficulty")
        dialog.geometry("400x400")
        dialog.configure(bg=self.bg_color)
        dialog.resizable(False, False)

        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        dialog_width = 400
        dialog_height = 400
        x = (screen_width - dialog_width) // 2
        y = (screen_height - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")

        dialog.transient(self.root)
        dialog.grab_set()

        label = tk.Label(dialog, text="Choose Difficulty Level:",
                         font=font.Font(family="Arial", size=16, weight="bold"),
                         bg=self.bg_color, fg=self.text_color)
        label.pack(pady=40)

        easy_btn = self._make_button(dialog, "Easy (45-54 clues)",
                                      lambda: self.generate_new_puzzle('easy', dialog),
                                      self.button_color, self.button_hover)
        easy_btn.pack(pady=20)

        medium_btn = self._make_button(dialog, "Medium (30-40 clues)",
                                        lambda: self.generate_new_puzzle('medium', dialog),
                                        self.button_color, self.button_hover)
        medium_btn.pack(pady=20)

        hard_btn = self._make_button(dialog, "Hard (17-25 clues)",
                                      lambda: self.generate_new_puzzle('hard', dialog),
                                      self.close_color, self.close_hover)
        hard_btn.pack(pady=20)

    def generate_new_puzzle(self, difficulty, dialog):
        """Generate and display a new puzzle with selected difficulty"""
        dialog.destroy()

        self.current_difficulty = difficulty
        self.puzzle = self.generator.generate(difficulty)
        self.original_puzzle = [[self.puzzle[r][c] for c in range(9)] for r in range(9)]
        self.user_grid = [[self.puzzle[r][c] for c in range(9)] for r in range(9)]

        # Reset the timer for the new puzzle
        self.start_time = time.time()

        for row in range(9):
            for col in range(9):
                entry = self.cell_entries[(row, col)]
                value = self.user_grid[row][col]

                entry.config(state='normal')
                entry.delete(0, tk.END)

                is_clue = self.original_puzzle[row][col] != 0
                cell_bg = self.clue_color if is_clue else self.input_color
                entry.config(bg=cell_bg)

                if value != 0:
                    entry.insert(0, str(value))

                entry.unbind('<KeyRelease>')

                if is_clue:
                    entry.config(state='readonly', readonlybackground=cell_bg)
                else:
                    entry.bind('<KeyRelease>', lambda e, r=row, c=col: self.on_cell_change(r, c, e))

    def on_cell_change(self, row, col, event):
        """Handle cell input changes and update user grid"""
        entry = self.cell_entries[(row, col)]
        value = entry.get().strip()

        if value:
            self.user_grid[row][col] = int(value)
        else:
            self.user_grid[row][col] = 0

    def clear_entries(self):
        """Clear all user entries, keep clues"""
        for row in range(9):
            for col in range(9):
                if self.original_puzzle[row][col] == 0:
                    entry = self.cell_entries[(row, col)]
                    entry.config(state='normal')
                    entry.delete(0, tk.END)
                    self.user_grid[row][col] = 0

    def check_solution(self):
        """Check if the current solution is correct"""
        for row in range(9):
            for col in range(9):
                if self.user_grid[row][col] == 0:
                    messagebox.showwarning("Incomplete", "Please fill all cells!")
                    return

        if self.is_valid_solution():
            try:
                here = os.path.dirname(os.path.abspath(__file__))
                congrats_path = os.path.join(here, 'CongratsScreen.py')
                env = os.environ.copy()
                env['PUZZLER_GAME_TYPE'] = 'sudoku'
                if self.timer_visible:
                    elapsed = int(time.time() - self.start_time)
                    env['PUZZLER_ELAPSED_SECONDS'] = str(elapsed)
                launch_detached([sys.executable, congrats_path], cwd=here, env=env)
            except Exception as e:
                messagebox.showerror("Congratulations Error", f"Could not open the congratulations screen: {e}")
            self.root.destroy()
        else:
            messagebox.showerror("Error", "There is an error in the puzzle. Please try again.")

    def is_valid_solution(self):
        """Validate the current solution"""
        for row in range(9):
            if len(set(self.user_grid[row])) != 9 or 0 in self.user_grid[row]:
                return False

        for col in range(9):
            column = [self.user_grid[row][col] for row in range(9)]
            if len(set(column)) != 9 or 0 in column:
                return False

        for box_row in range(3):
            for box_col in range(3):
                box = []
                for i in range(3):
                    for j in range(3):
                        box.append(self.user_grid[box_row * 3 + i][box_col * 3 + j])
                if len(set(box)) != 9 or 0 in box:
                    return False

        return True


# Create and run popup
if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuPopup(root)
    root.mainloop()