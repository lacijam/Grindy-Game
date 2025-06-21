import pygame

from gamestate import GameState

class TooltipContext:
    def __init__(self, *, font, player, pos=None, required_states=None, **kwargs):
        self.font = font
        self.player = player
        self.pos = pos or pygame.mouse.get_pos()
        self.required_states = required_states or { GameState.PLAYING }

        # allow storing arbitrary extras like 'stat'
        for key, value in kwargs.items():
            setattr(self, key, value)