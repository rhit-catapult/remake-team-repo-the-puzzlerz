import os
import random
import subprocess
import sys
import pygame


def open_game(game_type, launcher_path=None):
    try:
        if game_type == "sudoku":
            target = os.path.join(os.path.dirname(__file__), "Sudoku.py")
        elif game_type == "crossword":
            target = os.path.join(os.path.dirname(__file__), "Crossword.py")
        elif game_type == "word_search":
            target = os.path.join(os.path.dirname(__file__), "Word_Search.py")
        else:
            target = launcher_path or os.path.join(os.path.dirname(__file__), "PuzzlerzGame.py")
        subprocess.Popen([sys.executable, target])
    except Exception:
        pass


def open_home(launcher_path=None):
    """Always returns to the Puzzlerz Game main menu, regardless of
    which puzzle was just completed."""
    try:
        target = launcher_path or os.path.join(os.path.dirname(__file__), "PuzzlerzGame.py")
        subprocess.Popen([sys.executable, target])
    except Exception:
        pass


def main():
    pygame.init()
    pygame.mixer.init()

    info = pygame.display.Info()
    width, height = info.current_w, info.current_h
    screen = pygame.display.set_mode((width, height), pygame.FULLSCREEN)
    pygame.display.set_caption("Congratulations")
    clock = pygame.time.Clock()
    game_type = os.environ.get("PUZZLER_GAME_TYPE", "")
    launcher_path = os.environ.get("PUZZLER_LAUNCHER_PATH", "")
    elapsed_seconds_str = os.environ.get("PUZZLER_ELAPSED_SECONDS", "")
    show_time = elapsed_seconds_str != ""  # only set when the puzzle's timer was visible

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

    close_button = pygame.Rect(width // 2 - 200, height // 2 + 60, 160, 60)
    back_button = pygame.Rect(width // 2 + 40, height // 2 + 60, 220, 60)

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

    game_type = os.environ.get("PUZZLER_GAME_TYPE", "")
    launcher_path = os.environ.get("PUZZLER_LAUNCHER_PATH", "")

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
                    # "Close" always goes back to the main Puzzlerz
                    # home screen, no matter which puzzle was solved.
                    open_home(launcher_path)
                    running = False
                elif back_button.collidepoint(event.pos):
                    # "Back" relaunches the same puzzle type for
                    # another round.
                    open_game(game_type, launcher_path)
                    running = False

        screen.fill(background_color)

        title_surface = title_font.render("YOU WIN!!!", True, (0, 180, 0))
        title_rect = title_surface.get_rect(center=(width // 2, height // 2 - 40))
        screen.blit(title_surface, title_rect)

        if show_time:
            try:
                secs = int(float(elapsed_seconds_str))
                time_str = f"Your time: {secs // 60:02d}:{secs % 60:02d}"
            except ValueError:
                time_str = ""
            if time_str:
                time_surface = button_font.render(time_str, True, (60, 60, 60))
                time_rect = time_surface.get_rect(center=(width // 2, height // 2 + 10))
                screen.blit(time_surface, time_rect)

        pygame.draw.rect(screen, (220, 20, 20), close_button, border_radius=16)
        pygame.draw.rect(screen, (255, 255, 255), close_button, width=3, border_radius=16)
        close_surface = button_font.render("Close", True, (255, 255, 255))
        close_rect = close_surface.get_rect(center=close_button.center)
        screen.blit(close_surface, close_rect)

        pygame.draw.rect(screen, (40, 140, 220), back_button, border_radius=16)
        pygame.draw.rect(screen, (255, 255, 255), back_button, width=3, border_radius=16)
        back_surface = button_font.render("Back", True, (255, 255, 255))
        back_rect = back_surface.get_rect(center=back_button.center)
        screen.blit(back_surface, back_rect)

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