import os
import random
import pygame


def main():
    pygame.init()
    pygame.mixer.init()

    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Congratulations")
    clock = pygame.time.Clock()

    sound_path = os.path.join(os.path.dirname(__file__), "soundreality-airhorn-fx-343682.mp3")
    if os.path.exists(sound_path):
        try:
            airhorn_sound = pygame.mixer.Sound(sound_path)
            airhorn_sound.play()
        except Exception:
            pass

    background_color = (255, 255, 255)
    title_font = pygame.font.SysFont(None, 120)
    button_font = pygame.font.SysFont(None, 42)

    close_button = pygame.Rect(300, 430, 200, 60)

    confetti = []
    corners = [(0, 0), (width, 0), (0, height), (width, height)]
    for _ in range(120):
        x, y = random.choice(corners)
        confetti.append({
            "x": x,
            "y": y,
            "dx": random.uniform(-5, 5),
            "dy": random.uniform(-5, 5),
            "size": random.randint(6, 12),
            "color": random.choice([(255, 0, 0), (0, 180, 0), (0, 0, 255), (255, 165, 0), (255, 0, 255)]),
        })

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if close_button.collidepoint(event.pos):
                    running = False

        screen.fill(background_color)

        title_surface = title_font.render("YOU WIN!!!", True, (0, 180, 0))
        title_rect = title_surface.get_rect(center=(width // 2, height // 2 - 40))
        screen.blit(title_surface, title_rect)

        pygame.draw.rect(screen, (220, 20, 20), close_button, border_radius=16)
        pygame.draw.rect(screen, (255, 255, 255), close_button, width=3, border_radius=16)
        close_surface = button_font.render("Close", True, (255, 255, 255))
        close_rect = close_surface.get_rect(center=close_button.center)
        screen.blit(close_surface, close_rect)

        for piece in confetti:
            piece["x"] += piece["dx"]
            piece["y"] += piece["dy"]
            piece["dy"] += 0.08
            pygame.draw.rect(screen, piece["color"], (piece["x"], piece["y"], piece["size"], piece["size"]))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
