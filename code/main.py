import pygame
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from game import Game

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Grindy Game")

clock = pygame.time.Clock()

game = Game()

running = True
while running:
    dt = clock.tick(144) / 1000
    events = pygame.event.get()

    for event in events:
        if event.type == pygame.QUIT:
            running = False

    game.handle_events(events)
    game.update(dt, clock)
    game.draw(screen)

    pygame.display.flip()

pygame.quit()
