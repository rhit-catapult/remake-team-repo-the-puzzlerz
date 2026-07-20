import os
import pygame

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Puzzlerz Game")
clock = pygame.time.Clock()
title_font = pygame.font.SysFont(None, 72)
button_font = pygame.font.SysFont(None, 40)


def draw_puzzle_piece(surface, x, y, color, outline_color, flip=False):
    width, height = 160, 112
    tab_radius = 24
    bg_color = (245, 248, 255)

    body = pygame.Rect(x, y - height, width, height)
    shadow = body.move(6, 6)
    pygame.draw.rect(surface, (200, 210, 230), shadow, border_radius=24)
    pygame.draw.rect(surface, color, body, border_radius=20)

    edge_centers = {
        "top": (x + width // 2, y - height),
        "bottom": (x + width // 2, y),
        "left": (x, y - height // 2),
        "right": (x + width, y - height // 2),
    }

    def draw_tab(edge):
        connector_center = edge_centers[edge]
        pygame.draw.circle(surface, color, connector_center, tab_radius)
        pygame.draw.circle(surface, outline_color, connector_center, tab_radius, width=5)

    def draw_socket(edge):
        if edge == "top":
            socket_center = (edge_centers[edge][0], edge_centers[edge][1] + tab_radius // 2)
        elif edge == "bottom":
            socket_center = (edge_centers[edge][0], edge_centers[edge][1] - tab_radius // 2)
        elif edge == "left":
            socket_center = (edge_centers[edge][0] + tab_radius // 2, edge_centers[edge][1])
        else:
            socket_center = (edge_centers[edge][0] - tab_radius // 2, edge_centers[edge][1])
        pygame.draw.circle(surface, bg_color, socket_center, tab_radius)
        pygame.draw.circle(surface, outline_color, socket_center, tab_radius, width=5)
        pygame.draw.circle(surface, bg_color, socket_center, max(tab_radius - 10, 1))

    if not flip:
        tab_edges = ["top", "right"]
        socket_edges = ["left", "bottom"]
    else:
        tab_edges = ["top", "left"]
        socket_edges = ["right", "bottom"]

    for edge in tab_edges:
        draw_tab(edge)
    for edge in socket_edges:
        draw_socket(edge)

    pygame.draw.rect(surface, outline_color, body, width=5, border_radius=20)
    pygame.draw.line(surface, (255, 255, 255), (x + 18, y - height + 22), (x + width - 18, y - height + 22), 4)
    pygame.draw.line(surface, (255, 255, 255), (x + 20, y - height + 44), (x + width - 20, y - height + 44), 2)


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((245, 248, 255))

    title_surface = title_font.render("Puzzlr", True, (40, 40, 100))
    title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 50))
    screen.blit(title_surface, title_rect)

    button_texts = ["Sudoku", "Crossword", "Word Search"]
    button_width = 320
    button_height = 60
    button_spacing = 18
    button_x = (screen.get_width() - button_width) // 2
    button_y = 115
    button_color = (220, 230, 250)
    button_border = (70, 80, 150)

    for text in button_texts:
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        pygame.draw.rect(screen, button_color, button_rect, border_radius=18)
        pygame.draw.rect(screen, button_border, button_rect, width=4, border_radius=18)

        label_surface = button_font.render(text, True, (30, 30, 80))
        label_rect = label_surface.get_rect(center=button_rect.center)
        screen.blit(label_surface, label_rect)

        button_y += button_height + button_spacing

    draw_puzzle_piece(screen, 14, screen.get_height() - 16, (72, 144, 240), (30, 70, 140), flip=False)
    draw_puzzle_piece(screen, screen.get_width() - 174, screen.get_height() - 16, (140, 80, 220), (80, 40, 140), flip=True)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()

