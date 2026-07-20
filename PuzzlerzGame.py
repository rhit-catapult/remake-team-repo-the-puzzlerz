import os
import pygame
import tkinter as tk
from tkinter import font, messagebox, simpledialog
from sudoku_gen import SudokuGen
import subprocess
import sys

pygame.init()
# Try to load a jigsaw outline image (place your image at project root or in assets/)
jigsaw_image = None
_jigsaw_paths = (
    "jigsaw_outline.png",
    os.path.join("assets", "jigsaw_outline.png"),
    os.path.join("samples", "jigsaw_outline.png"),
    os.path.join("samples", "sample_posters", "jigsaw_outline.png"),
)
for _p in _jigsaw_paths:
    if os.path.exists(_p):
        try:
            jigsaw_image = pygame.image.load(_p).convert_alpha()
            break
        except Exception:
            jigsaw_image = None
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Puzzlerz Game")
clock = pygame.time.Clock()
title_font = pygame.font.SysFont(None, 72)
button_font = pygame.font.SysFont(None, 40)


def draw_puzzle_piece(surface, x, y, color, outline_color, flip=False):
    width, height = 172, 112
    body = pygame.Rect(x, y - height, width, height)
    shadow = body.move(6, 6)
    pygame.draw.rect(surface, (206, 216, 232), shadow, border_radius=26)

    # If a jigsaw outline image is available, use it (image should include transparent background)
    if jigsaw_image:
        pygame.draw.rect(surface, color, body, border_radius=22)
        img = pygame.transform.smoothscale(jigsaw_image, (width, height))
        if flip:
            img = pygame.transform.flip(img, True, False)
        surface.blit(img, (x, y - height))
        pygame.draw.rect(surface, outline_color, body, width=2, border_radius=22)
        return

    # Fallback: draw a more literal jigsaw piece with a protruding tab and a square-edged socket.
    bg_color = (255, 255, 255)
    tab_w = 42
    tab_h = 28

    pygame.draw.rect(surface, color, body, border_radius=22)

    # Draw the outer border only on the shaded region around the edge of the piece.
    pygame.draw.rect(surface, outline_color, (x + 2, y - height + 2, width - 4, height - 4), width=3, border_radius=18)

    # Top tab
    pygame.draw.rect(surface, color, (x + width // 2 - tab_w // 2, y - height - tab_h // 2, tab_w, tab_h))
    pygame.draw.rect(surface, outline_color, (x + width // 2 - tab_w // 2, y - height - tab_h // 2, tab_w, tab_h), width=3)

    # Right tab
    pygame.draw.rect(surface, color, (x + width - tab_h // 2, y - height // 2 - tab_w // 2, tab_h, tab_w))
    pygame.draw.rect(surface, outline_color, (x + width - tab_h // 2, y - height // 2 - tab_w // 2, tab_h, tab_w), width=3)

    # Left socket (blends into the background)
    pygame.draw.rect(surface, bg_color, (x - 8, y - height // 2 - 16, 20, 32))
    pygame.draw.line(surface, (255, 255, 255), (x - 8, y - height // 2 - 16), (x - 8, y - height // 2 + 16), 3)
    pygame.draw.line(surface, (255, 255, 255), (x + 12, y - height // 2 - 16), (x + 12, y - height // 2 + 16), 3)

    # Bottom socket (blends into the background)
    pygame.draw.rect(surface, bg_color, (x + width // 2 - 16, y - 8, 32, 20))
    pygame.draw.line(surface, (255, 255, 255), (x + width // 2 - 16, y - 8), (x + width // 2 + 16, y - 8), 3)
    pygame.draw.line(surface, (255, 255, 255), (x + width // 2 - 16, y + 12), (x + width // 2 + 16, y + 12), 3)

    # Add a small highlight line to suggest a puzzle edge.
    pygame.draw.line(surface, (255, 255, 255), (x + 16, y - height + 18), (x + width - 16, y - height + 18), 3)
    pygame.draw.line(surface, (255, 255, 255), (x + 18, y - height + 38), (x + width - 18, y - height + 38), 2)


running = True
while running:
    button_texts = ["Sudoku", "Crossword", "Word Search"]
    button_width = 320
    button_height = 60
    button_spacing = 18
    button_x = (screen.get_width() - button_width) // 2
    button_y = 115
    button_color = (240, 246, 255)
    button_border = (70, 90, 160)
    button_text_color = (25, 35, 85)

    # Create button rects before handling events so clicks map correctly
    button_rects = []
    temp_y = button_y
    for text in button_texts:
        button_rects.append((text, pygame.Rect(button_x, temp_y, button_width, button_height)))
        temp_y += button_height + button_spacing

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # detect which button was clicked
            for t, rect in button_rects:
                if rect.collidepoint((mx, my)):
                    if t == "Sudoku":
                        # Launch Sudoku popup in a separate Python process to avoid mixing GUI loops
                        try:
                            sudoku_path = os.path.join(os.path.dirname(__file__), 'Sudoku.py')
                            subprocess.Popen([sys.executable, sudoku_path])
                        except Exception as e:
                            messagebox.showerror("Sudoku Error", f"Cannot open Sudoku: {e}")
                    elif t == "Word Search":
                        try:
                            word_search_path = os.path.join(os.path.dirname(__file__), 'Word_Search.py')
                            subprocess.Popen([sys.executable, word_search_path])
                        except Exception as e:
                            messagebox.showerror("Word Search Error", f"Cannot open Word Search: {e}")

    screen.fill((255, 255, 255))

    title_surface = title_font.render("Puzzlr", True, (40, 40, 100))
    title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 50))
    screen.blit(title_surface, title_rect)

    # Draw buttons and labels
    for text, button_rect in button_rects:
        shadow_rect = button_rect.move(0, 6)
        pygame.draw.rect(screen, (220, 225, 235), shadow_rect, border_radius=18)
        pygame.draw.rect(screen, button_color, button_rect, border_radius=18)
        pygame.draw.rect(screen, button_border, button_rect, width=3, border_radius=18)
        label_surface = button_font.render(text, True, button_text_color)
        label_rect = label_surface.get_rect(center=button_rect.center)
        screen.blit(label_surface, label_rect)

    draw_puzzle_piece(screen, 8, screen.get_height() - 12, (72, 144, 240), (30, 70, 140), flip=False)
    draw_puzzle_piece(screen, screen.get_width() - 186, screen.get_height() - 12, (140, 80, 220), (80, 40, 140), flip=True)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()