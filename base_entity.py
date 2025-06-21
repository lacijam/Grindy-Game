import pygame

class BaseEntity:
    def __init__(self, id, x, y, width, height, zone, type="generic"):
        self.id = id
        self.type = type
        self.rect = pygame.Rect(x, y, width, height)
        self.pos = pygame.Vector2(x, y)
        self.zone = zone

        self.combat = None

    def update(self, dt, ctx):
        pass

    def draw(self, screen, camera, font=None):
        pass

    def distance_to(self, other_entity):
        return pygame.Vector2(self.rect.center).distance_to(pygame.Vector2(other_entity.rect.center))
