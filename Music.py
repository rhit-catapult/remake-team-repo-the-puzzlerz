import pygame


# Initialize all imported pygame modules
pygame.init()

# Create the window surface (width, height)
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Music")

# Game loop control flag



clock = pygame.time.Clock()
title_font = pygame.font.SysFont(None, 72)
button_font = pygame.font.SysFont(None, 40)

running=True
while running:
    button_texts = ["Ambient", "Classical", "Jazz", "Upbeat"]
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
                    if t == "Ambient":
                        pygame.mixer.music.load("Ambient.mp3")
                        pygame.mixer.music.play(-1)  # -1 = loop forever
                    elif t == "Classical":
                        pygame.mixer.music.load("Classical.mp3")
                        pygame.mixer.music.play(-1)  # -1 = loop forever
                    elif t == "Jazz":
                        pygame.mixer.music.load("Jazz.mp3")
                        pygame.mixer.music.play(-1)  # -1 = loop forever
                    elif t== "Upbeat":
                        pygame.mixer.music.load("Upbeat.mp3")
                        pygame.mixer.music.play(-1)  # -1 = loop forever

    screen.fill((255, 255, 255))

    # Draw buttons and labels
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

# Uninitialize pygame modules cleanly before closing script
pygame.quit()