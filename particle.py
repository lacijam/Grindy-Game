import random
import math

import pygame

class Particle:
    def __init__(self, x, y, colour, source_x, source_y, life_min, life_max, dt):
        self.x = x + random.randint(-4, 4)
        self.y = y + random.randint(-4, 4)
        self.life_min = max(life_min, dt * 0.4)
        self.life_max = max(life_max, dt * 0.6)

        angle = math.atan2(self.y - source_y, self.x - source_x)
        spread = random.uniform(-0.5, 0.5)
        speed = random.uniform(1.5, 2.0) * 220

        self.dx = math.cos(angle + spread) * speed
        self.dy = math.sin(angle + spread) * speed
        self.colour = colour
        self.life = random.uniform(life_min, life_max)  # seconds
        self.age = 0

    def update(self, dt):
        self.x += self.dx * dt
        self.y += self.dy * dt
        self.age += dt

    def is_dead(self):
        return self.age >= self.life

    def draw(self, screen, camera):
        screen_x, screen_y = camera.apply((self.x, self.y))
        pygame.draw.rect(screen, self.colour, (screen_x, screen_y, 3, 3))
