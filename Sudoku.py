import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import font, messagebox, simpledialog
from copy import deepcopy
from sudoku_gen import SudokuGen
from process_utils import (
    launch_detached,
    open_or_focus_music,
    open_or_focus_screen,
    write_screen_pid,
    clear_screen_pid,
)

THIS_SCRIPT_PATH = os.path.abspath(__file__)


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
        self.error_color = '#F1948A'     # highlight for incorrect/conflicting cells
        self.button_color = '#466EC8'
        self.button_hover = '#5F87E1'
        self.close_color = '#CD4646'
        self.close_hover = '#E15F5F'
        self.music_color = '#828C96'     # matches the launcher's gray Music button
        self.music_hover = '#96A0AA'
        self.notes_off_color = '#466EC8'  # same as the standard button color
        self.notes_off_hover = '#5F87E1'
        self.notes_on_color = '#3B9C6D'   # green while notes mode is active
        self.notes_on_hover = '#4CB57F'
        self.button_text_color = '#FFFFFF'

        self.root.configure(bg=self.bg_color)

        # Generator
        self.generator = SudokuGen()
        self.current_difficulty = 'medium'
        self.puzzle = self.generator.generate(self.current_difficulty)
        self.user_grid = [[self.puzzle[r][c] for c in range(9)] for r in range(9)]  # User input grid
        self.original_puzzle = [[self.puzzle[r][c] for c in range(9)] for r in range(9)]  # Original puzzle
        # The actual filled-in solution for this puzzle. SudokuGen
        # already builds and verifies a unique solution as part of
        # generate() and keeps it on self.generator.solution -- snapshot
        # it (deepcopy, since generate() reuses/mutates that attribute
        # on the next call) rather than re-solving the puzzle
        # ourselves. "Check Solution" compares each cell against this.
        # Falls back to solving it ourselves only if that's ever
        # missing (shouldn't normally happen).
        self.solution = (
            deepcopy(self.generator.solution)
            if self.generator.solution is not None
            else self.solve_sudoku(self.original_puzzle)
        )

        # Cells currently highlighted red from the last "Check Solution"
        # click. Cleared as soon as any cell is edited.
        self.error_cells = set()

        # Pencil-mark notes: small candidate digits the player can jot
        # in a cell without them counting as the actual answer. Keyed
        # by (row, col) -> a set of single-character digit strings.
        # Purely a player aid -- never touched by check_solution().
        self.notes = {(r, c): set() for r in range(9) for c in range(9)}
        self.notes_mode = False

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
        self.notes_font = font.Font(family="Arial", size=7)

        # Register validation command
        self.validate_cmd = (self.root.register(self.validate_digit), '%P', '%d')
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

        # Announce that this Sudoku window is alive, so Music's Close
        # button (or another screen's) can find and refocus it later
        # instead of relaunching a fresh, unsolved puzzle.
        write_screen_pid(THIS_SCRIPT_PATH)

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
        self.note_frames = {}
        self.note_mini_labels = {}

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

                # Pencil-mark notes grid: a 3x3 arrangement of tiny
                # labels, one fixed position per digit (1 top-left ...
                # 9 bottom-right, like a keypad), covering the same
                # area as the Entry. It's placed after the Entry (so
                # stacked above it) but only actually lifted to the
                # front while the cell is empty -- refresh_note_visibility()
                # drops it behind the Entry again once a real answer
                # is typed, so the big answer digit is what's visible.
                note_frame = tk.Frame(container, bg=cell_bg)
                note_frame.place(x=border_left, y=border_top, width=44, height=44)
                note_frame.bind('<Button-1>', lambda e, ent=entry: ent.focus_set())
                for i in range(3):
                    note_frame.grid_rowconfigure(i, weight=1, uniform="notes_row")
                    note_frame.grid_columnconfigure(i, weight=1, uniform="notes_col")

                mini_labels = {}
                for idx in range(9):
                    digit = str(idx + 1)
                    r_idx, c_idx = divmod(idx, 3)
                    mini_lbl = tk.Label(
                        note_frame, text="", font=self.notes_font,
                        bg=cell_bg, fg="#707070"
                    )
                    mini_lbl.grid(row=r_idx, column=c_idx, sticky='nsew')
                    mini_lbl.bind('<Button-1>', lambda e, ent=entry: ent.focus_set())
                    mini_labels[digit] = mini_lbl

                self.note_frames[(row, col)] = note_frame
                self.note_mini_labels[(row, col)] = mini_labels

                if is_clue:
                    entry.config(state='readonly', readonlybackground=cell_bg)
                else:
                    entry.bind('<KeyRelease>', lambda e, r=row, c=col: self.on_cell_change(r, c, e))
                    entry.bind('<KeyPress>', lambda e, r=row, c=col: self.on_cell_keypress(r, c, e))
                    # The instant this Entry actually gets focus -- whether
                    # from a direct click on it, or indirectly via the
                    # notes grid's click-forwarding above -- bring it to
                    # the front so its cursor is visible and it's
                    # unambiguously the widget receiving clicks/keys from
                    # here on. When focus leaves, hand the decision back
                    # to refresh_note_visibility (notes reclaim the top
                    # layer only if the cell is still empty).
                    entry.bind('<FocusIn>', lambda e, r=row, c=col: self.on_entry_focus_in(r, c))
                    entry.bind('<FocusOut>', lambda e, r=row, c=col: self.refresh_note_visibility(r, c))

                self.cell_entries[(row, col)] = entry
                self.cells[(row, col)] = entry
                self.refresh_note_visibility(row, col)

        # Button frame
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(pady=20)

        new_btn = self._make_button(button_frame, "New Puzzle", self.new_puzzle_dialog,
                                     self.button_color, self.button_hover)
        new_btn.pack(side=tk.LEFT, padx=10)

        clear_btn = self._make_button(button_frame, "Clear Entries", self.clear_entries,
                                       self.button_color, self.button_hover)
        clear_btn.pack(side=tk.LEFT, padx=10)

        self.notes_toggle_btn = self._make_button(button_frame, "Notes: Off", self.toggle_notes_mode,
                                                    self.notes_off_color, self.notes_off_hover)
        self.notes_toggle_btn.pack(side=tk.LEFT, padx=10)

        check_btn = self._make_button(button_frame, "Check Solution", self.check_solution,
                                       self.button_color, self.button_hover)
        check_btn.pack(side=tk.LEFT, padx=10)

        self.timer_toggle_btn = self._make_button(button_frame, "Hide Timer", self.toggle_timer,
                                                    self.button_color, self.button_hover)
        self.timer_toggle_btn.pack(side=tk.LEFT, padx=10)

        music_btn = self._make_button(button_frame, "Music", self.open_music,
                                       self.music_color, self.music_hover)
        music_btn.pack(side=tk.LEFT, padx=10)

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
        # Stored on the widget (rather than only captured in the
        # lambdas below) so a caller can retint a button later --
        # e.g. the Notes toggle switching to green while active -- and
        # have hover/leave still pick up the new colors.
        btn._base_color = color
        btn._hover_color = hover_color
        btn.bind('<Enter>', lambda e: btn.config(bg=btn._hover_color))
        btn.bind('<Leave>', lambda e: btn.config(bg=btn._base_color))
        return btn

    # ---------------------------------------------------------------- timer
    def tick_timer(self):
        """Recurring 1-second tick that updates the elapsed-time label
        and refreshes this screen's alive-heartbeat."""
        elapsed = int(time.time() - self.start_time)
        mins, secs = divmod(elapsed, 60)
        self.timer_var.set(f"{mins:02d}:{secs:02d}")
        write_screen_pid(THIS_SCRIPT_PATH)
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

    # ---------------------------------------------------------------- notes
    def toggle_notes_mode(self):
        """Switch between normal entry and pencil-mark notes mode.
        While notes mode is on, typing a digit into an empty,
        non-clue cell toggles that digit as a small candidate note
        instead of filling in the cell's real answer."""
        self.notes_mode = not self.notes_mode
        btn = self.notes_toggle_btn
        if self.notes_mode:
            btn.config(text="Notes: On", bg=self.notes_on_color)
            btn._base_color = self.notes_on_color
            btn._hover_color = self.notes_on_hover
        else:
            btn.config(text="Notes: Off", bg=self.notes_off_color)
            btn._base_color = self.notes_off_color
            btn._hover_color = self.notes_off_hover

    def on_cell_keypress(self, row, col, event):
        """Intercept digit keys before they reach the Entry's own
        insert behavior, so that in notes mode they toggle a small
        candidate digit instead of changing the cell's real answer.
        Returning 'break' stops the keystroke from being inserted;
        returning None lets it proceed exactly as before."""
        if not self.notes_mode:
            return None

        if event.keysym in ('BackSpace', 'Delete'):
            entry = self.cell_entries[(row, col)]
            if entry.get().strip() == '' and self.notes.get((row, col)):
                self.notes[(row, col)] = set()
                self.update_note_label(row, col)
                self.refresh_note_visibility(row, col)
            return None

        if event.char and event.char.isdigit() and event.char != '0':
            entry = self.cell_entries[(row, col)]
            if entry.get().strip() != '':
                # This cell already holds a real answer -- notes only
                # apply to empty cells, so ignore the keystroke rather
                # than silently overwriting the answer with a note.
                return "break"
            self.toggle_note(row, col, event.char)
            self.refresh_note_visibility(row, col)
            return "break"

        # Anything else (arrow keys, Tab, ...) behaves as normal.
        return None

    def toggle_note(self, row, col, digit):
        """Add or remove a single candidate digit from a cell's notes
        and refresh its on-screen display."""
        notes = self.notes.setdefault((row, col), set())
        if digit in notes:
            notes.discard(digit)
        else:
            notes.add(digit)
        self.update_note_label(row, col)

    def update_note_label(self, row, col):
        """Refresh the 3x3 notes mini-grid for one cell to match
        self.notes -- each digit always shows in the same fixed
        position (1 top-left ... 9 bottom-right) so marks don't shift
        around as others are added or removed."""
        mini_labels = self.note_mini_labels.get((row, col))
        if mini_labels is None:
            return
        digits = self.notes.get((row, col), set())
        for digit, lbl in mini_labels.items():
            lbl.config(text=digit if digit in digits else "")

    def on_entry_focus_in(self, row, col):
        """Called the instant a cell's Entry gains keyboard focus --
        whether from a direct click on it, or indirectly via the notes
        grid's click-forwarding (it's on top of an empty cell and
        hands focus to the Entry without changing the visible layer).

        In normal mode, bring the Entry to the front so its cursor is
        visible and it's unambiguously what receives clicks/keys from
        here on -- exactly like before notes existed. In notes mode,
        leave the notes grid on top instead, so newly toggled pencil
        marks are visible immediately rather than hidden behind a
        blank, focused Entry until focus moves elsewhere."""
        if not self.notes_mode:
            self.cell_entries[(row, col)].lift()

    def refresh_note_visibility(self, row, col):
        """Show the pencil-mark mini-grid on top of the Entry only
        while the cell is empty. Once a real answer is typed, drop the
        notes grid behind the Entry so the big answer digit is what's
        actually visible -- the two never need to be seen at once."""
        note_frame = self.note_frames.get((row, col))
        if note_frame is None:
            return
        entry = self.cell_entries[(row, col)]
        if entry.get().strip() == '':
            note_frame.lift()
        else:
            note_frame.lower()

    def close_window(self):
        """Close the Sudoku window and return to the main launcher --
        reusing an already-running launcher window if there is one,
        instead of always spawning (and stacking) a fresh instance."""
        clear_screen_pid(THIS_SCRIPT_PATH)
        self.root.destroy()
        here = os.path.dirname(os.path.abspath(__file__))
        launcher_path = os.path.join(here, "PuzzlerzGame.py")
        if not open_or_focus_screen(launcher_path, "Puzzlerz Game", here):
            print("Failed to return to PuzzlerzGame.py -- see console for details.")

    def open_music(self):
        """Open the Music window, or bring an already-running one to
        the front instead of spawning a duplicate track."""
        here = os.path.dirname(os.path.abspath(__file__))
        caller_path = os.path.abspath(__file__)
        if not open_or_focus_music(here, caller_path):
            messagebox.showerror("Music Error", "Cannot open Music -- see console for details.")

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
        self.solution = (
            deepcopy(self.generator.solution)
            if self.generator.solution is not None
            else self.solve_sudoku(self.original_puzzle)
        )
        self.error_cells = set()
        self.notes = {(r, c): set() for r in range(9) for c in range(9)}

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
                entry.unbind('<KeyPress>')
                entry.unbind('<FocusIn>')
                entry.unbind('<FocusOut>')

                # New puzzle, so any leftover pencil marks from the
                # previous one no longer apply -- clear the display too.
                note_frame = self.note_frames.get((row, col))
                if note_frame is not None:
                    note_frame.config(bg=cell_bg)
                for lbl in self.note_mini_labels.get((row, col), {}).values():
                    lbl.config(text="", bg=cell_bg)

                if is_clue:
                    entry.config(state='readonly', readonlybackground=cell_bg)
                else:
                    entry.bind('<KeyRelease>', lambda e, r=row, c=col: self.on_cell_change(r, c, e))
                    entry.bind('<KeyPress>', lambda e, r=row, c=col: self.on_cell_keypress(r, c, e))
                    entry.bind('<FocusIn>', lambda e, r=row, c=col: self.on_entry_focus_in(r, c))
                    entry.bind('<FocusOut>', lambda e, r=row, c=col: self.refresh_note_visibility(r, c))

                self.refresh_note_visibility(row, col)

    def on_cell_change(self, row, col, event):
        """Handle cell input changes and update user grid"""
        # Any edit invalidates the last "Check Solution" highlighting,
        # since the conflicts that were flagged may no longer apply.
        if self.error_cells:
            self.clear_error_highlights()

        entry = self.cell_entries[(row, col)]
        value = entry.get().strip()

        if value:
            self.user_grid[row][col] = int(value)
            # A real answer makes any pencil-mark notes for this cell
            # moot -- clear them so they don't linger underneath it.
            if self.notes.get((row, col)):
                self.notes[(row, col)] = set()
                self.update_note_label(row, col)
        else:
            self.user_grid[row][col] = 0

        self.refresh_note_visibility(row, col)

    def clear_entries(self):
        """Clear all user entries, keep clues"""
        self.clear_error_highlights()
        for row in range(9):
            for col in range(9):
                if self.original_puzzle[row][col] == 0:  # Only clear user-entered cells
                    entry = self.cell_entries[(row, col)]
                    entry.config(state='normal')
                    entry.delete(0, tk.END)
                    self.user_grid[row][col] = 0
                    self.notes[(row, col)] = set()
                    self.update_note_label(row, col)
                    self.refresh_note_visibility(row, col)

    # ---------------------------------------------------------- highlighting
    def normal_cell_color(self, row, col):
        """The color a cell should show when it isn't flagged as an
        error -- the clue tint for givens, plain white otherwise."""
        return self.clue_color if self.original_puzzle[row][col] != 0 else self.input_color

    def set_cell_color(self, row, col, color):
        """Set a cell's background, accounting for readonly (clue)
        cells needing 'readonlybackground' instead of 'bg'. Also keeps
        the notes mini-grid in sync so a highlighted cell doesn't show
        a mismatched patch of color behind its pencil marks."""
        entry = self.cell_entries[(row, col)]
        if self.original_puzzle[row][col] != 0:
            entry.config(readonlybackground=color)
        else:
            entry.config(bg=color)
        note_frame = self.note_frames.get((row, col))
        if note_frame is not None:
            note_frame.config(bg=color)
        for lbl in self.note_mini_labels.get((row, col), {}).values():
            lbl.config(bg=color)

    def clear_error_highlights(self):
        """Revert every currently-highlighted cell back to its normal
        color and forget the highlight set."""
        for (r, c) in self.error_cells:
            self.set_cell_color(r, c, self.normal_cell_color(r, c))
        self.error_cells = set()

    @staticmethod
    def solve_sudoku(clue_grid):
        """Fallback solver, used only if self.generator.solution ever
        turns out to be missing -- normally sudoku_gen.py's own
        generate() already builds and verifies a unique solution and
        hands it back via self.generator.solution, which is what
        __init__/generate_new_puzzle actually use.

        Solves a Sudoku from its clues alone via plain backtracking
        with a most-constrained-cell heuristic (picking the
        emptiest-of-options cell first), which keeps it fast even for
        low-clue "hard" puzzles. Returns a fully solved 9x9 grid, or
        None if the clues turned out not to have a solution."""
        board = [row[:] for row in clue_grid]

        def candidates(r, c):
            used = set(board[r])
            used.update(board[i][c] for i in range(9))
            br, bc = 3 * (r // 3), 3 * (c // 3)
            used.update(
                board[br + i][bc + j]
                for i in range(3) for j in range(3)
            )
            return [v for v in range(1, 10) if v not in used]

        def find_best_empty():
            best_cell = None
            best_candidates = None
            for r in range(9):
                for c in range(9):
                    if board[r][c] != 0:
                        continue
                    opts = candidates(r, c)
                    if best_candidates is None or len(opts) < len(best_candidates):
                        best_cell, best_candidates = (r, c), opts
                        if not opts:
                            return best_cell, best_candidates
            return best_cell, best_candidates

        def backtrack():
            cell, opts = find_best_empty()
            if cell is None:
                return True  # no empty cells left -- solved
            if not opts:
                return False  # dead end -- this cell has no legal digit
            r, c = cell
            for v in opts:
                board[r][c] = v
                if backtrack():
                    return True
                board[r][c] = 0
            return False

        return board if backtrack() else None

    def find_conflicts(self):
        """Return the set of (row, col) cells whose value duplicates
        another cell's value within the same row, column, or 3x3 box.
        Zeros (empty cells) are ignored. Used only as a fallback by
        check_solution() for the unlikely case solve_sudoku() couldn't
        find this puzzle's actual solution -- normally the direct
        cell-by-cell comparison against self.solution is used
        instead, since a conflict-free grid can still disagree with
        the puzzle's actual (unique) solution."""
        conflicts = set()
        grid = self.user_grid

        # Rows
        for r in range(9):
            seen = {}
            for c in range(9):
                v = grid[r][c]
                if v == 0:
                    continue
                seen.setdefault(v, []).append((r, c))
            for cells in seen.values():
                if len(cells) > 1:
                    conflicts.update(cells)

        # Columns
        for c in range(9):
            seen = {}
            for r in range(9):
                v = grid[r][c]
                if v == 0:
                    continue
                seen.setdefault(v, []).append((r, c))
            for cells in seen.values():
                if len(cells) > 1:
                    conflicts.update(cells)

        # 3x3 boxes
        for box_row in range(3):
            for box_col in range(3):
                seen = {}
                for i in range(3):
                    for j in range(3):
                        r = box_row * 3 + i
                        c = box_col * 3 + j
                        v = grid[r][c]
                        if v == 0:
                            continue
                        seen.setdefault(v, []).append((r, c))
                for cells in seen.values():
                    if len(cells) > 1:
                        conflicts.update(cells)

        return conflicts

    def check_solution(self):
        """Check the current grid strictly against this puzzle's own
        solution: a cell is flagged in red if and only if it disagrees
        with the solution at that position -- so each cell is judged
        independently against the answer key, rather than only being
        flagged when it happens to conflict with another cell in its
        row/column/box. (A grid can be conflict-free by that older
        definition and still be wrong, e.g. two cells swapped with a
        third that only clashes with one of them.)"""
        for row in range(9):
            for col in range(9):
                if self.user_grid[row][col] == 0:
                    messagebox.showwarning("Incomplete", "Please fill all cells!")
                    return

        # Clear any highlights left over from a previous check before
        # computing and applying the current set.
        self.clear_error_highlights()

        if self.solution is not None:
            incorrect = {
                (r, c)
                for r in range(9) for c in range(9)
                if self.user_grid[r][c] != self.solution[r][c]
            }
        else:
            # Extremely unlikely fallback: we couldn't derive a
            # solution for this puzzle's clues, so fall back to
            # flagging rule conflicts instead of leaving Check
            # Solution unable to say anything at all.
            incorrect = self.find_conflicts()

        if incorrect:
            self.error_cells = incorrect
            for (r, c) in incorrect:
                self.set_cell_color(r, c, self.error_color)
            messagebox.showerror(
                "Error",
                "There is an error in the puzzle. The incorrect cells are highlighted in red."
            )
            return

        # Every cell filled and every cell matches the solution.
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
        clear_screen_pid(THIS_SCRIPT_PATH)
        self.root.destroy()


# Create and run popup
if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuPopup(root)
    root.mainloop()