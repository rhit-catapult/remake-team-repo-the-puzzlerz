import os
import pygame
import tkinter as tk
from tkinter import font, messagebox, simpledialog
from sudoku_gen import SudokuGen
import subprocess
import sys
import tempfile
import time
import signal
from process_utils import launch_detached

# Only init display + font here -- NOT the full pygame.init(), so this
# process never touches the audio device and can't interrupt whatever
# is currently playing in Music.py.
pygame.display.init()
pygame.font.init()

MUSIC_PID_PATH = os.path.join(tempfile.gettempdir(), "puzzlerz_music.pid")


def music_already_running():
    """True if Music.py's heartbeat file was touched recently, meaning
    a Music process is alive (and playing) somewhere right now."""
    try:
        mtime = os.path.getmtime(MUSIC_PID_PATH)
    except OSError:
        return False
    return (time.time() - mtime) < 3


def stop_music_process():
    """Terminate the background Music.py process (if any). Called only
    when the whole Puzzlerz app is being closed -- not when simply
    navigating to a puzzle -- so music stops exactly when you exit."""
    try:
        with open(MUSIC_PID_PATH, "r") as f:
            pid = int(f.read().strip())
    except (OSError, ValueError):
        return
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass  # already gone
    try:
        os.remove(MUSIC_PID_PATH)
    except OSError:
        pass


def focus_music_window():
    """Bring the already-running Music window to the front, restoring
    it if minimized. This is platform-specific since there's no
    cross-process 'focus that window' API in pygame -- each branch
    fails silently if the needed tool isn't available."""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.FindWindowW(None, "Music")
            if hwnd:
                SW_RESTORE = 9
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.SetForegroundWindow(hwnd)
        except Exception:
            pass
    elif sys.platform.startswith("linux"):
        # Requires wmctrl (common on most desktop Linux distros).
        try:
            subprocess.Popen(["wmctrl", "-a", "Music"])
        except Exception:
            pass
    elif sys.platform == "darwin":
        # Best-effort: ask System Events to raise any window titled
        # "Music" belonging to a Python process.
        try:
            script = (
                'tell application "System Events"\n'
                '  set procs to processes whose name contains "Python"\n'
                '  repeat with p in procs\n'
                '    try\n'
                '      set frontmost of p to true\n'
                '      exit repeat\n'
                '    end try\n'
                '  end repeat\n'
                'end tell'
            )
            subprocess.Popen(["osascript", "-e", script])
        except Exception:
            pass


info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
pygame.display.set_caption("Puzzlerz Game")


def _load_piece_image(filename):
    """Look for filename at project root, assets/, samples/, or
    samples/sample_posters/, anchored to this script's own directory
    so it works no matter what the current working directory is.
    Must run AFTER pygame.display.set_mode(), since convert_alpha()
    needs a display surface to already exist."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidate_paths = (
        os.path.join(here, filename),
        os.path.join(here, "assets", filename),
        os.path.join(here, "samples", filename),
        os.path.join(here, "samples", "sample_posters", filename),
    )
    for p in candidate_paths:
        if os.path.exists(p):
            try:
                return pygame.image.load(p).convert_alpha()
            except Exception as e:
                print(f"Failed to load image from {p}: {e}")
    print(f"No image found for {filename}. Checked:", candidate_paths)
    return None


# Six background puzzle-piece accents, scattered around the edges of
# the screen, plus the blue/lavender pair spread across the bottom.
# Any that fail to load are simply skipped, so a missing file doesn't
# crash the game -- it just means one fewer piece appears.
_piece_filenames = [
    "BrownPuzzlePiece.png",
    "DarkerbluePuzzlePiece.png",
    "GreenPuzzlePiece.png",
    "OrangePuzzlePiece.png",
    "PinkPuzzlePiece.png",
    "YellowPuzzlePiece.png",
]
piece_images = [img for img in (_load_piece_image(f) for f in _piece_filenames) if img is not None]

jigsaw_image_left = _load_piece_image("blue_puzzle_piece.png")
jigsaw_image_right = _load_piece_image("LavenderPuzzlePiece.png")

# Each entry: (image, x_fraction, y_fraction, target_width_px,
# rotation_degrees, alpha). Fractions are of screen width/height, so
# this scales to any resolution. Positions keep clear of the title and
# the vertical button column in the center of the screen.
background_scatter = []
_scatter_slots = [
    (0.05, 0.16, 150, -12, 235),
    (0.93, 0.12, 130, 16, 235),
    (0.04, 0.50, 140, 10, 235),
    (0.95, 0.46, 150, -18, 235),
    (0.08, 0.86, 160, 14, 235),
    (0.90, 0.84, 140, -9, 235),
]
for img, slot in zip(piece_images, _scatter_slots):
    xf, yf, target_w, angle, alpha = slot
    background_scatter.append((img, xf, yf, target_w, angle, alpha))

# Blue + lavender pair, matching the same target width/alpha as the
# other scattered pieces, spread evenly across the bottom of the
# screen instead of sitting side-by-side at dead center.
if jigsaw_image_left:
    background_scatter.append((jigsaw_image_left, 0.32, 0.93, 150, 0, 235))
if jigsaw_image_right:
    background_scatter.append((jigsaw_image_right, 0.68, 0.93, 150, 0, 235))


def draw_background_pieces(surface):
    """Draw all scattered puzzle-piece accents as a background layer,
    behind the title and buttons. Skips silently if no piece images
    loaded at all."""
    if not background_scatter:
        return
    sw, sh = surface.get_width(), surface.get_height()
    for img, xf, yf, target_w, angle, alpha in background_scatter:
        scale = target_w / img.get_width()
        target_h = max(1, int(img.get_height() * scale))
        scaled = pygame.transform.smoothscale(img, (target_w, target_h))
        if angle:
            scaled = pygame.transform.rotate(scaled, angle)
        scaled.set_alpha(alpha)
        rect = scaled.get_rect(center=(int(sw * xf), int(sh * yf)))
        surface.blit(scaled, rect)


clock = pygame.time.Clock()
title_font = pygame.font.SysFont(None, 170)
button_font = pygame.font.SysFont(None, 48)

running = True
exiting_app = False  # True only for a genuine app-close, not puzzle navigation

while running:
    button_texts = ["Sudoku", "Crossword", "Word Search"]
    button_width = 390
    button_height = 78
    button_spacing = 22
    button_x = (screen.get_width() - button_width) // 2
    button_y = max(180, (screen.get_height() // 2) - (((len(button_texts) * button_height) + ((len(button_texts) - 1) * button_spacing)) // 2) + 20)
    button_color = (240, 246, 255)
    button_border = (70, 90, 160)
    button_text_color = (25, 35, 85)
    x_button_rect = pygame.Rect(20, 20, 58, 58)
    music_button_rect = pygame.Rect(screen.get_width() - 220, 20, 180, 58)

    button_rects = []
    temp_y = button_y
    for text in button_texts:
        button_rects.append((text, pygame.Rect(button_x, temp_y, button_width, button_height)))
        temp_y += button_height + button_spacing

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            exiting_app = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if x_button_rect.collidepoint((mx, my)):
                running = False
                exiting_app = True
            elif music_button_rect.collidepoint((mx, my)):
                if music_already_running():
                    # Already playing somewhere -- bring it to the
                    # front instead of spawning a duplicate track.
                    focus_music_window()
                else:
                    try:
                        here = os.path.dirname(os.path.abspath(__file__))
                        music_path = os.path.join(here, 'Music.py')
                        launch_detached([sys.executable, music_path], cwd=here)
                    except Exception as e:
                        messagebox.showerror("Music Error", f"Cannot open Music: {e}")
            else:
                for t, rect in button_rects:
                    if rect.collidepoint((mx, my)):
                        launched = False
                        if t == "Sudoku":
                            try:
                                here = os.path.dirname(os.path.abspath(__file__))
                                sudoku_path = os.path.join(here, 'Sudoku.py')
                                launch_detached([sys.executable, sudoku_path], cwd=here)
                                launched = True
                            except Exception as e:
                                messagebox.showerror("Sudoku Error", f"Cannot open Sudoku: {e}")
                        elif t == "Crossword":
                            try:
                                here = os.path.dirname(os.path.abspath(__file__))
                                crossword_path = os.path.join(here, 'Crossword.py')
                                launch_detached([sys.executable, crossword_path], cwd=here)
                                launched = True
                            except Exception as e:
                                messagebox.showerror("Crossword Error", f"Cannot open Crossword: {e}")
                        elif t == "Word Search":
                            try:
                                here = os.path.dirname(os.path.abspath(__file__))
                                word_search_path = os.path.join(here, 'Word_Search.py')
                                launch_detached([sys.executable, word_search_path], cwd=here)
                                launched = True
                            except Exception as e:
                                messagebox.showerror("Word Search Error", f"Cannot open Word Search: {e}")

                        # Close this launcher window once a puzzle has
                        # opened, so exactly one window is ever on
                        # screen -- no stacked launcher copies. Music
                        # is untouched here since this is navigation,
                        # not exiting the app.
                        if launched:
                            running = False

    # Once running is False we're about to tear the display down --
    # skip drawing entirely so we never touch a surface that pygame
    # is in the middle of releasing.
    if not running:
        continue

    screen.fill((255, 255, 255))

    # Background accent layer -- drawn first so the title/buttons sit
    # on top of it.
    draw_background_pieces(screen)

    title_surface = title_font.render("Puzzlr", True, (0, 170, 170))
    title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 115))
    screen.blit(title_surface, title_rect)

    pygame.draw.rect(screen, (220, 20, 20), x_button_rect, border_radius=16)
    pygame.draw.rect(screen, (255, 255, 255), x_button_rect, width=3, border_radius=16)
    x_surface = button_font.render("X", True, (255, 255, 255))
    x_rect = x_surface.get_rect(center=x_button_rect.center)
    screen.blit(x_surface, x_rect)

    pygame.draw.rect(screen, (130, 140, 150), music_button_rect, border_radius=18)
    pygame.draw.rect(screen, (80, 90, 100), music_button_rect, width=3, border_radius=18)
    music_surface = button_font.render("Music", True, (255, 255, 255))
    music_rect = music_surface.get_rect(center=music_button_rect.center)
    screen.blit(music_surface, music_rect)

    for text, button_rect in button_rects:
        shadow_rect = button_rect.move(0, 6)
        pygame.draw.rect(screen, (220, 225, 235), shadow_rect, border_radius=18)
        pygame.draw.rect(screen, button_color, button_rect, border_radius=18)
        pygame.draw.rect(screen, button_border, button_rect, width=3, border_radius=18)
        label_surface = button_font.render(text, True, button_text_color)
        label_rect = label_surface.get_rect(center=button_rect.center)
        screen.blit(label_surface, label_rect)

    pygame.display.flip()
    clock.tick(60)

if exiting_app:
    stop_music_process()

pygame.quit()