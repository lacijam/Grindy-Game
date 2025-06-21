import pygame
import random

from constants import *
from resource_node_data import RESOURCE_NODE_LOOKUP

class ResourceNode:
    def __init__(self, x, y, node_id):
        self.id = node_id
        self.data = RESOURCE_NODE_LOOKUP[node_id]

        self.name = self.data["name"]
        self.skill = self.data["skill"]
        self.size = self.data["size"]
        self.rect = pygame.Rect(x, y, self.size, self.size)
        self.pos = pygame.Vector2(x, y)

        self.colour = self.data["colour"]
        self.max_hp = self.data["hp"]
        self.hp = self.max_hp
        self.reward_xp = self.data["reward_xp"]
        self.drop_table = self.data["drop_table"]
        self.required_skills = self.data.get("required_skills", {})

        self.depleted = False
        self.respawn_timer = 0
        self.respawn_time = 10.0  # could also be moved into node data if needed

        # temp for legacy items
        if isinstance(self.drop_table, list):
            self.drop_table = {
                "common": self.drop_table
            }

    def update(self, dt): 
        pass

    def draw(self, screen, camera, font, player):
        skill = self.data.get("skill", "mining")  # e.g. mining, woodcutting
        player_level = player.skills.get_skill_level(skill)
        required_skill = self.required_skills.get(skill, 0)
        is_locked = player_level < required_skill

        # old from when we had depleted
        alpha = 255

        # red tint for locked nodes
        if is_locked:
            colour = (
                min(self.colour[0] + 50, 255),
                max(self.colour[1] - 50, 0),
                max(self.colour[2] - 50, 0),
            )
        else:
            colour = self.colour

        surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        surface.fill((*colour, alpha))
        screen.blit(surface, camera.apply(self.rect))

        if player_level >= required_skill:
            hp_text = font.render(str(self.hp), True, (255, 255, 255))
            text_rect = hp_text.get_rect(center=self.rect.center)
            screen.blit(hp_text, camera.apply(text_rect))

    def mine(self, damage): # returns true on node depletion (death)
        self.hp -= damage

        depleted = self.hp <= 0
        if depleted:
            self.respawn_timer = self.respawn_time

        return depleted
        
    def get_partial_xp(self, damage):
        fraction = damage / self.max_hp
        return int(self.reward_xp * fraction)

    def get_partial_drops(self, damage):
        fraction = damage / self.max_hp
        result = {}

        for tier, drops in self.drop_table.items():
            for drop in drops:
                item_id = drop[0]
                base_chance = drop[1]
                quantity = drop[2] if len(drop) > 2 else (1, 1)

                # Scale drop chance down slightly for partial hits
                scaled_chance = base_chance * fraction * 0.75  # Slight penalty for partial

                if random.random() <= scaled_chance:
                    amount = random.randint(*quantity)
                    result[item_id] = {
                        "qty": amount,
                        "tier": tier,
                        "chance": scaled_chance
                    }

        return result
    
    def drop_items(self):
        result = {}
        for tier, drops in self.drop_table.items():
            for drop in drops:
                item_id = drop[0]
                chance = drop[1]
                quantity = drop[2] if len(drop) > 2 else (1, 1)

                if random.random() <= chance:
                    amount = random.randint(*quantity)
                    result[item_id] = {
                        "qty": amount,
                        "tier": tier,
                        "chance": chance
                    }
        return result
    

