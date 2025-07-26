import math
import random
import pygame

from data.enemy_data import ENEMY_DATA
from draw_helpers import draw_progress_bar
from state_machine import StateMachine
from state import *
from combat_entity import CombatEntity
from base_entity import BaseEntity

class EnemyContext:
    def __init__(self, zone, player, camera, zone_size):
        self.zone = zone
        self.player = player
        self.camera = camera
        self.zone_size = zone_size

class MovementBehaviour:
    def __init__(self):
        self.initialized = False

    def update(self, enemy, dt, ctx):
        pass

    def consume_effects(self):
        return self.ctx.consume_effects()

class MovementContext:
    def __init__(self, player):
        self.vector = pygame.Vector2()

        self.player = player

        self.pending_effects = []

        self.fsm = None

    def queue_effect(self, effect_type, **kwargs):
        self.pending_effects.append({"type": effect_type, **kwargs})

    def consume_effects(self):
        effects = self.pending_effects
        self.pending_effects = []
        return effects

class SpiderMovementBehaviour(MovementBehaviour):
    def __init__(self, player):
        super().__init__()
        
        self.ctx = MovementContext(player)
        self.fsm = StateMachine()
        self.ctx.fsm = self.fsm

        self.fsm.add_state(WanderState(
            name="wander",
            speed_multiplier=0.8,
            duration_range=(1.0, 2.0),
            next_state="zigzag"
        ))

        self.fsm.add_state(ZigzagState(
            name="zigzag",
            speed_multiplier=1.5,
            segment_duration_range=(0.1, 0.3),
            total_duration_range=(1.0, 1.5),
            next_state="leap"
        ))

        self.fsm.add_state(LeapState(
            name="leap",
            duration=0.3,
            leap_strength=7.0,
            decel_factor=0.2,
            next_state="wander",
            sound_id="spider_jump",
            target_func=lambda e, ctx: ctx.player.pos,
            target_radius=200
        ))

    def update(self, enemy, dt, ctx):
        if not self.initialized:
            self.fsm.change_state("wander", enemy, self.ctx)
            self.initialized = True

        self.fsm.update(enemy, dt, self.ctx)

class SlimeMovementBehaviour(MovementBehaviour):
    def __init__(self, player):
        super().__init__()

        self.ctx = MovementContext(player)
        self.fsm = StateMachine()
        self.ctx.fsm = self.fsm

        self.fsm.add_state(IdleState(
            name="idle",
            duration_range=(1.0, 1.5),
            next_state="squash"
        ))

        self.fsm.add_state(SquashState(
            name="squash",
            duration=0.7,
            next_state="leap"
        ))

        self.fsm.add_state(LeapState(
            name="leap",
            duration=0.3,
            leap_strength=4.0,
            decel_factor=0.02,
            next_state="wander",
            sound_id="slime_jump"
        ))

        self.fsm.add_state(WanderState(
            name="wander",
            speed_multiplier=0.2,
            duration_range=(2.0, 5.0),
            next_state="idle"
        ))

    def update(self, enemy, dt, zone_ctx):
        if not self.initialized:
            self.fsm.change_state("idle", enemy, self.ctx)
            self.initialized = True

        self.fsm.update(enemy, dt, self.ctx)
    
class ZombieMovementBehaviour(MovementBehaviour):
    def __init__(self, player):
        super().__init__()

        self.ctx = MovementContext(player)
        self.fsm = StateMachine()
        self.ctx.fsm = self.fsm

        self.ctx.fsm.add_state(ChaseState(
            name="chase",
            radius=250,
            speed_multiplier=1.5,
            fallback="wander"
        ))

        self.ctx.fsm.add_state(WanderState(
            name="wander",
            speed_multiplier=0.5,
            duration_range=(1.0, 2.0),
            next_state="chase"
        ))

    def update(self, enemy, dt, zone_ctx):
        if not self.initialized:
            self.ctx.fsm.change_state("chase", enemy, self.ctx)
            self.initialized = True

        self.ctx.fsm.update(enemy, dt, self.ctx)

class SkeletonMovementBehaviour(MovementBehaviour):
    def __init__(self, player):
        super().__init__()

        self.ctx = MovementContext(player)
        self.fsm = StateMachine()
        self.ctx.fsm = self.fsm

        self.ctx.fsm.add_state(StrafeState(
            name="strafe",
            radius=180,
            fallback="wander",
            duration=2.0,
        ))

        self.ctx.fsm.add_state(WanderState(
            name="wander",
            speed_multiplier=0.6,
            duration_range=(1.0, 2.0),
            next_state="strafe"
        ))

    def update(self, enemy, dt, zone_ctx):
        if not self.initialized:
            self.ctx.fsm.change_state("strafe", enemy, self.ctx)
            self.initialized = True

        self.ctx.fsm.update(enemy, dt, self.ctx)

class Enemy(BaseEntity):
    def __init__(self, x, y, enemy_id, zone):
        data = ENEMY_DATA[enemy_id]
        super().__init__(enemy_id, x, y, data["size"], data["size"], zone, type=data.get("type", "mob"))
        self.name = data["name"]

        self.base_colour = data["colour"]
        self.current_colour = self.base_colour
        self.hit_colour = (255, 0, 0)

        self.sounds = data.get("sounds", {})

        self.level = data["level"]
        self.base_damage = data["damage"]
        self.reward_xp = data["xp"]
        self.reward_coins = data["coins"]
        self.speed = data["speed"]
        self.drop_table = data["drop_table"]

        self.dx = 0
        self.dy = 0
        self.change_dir_timer = 0
        self.damage_cooldown = 0 # visual display
        self.max_damage_cooldown_duration = 0.75
        
        self._last_contact_hit = 0 # attack cooldown for attacking player
        self.attack_radius = 25

        self.combat = CombatEntity(
            owner=self,
            hp=data["hp"],
            max_hp=data["hp"],
            weight=data["weight"],
            regen_rate=data.get("regen", 0), # you can add this to ENEMY_DATA optionally
            regen_interval=1000
        )
        
        self.was_hit = False
        
        self.movement_behaviour = None  # Optional AI

        # @temp stops legacy items crashing drop_items
        if isinstance(self.drop_table, list):
            self.drop_table = {
                "common": self.drop_table
            }

    def update(self, dt, ctx: EnemyContext):
        self._update_damage_colour(dt)

        if self.movement_behaviour:
            self.movement_behaviour.update(self, dt, ctx)
        else:
            self.wander(dt)

        enemy_pos = pygame.Vector2(self.rect.center)
        player_pos = pygame.Vector2(ctx.player.rect.center)

        if enemy_pos.distance_to(player_pos) <= self.attack_radius:
            self._try_deal_contact_damage(ctx.player)

        self.combat.update(dt)

        self._apply_movement(dt, ctx.zone_size)

        self._sync_rect_to_pos()

    def _try_deal_contact_damage(self, player):
        now = pygame.time.get_ticks()

        if now - self._last_contact_hit >= 1000: 
            direction = pygame.Vector2(player.rect.center) - pygame.Vector2(self.rect.center)
            direction = direction.normalize() * 300 if direction.length_squared() > 0 else pygame.Vector2(0, 0)

            damage = self.base_damage # may be modified in future by enemy state (enraged, phases ...)
            player.combat.take_damage(damage, direction, attacker_entity=self)
            self._last_contact_hit = now

    def _update_damage_colour(self, dt):
        if self.damage_cooldown > 0:
            t = self.damage_cooldown / self.max_damage_cooldown_duration
            r = self.hit_colour[0] * t + self.base_colour[0] * (1 - t)
            g = self.hit_colour[1] * t + self.base_colour[1] * (1 - t)
            b = self.hit_colour[2] * t + self.base_colour[2] * (1 - t)
            self.current_colour = (int(r), int(g), int(b))
            self.damage_cooldown -= dt
        else:
            self.current_colour = self.base_colour

    def wander(self, dt):
        self.change_dir_timer -= dt
        if self.change_dir_timer <= 0:
            angle = random.uniform(0, 2 * math.pi)
            self.dx = self.speed * math.cos(angle)
            self.dy = self.speed * math.sin(angle)
            self.change_dir_timer = random.uniform(0.75, 1.5)

    def _apply_movement(self, dt, zone_size):
        self.pos.x += self.dx * dt
        self.pos.y += self.dy * dt

        max_x = zone_size - self.rect.width
        max_y = zone_size - self.rect.height

        if self.pos.x < 0 or self.pos.x > max_x:
            self.pos.x = max(0, min(self.pos.x, max_x))
            self.dx = -self.dx

        if self.pos.y < 0 or self.pos.y > max_y:
            self.pos.y = max(0, min(self.pos.y, max_y))
            self.dy = -self.dy

        if abs(self.dx) < 0.02: self.dx = 0
        if abs(self.dy) < 0.02: self.dy = 0

    def _apply_knockback(self, dt):
        self.pos += self.knockback_vector * dt
        self.knockback_vector *= math.exp(-KNOCKBACK_FRICTION * dt)

    def _sync_rect_to_pos(self):
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

    def draw_hp_bar(self, screen, camera):
        if self.combat.hp == self.combat.max_hp:
            return
        
        bar_width = self.rect.width
        bar_height = 5
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 2

        bar_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)

        draw_progress_bar(
            screen,
            camera.apply(bar_rect),
            progress=self.combat.hp / self.combat.max_hp,
            colour=(0, 200, 0),
            border_colour=(0, 0, 0),
            bg_colour=(120, 0, 0),
            text=None,
            font=None
        )

    def draw_base(self, screen, camera, font):
        pygame.draw.rect(screen, self.current_colour, camera.apply(self.rect))

    def debug_draw_attack_radius(self, screen, camera):
        pos = pygame.Vector2(self.rect.center)
        screen_pos = camera.apply(pos)
        pygame.draw.circle(screen, (255, 0, 0), screen_pos, self.attack_radius, 3)

    def draw(self, screen, camera, font):
        self.draw_base(screen, camera, font)
        self.draw_hp_bar(screen, camera)
        self.debug_draw_attack_radius(screen, camera)

    def hit(self, amount, knockback_vector=pygame.Vector2(0, 0)): # return true on death
        self.combat.take_damage(amount, knockback_vector)
        self.damage_cooldown = self.max_damage_cooldown_duration
        self.current_colour = self.hit_colour

        if amount > 0 and not self.was_hit:
            self.was_hit = True

        return self.combat.hp <= 0
    
    def drop_items(self, magic_find=0.0):
        result = {}
        for tier, drops in self.drop_table.items():
            for drop in drops:
                item_id = drop[0]
                base_chance = drop[1]
                quantity = drop[2] if len(drop) > 2 else (1, 1)

                adjusted_chance = base_chance

                if base_chance < 0.05:
                    adjusted_chance = base_chance * (1 + magic_find / 100)
                    adjusted_chance = min(adjusted_chance, 0.05)

                if random.random() <= adjusted_chance:
                    amount = random.randint(*quantity)
                    result[item_id] = {
                        "qty": amount,
                        "tier": tier,
                    }
        return result

class Zombie(Enemy):
    def __init__(self, x, y, player, zone):
        super().__init__(x, y, "zombie", zone)
        self.movement_behaviour = ZombieMovementBehaviour(player)

class Ghoul(Enemy):
    def __init__(self, x, y, player, zone):
        super().__init__(x, y, "ghoul", zone)
        self.movement_behaviour = ZombieMovementBehaviour(player)

class CorruptedSoul(Enemy):
    def __init__(self, x, y, player, zone):
        super().__init__(x, y, "corrupted_soul", zone)
        self.movement_behaviour = ZombieMovementBehaviour(player)

class Skeleton(Enemy):
    def __init__(self, x, y, player, zone):
        super().__init__(x, y, "skeleton", zone)
        self.movement_behaviour = SkeletonMovementBehaviour(player)

class Spider(Enemy):
    def __init__(self, x, y, player, zone):
        super().__init__(x, y, "spider", zone)
        self.movement_behaviour = SpiderMovementBehaviour(player)

    def update(self, dt, ctx):
        super().update(dt, ctx)

        if hasattr(self.movement_behaviour, "consume_effects"):
            for effect in self.movement_behaviour.consume_effects():
                if effect["type"] == "sound":
                    ctx.sound_manager.queue_positional(
                        effect["id"],
                        effect["pos"],
                        ctx.player.rect.center,
                        400
                    )

class RedSpider(Enemy):
    def __init__(self, x, y, player, zone):
        super().__init__(x, y, "red_spider", zone)
        self.movement_behaviour = SpiderMovementBehaviour(player)

class Slime(Enemy):
    def __init__(self, x, y, player, zone):
        super().__init__(x, y, "slime", zone)
        self.movement_behaviour = SlimeMovementBehaviour(player)

    def update(self, dt, ctx):
        super().update(dt, ctx)

        if hasattr(self.movement_behaviour, "consume_effects"):
            for effect in self.movement_behaviour.consume_effects():
                if effect["type"] == "particles":
                    ctx.zone.spawn_particles(
                        x=effect["pos"][0],
                        y=effect["pos"][1],
                        colour=effect.get("colour", (255, 255, 255)),
                        source_x=effect["pos"][0],
                        source_y=effect["pos"][1],
                        count=effect.get("count", 8),
                        life_min=effect.get("life_min", 0.08),
                        life_max=effect.get("life_max", 0.15),
                        dt=dt
                    )
                elif effect["type"] == "sound":
                    ctx.sound_manager.queue_positional(
                        effect["id"],
                        effect["pos"],
                        ctx.player.rect.center,
                        400
                    )