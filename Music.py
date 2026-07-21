import pygame


# Initialize all imported pygame modules
pygame.init()

# Create the window surface (width, height)
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Music")

clock = pygame.time.Clock()
title_font = pygame.font.SysFont(None, 72)
button_font = pygame.font.SysFont(None, 40)
small_font = pygame.font.SysFont(None, 28)

running = True

# Master volume, controlled by the slider (0.0 - 1.0)
current_volume = 0.125
dragging_slider = False

while running:
    button_texts = ["Ambient", "Classical", "Jazz", "Upbeat", "Mute"]
    button_width = 320
    button_height = 60
    button_spacing = 18
    button_x = (screen.get_width() - button_width) // 2
    button_y = 115
    button_color = (240, 246, 255)
    button_border = (70, 90, 160)
    button_text_color = (25, 35, 85)

    # Special styling for the Mute button (red)
    mute_button_color = (225, 60, 60)
    mute_button_border = (140, 20, 20)
    mute_text_color = (255, 255, 255)

    # Create button rects before handling events so clicks map correctly
    button_rects = []
    temp_y = button_y
    for text in button_texts:
        button_rects.append((text, pygame.Rect(button_x, temp_y, button_width, button_height)))
        temp_y += button_height + button_spacing

    # --- Volume slider layout ---
    slider_width = 320
    slider_x = (screen.get_width() - slider_width) // 2
    slider_y = temp_y + 30
    slider_track_rect = pygame.Rect(slider_x, slider_y, slider_width, 8)
    handle_radius = 12
    handle_x = slider_x + int(current_volume * slider_width)
    handle_center = (handle_x, slider_y + 4)
    handle_rect = pygame.Rect(0, 0, handle_radius * 2, handle_radius * 2)
    handle_rect.center = handle_center

    # --- Close button (top-right corner) ---
    close_button_rect = pygame.Rect(screen.get_width() - 100, 15, 85, 35)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Close button
            if close_button_rect.collidepoint((mx, my)):
                running = False

            # Volume slider - clicking the track or handle starts dragging
            elif slider_track_rect.inflate(0, 20).collidepoint((mx, my)) or handle_rect.collidepoint((mx, my)):
                dragging_slider = True
                rel_x = min(max(mx - slider_x, 0), slider_width)
                current_volume = rel_x / slider_width
                pygame.mixer.music.set_volume(current_volume)

            else:
                # detect which music button was clicked
                for t, rect in button_rects:
                    if rect.collidepoint((mx, my)):
                        if t == "Ambient":
                            pygame.mixer.music.load("Ambient.mp3")
                            pygame.mixer.music.play(-1)  # -1 = loop forever
                            pygame.mixer.music.set_volume(current_volume)
                        elif t == "Classical":
                            pygame.mixer.music.load("Classical.mp3")
                            pygame.mixer.music.play(-1)  # -1 = loop forever
                            pygame.mixer.music.set_volume(current_volume)
                        elif t == "Jazz":
                            pygame.mixer.music.load("Jazz.mp3")
                            pygame.mixer.music.play(-1)  # -1 = loop forever
                            pygame.mixer.music.set_volume(current_volume)
                        elif t == "Upbeat":
                            pygame.mixer.music.load("Upbeat.mp3")
                            pygame.mixer.music.play(-1)  # -1 = loop forever
                            pygame.mixer.music.set_volume(current_volume)
                        elif t == "Mute":
                            pygame.mixer.music.set_volume(0)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            dragging_slider = False

        elif event.type == pygame.MOUSEMOTION and dragging_slider:
            mx, my = event.pos
            rel_x = min(max(mx - slider_x, 0), slider_width)
            current_volume = rel_x / slider_width
            pygame.mixer.music.set_volume(current_volume)

    screen.fill((255, 255, 255))

    title_surface = title_font.render("Music", True, (40, 40, 100))
    title_rect = title_surface.get_rect(center=(screen.get_width() // 2, 50))
    screen.blit(title_surface, title_rect)

    # Draw buttons and labels
    for text, button_rect in button_rects:
        shadow_rect = button_rect.move(0, 6)
        pygame.draw.rect(screen, (220, 225, 235), shadow_rect, border_radius=18)

        if text == "Mute":
            fill_color = mute_button_color
            border_color = mute_button_border
            text_color = mute_text_color
        else:
            fill_color = button_color
            border_color = button_border
            text_color = button_text_color

        pygame.draw.rect(screen, fill_color, button_rect, border_radius=18)
        pygame.draw.rect(screen, border_color, button_rect, width=3, border_radius=18)
        label_surface = button_font.render(text, True, text_color)
        label_rect = label_surface.get_rect(center=button_rect.center)
        screen.blit(label_surface, label_rect)

    # Draw volume slider
    volume_label = small_font.render("Volume", True, (40, 40, 100))
    volume_label_rect = volume_label.get_rect(midbottom=(slider_track_rect.centerx, slider_track_rect.top - 10))
    screen.blit(volume_label, volume_label_rect)

    pygame.draw.rect(screen, (220, 225, 235), slider_track_rect, border_radius=4)
    filled_track_rect = pygame.Rect(slider_x, slider_y, handle_x - slider_x, 8)
    pygame.draw.rect(screen, (70, 90, 160), filled_track_rect, border_radius=4)
    pygame.draw.circle(screen, (240, 246, 255), handle_center, handle_radius)
    pygame.draw.circle(screen, (70, 90, 160), handle_center, handle_radius, width=2)

    percent_label = small_font.render(f"{int(current_volume * 100)}%", True, (40, 40, 100))
    percent_label_rect = percent_label.get_rect(midtop=(slider_track_rect.centerx, slider_track_rect.bottom + 8))
    screen.blit(percent_label, percent_label_rect)

    # Draw close button (solid red with "Close" label)
    pygame.draw.rect(screen, (200, 30, 30), close_button_rect, border_radius=8)
    pygame.draw.rect(screen, (140, 20, 20), close_button_rect, width=2, border_radius=8)
    close_label = small_font.render("Close", True, (255, 255, 255))
    close_label_rect = close_label.get_rect(center=close_button_rect.center)
    screen.blit(close_label, close_label_rect)

    pygame.display.flip()
    clock.tick(60)

# Uninitialize pygame modules cleanly before closing script
pygame.quit()