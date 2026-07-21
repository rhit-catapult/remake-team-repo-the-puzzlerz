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


# Try to load the puzzle-piece image (place your file at project root
# or in an assets/ subfolder -- the filename below matches the upload
# exactly, underscores included).

info = pygame.display.Info()
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)
pygame.display.set_caption("Puzzlerz Game")

jigsaw_image = None
_here = os.path.dirname(os.path.abspath(__file__))
_jigsaw_paths = (
    os.path.join(_here, "blue_puzzle_piece.png"),
    os.path.join(_here, "assets", "blue_puzzle_piece.png"),
    os.path.join(_here, "samples", "blue_puzzle_piece.png"),
    os.path.join(_here, "samples", "sample_posters", "blue_puzzle_piece.png"),
)
for _p in _jigsaw_paths:
    if os.path.exists(_p):
        try:
            jigsaw_image = pygame.image.load(_p).convert_alpha()
            break
        except Exception as e:
            print(f"Failed to load jigsaw image from {_p}: {e}")
            jigsaw_image = None
if jigsaw_image is None:
    print("No puzzle-piece image found. Checked:", _jigsaw_paths)

clock = pygame.time.Clock()
title_font = pygame.font.SysFont(None, 170)
button_font = pygame.font.SysFont(None, 48)


def draw_puzzle_piece(surface, x, y, color, outline_color, flip=False):
    width, height = 287, 187
    body = pygame.Rect(x, y - height, width, height)

    # If the puzzle-piece image is available, use it (image should
    # include a transparent background, which the processed file does).
    if jigsaw_image:
        img = pygame.transform.smoothscale(jigsaw_image, (width, height))
        if flip:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, (x, y - height))
        return

    # Fallback: if the image isn't found, draw a simple placeholder
    # rounded rect so the corner isn't left completely blank.
    pygame.draw.rect(surface, color, body, border_radius=22)
    pygame.draw.rect(surface, outline_color, body, width=2, border_radius=22)


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
                        music_path = os.path.join(os.path.dirname(__file__), 'Music.py')
                        subprocess.Popen([sys.executable, music_path])
                    except Exception as e:
                        messagebox.showerror("Music Error", f"Cannot open Music: {e}")
            else:
                for t, rect in button_rects:
                    if rect.collidepoint((mx, my)):
                        launched = False
                        if t == "Sudoku":
                            try:
                                sudoku_path = os.path.join(os.path.dirname(__file__), 'Sudoku.py')
                                subprocess.Popen([sys.executable, sudoku_path])
                                launched = True
                            except Exception as e:
                                messagebox.showerror("Sudoku Error", f"Cannot open Sudoku: {e}")
                        elif t == "Crossword":
                            try:
                                crossword_path = os.path.join(os.path.dirname(__file__), 'Crossword.py')
                                subprocess.Popen([sys.executable, crossword_path])
                                launched = True
                            except Exception as e:
                                messagebox.showerror("Crossword Error", f"Cannot open Crossword: {e}")
                        elif t == "Word Search":
                            try:
                                word_search_path = os.path.join(os.path.dirname(__file__), 'Word_Search.py')
                                subprocess.Popen([sys.executable, word_search_path])
                                launched = True
                            except Exception as e:
                                messagebox.showerror("Word Search Error", f"Cannot open Word Search: {e}")

                        if launched:
                            running = False

    screen.fill((255, 255, 255))

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

    draw_puzzle_piece(screen, 8, screen.get_height() - 12, (72, 144, 240), (30, 70, 140), flip=False)
    draw_puzzle_piece(screen, screen.get_width() - 301, screen.get_height() - 12, (140, 80, 220), (80, 40, 140),
                      flip=True)

    pygame.display.flip()
    clock.tick(60)

if exiting_app:
    stop_music_process()

pygame.quit()