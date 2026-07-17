import pygame

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("pyproject game")
clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        screen.fill((255, 255, 255))
        pygame.display.flip()
        if event.type == pygame.QUIT:
            running =False
