import pygame
import random

from constants import FONT_SIZE

# Popups
POPUP_DEFAULT_COLOUR = (255, 255, 255)
POPUP_DAMAGE_COLOUR = (255, 255, 255)
POPUP_CRIT_DAMAGE_COLOUR = (255, 255, 100)
POPUP_DAMAGE_LIFETIME = 150
POPUP_CRIT_SIZE_BOOST = 10
POPUP_DY = -0.4

class Popup:
    def __init__(self, x, y, text, colour=POPUP_DEFAULT_COLOUR, lifetime=POPUP_DAMAGE_LIFETIME, dy=POPUP_DY, font_size=FONT_SIZE):
        self.x = x + random.randint(-5, 5)
        self.y = y + random.randint(-5, 5)
        self.text = str(text)
        self.colour = colour
        self.lifetime_max = lifetime
        self.lifetime = lifetime
        self.alpha = 255
        self.dy = dy
        self.font = pygame.font.SysFont(None, font_size)

    def update(self):
        self.y += self.dy
        self.lifetime -= 1
        fade = max(0, self.lifetime / self.lifetime_max)
        self.alpha = int(255 * fade**2)  # fade-out ease

    def draw(self, surface, camera, font):
        if self.lifetime > 0:
            surf = self.font.render(self.text, True, self.colour)
            faded = surf.convert_alpha()
            faded.fill((255, 255, 255, self.alpha), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(faded, camera.apply((self.x, self.y)))

    def is_alive(self):
        return self.lifetime > 0
