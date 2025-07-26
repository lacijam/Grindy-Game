import pygame
from dataclasses import dataclass

from data.item_data import ITEMS  # adjust path if needed
from format import get_rarity_colour, get_colour_for_type
from draw_helpers import draw_typed_text

@dataclass
class PickupEntry:
    item_id: str
    amount: int
    timestamp: int

class PickupLog:
    def __init__(self, font, max_entries=6, lifespan_ms=3500):
        self.font = font
        self.entries = []  # List[PickupEntry]
        self.max_entries = max_entries
        self.lifespan_ms = lifespan_ms

    def log(self, item_id, amount=1):
        now = pygame.time.get_ticks()

        # Try to consolidate with recent identical entry
        for index, entry in enumerate(self.entries):
            if entry.item_id == item_id and now - entry.timestamp < self.lifespan_ms:
                self.entries[index] = PickupEntry(item_id, entry.amount + amount, now)
                break
        else:
            self.entries.insert(0, PickupEntry(item_id, amount, now))

        if len(self.entries) > self.max_entries:
            self.entries.pop()

    def update(self):
        now = pygame.time.get_ticks()
        self.entries = [
            entry for entry in self.entries
            if now - entry.timestamp < self.lifespan_ms
        ]

    def draw(self, surface, x, y):
        for index, entry in enumerate(self.entries):
            item = ITEMS.get(entry.item_id, {})
            name = item.get("name", entry.item_id)
            rarity_colour = get_rarity_colour(item.get("rarity", "common"))
            alpha = self._get_alpha(entry.timestamp)

            segments = [
                (f"+{entry.amount} ", get_colour_for_type("number")),
                (name, rarity_colour)
            ]

            draw_typed_text(surface, self.font, segments, x, y - index * 18, alpha=alpha)
    
    def _get_alpha(self, timestamp):
        now = pygame.time.get_ticks()
        elapsed = now - timestamp
        remaining = self.lifespan_ms - elapsed
        fade_start = 1000  # Last second fades out

        if remaining > fade_start:
            return 255
        elif remaining <= 0:
            return 0
        else:
            return int(255 * (remaining / fade_start))
