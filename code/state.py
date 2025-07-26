import random
import math
import pygame

class State:
    def __init__(self, name):
        self.name = name

    def enter(self, enemy, ctx):
        pass

    def update(self, enemy, dt, ctx):
        pass

    def exit(self, enemy, ctx):
        pass

class IdleState(State):
    def __init__(self, name="idle", duration_range=(0.5, 1.0), next_state="squash"):
        super().__init__(name)
        self.duration_range = duration_range
        self.next_state = next_state

    def enter(self, enemy, ctx):
        ctx.fsm.timer = random.uniform(*self.duration_range)
        enemy.dx = 0
        enemy.dy = 0

    def update(self, enemy, dt, ctx):
        if ctx.fsm.timer <= 0:
            ctx.fsm.change_state(self.next_state, enemy, ctx)

class WanderState(State):
    def __init__(self, name="wander", speed_multiplier=1.0, duration_range=(1.0, 2.0), next_state="idle"):
        super().__init__(name)
        self.speed_multiplier = speed_multiplier
        self.duration_range = duration_range
        self.next_state = next_state

    def enter(self, enemy, ctx):
        ctx.fsm.timer = random.uniform(*self.duration_range)
        angle = random.uniform(0, 2 * math.pi)
        enemy.dx = enemy.speed * self.speed_multiplier * math.cos(angle)
        enemy.dy = enemy.speed * self.speed_multiplier * math.sin(angle)

    def update(self, enemy, dt, ctx):
        if ctx.fsm.timer <= 0:
            ctx.fsm.change_state(self.next_state, enemy, ctx)

class SquashState(State):
    def __init__(self, name="squash", duration=0.4, next_state="leap"):
        super().__init__(name)
        self.duration = duration
        self.next_state = next_state

    def enter(self, enemy, ctx):
        ctx.fsm.timer = self.duration
        enemy.dx = 0
        enemy.dy = 0
        ctx.squash_t = 0.0

    def update(self, enemy, dt, ctx):
        total = self.duration
        ctx.squash_t = 1.0 - max(0, ctx.fsm.timer / total)
        if ctx.fsm.timer <= 0:
            ctx.fsm.change_state(self.next_state, enemy, ctx)

class LeapState(State):
    def __init__(self, name="leap", duration=0.3, leap_strength=5.0, decel_factor=0.02, next_state="wander", sound_id="slime_jump", target_func=None, target_radius=50):
        super().__init__(name)
        self.duration = duration
        self.leap_strength = leap_strength
        self.decel_factor = decel_factor
        self.next_state = next_state
        self.sound_id = sound_id
        self.target_func = target_func  # returns target position or None
        self.target_radius = target_radius

    def enter(self, enemy, ctx):
        ctx.fsm.timer = self.duration

        target_pos = None
        if self.target_func:
            candidate = self.target_func(enemy, ctx)
            if candidate:
                if self.target_radius is None or enemy.pos.distance_to(candidate) <= self.target_radius:
                    target_pos = candidate

        if target_pos:
            direction = (target_pos - enemy.pos)
            if direction.length_squared() > 0:
                direction = direction.normalize()
                ctx.vector = direction * (enemy.speed * self.leap_strength)
            else:
                ctx.vector = pygame.Vector2()
        else:
            ctx.vector = self._random_vector(enemy)

    def _random_vector(self, enemy):
        angle = random.uniform(0, 2 * math.pi)
        speed = enemy.speed * self.leap_strength
        return pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)

    def update(self, enemy, dt, ctx):
        enemy.dx = ctx.vector.x
        enemy.dy = ctx.vector.y
        ctx.vector *= math.pow(self.decel_factor, dt)

        if ctx.fsm.timer <= 0:
            enemy.dx = 0
            enemy.dy = 0
            ctx.queue_effect("particles", pos=enemy.rect.center, colour=enemy.current_colour)
            ctx.queue_effect("sound", id=self.sound_id, pos=enemy.rect.center)
            ctx.fsm.change_state(self.next_state, enemy, ctx)

class ZigzagState(State):
    def __init__(self, name, speed_multiplier=1.0, segment_duration_range=(0.2, 0.5), total_duration_range=(1.0, 2.0), next_state=None):
        super().__init__(name)
        self.speed_multiplier = speed_multiplier
        self.segment_duration_range = segment_duration_range
        self.total_duration_range = total_duration_range
        self.next_state = next_state

        self.remaining_total_time = 0
        self.segment_timer = 0
        self.current_angle = 0

    def enter(self, entity, ctx):
        self.remaining_total_time = random.uniform(*self.total_duration_range)
        self._choose_new_direction()

    def _choose_new_direction(self):
        self.current_angle = random.uniform(0, 2 * math.pi)
        self.segment_timer = random.uniform(*self.segment_duration_range)

    def update(self, entity, dt, ctx):
        self.remaining_total_time -= dt
        self.segment_timer -= dt

        if self.segment_timer <= 0:
            self._choose_new_direction()

        speed = getattr(entity, "speed", 1.0) * self.speed_multiplier
        entity.dx = math.cos(self.current_angle) * speed
        entity.dy = math.sin(self.current_angle) * speed

        if self.remaining_total_time <= 0:
            if self.next_state:
                ctx.fsm.change_state(self.next_state, entity, ctx)

class ChaseState(State):
    def __init__(self, name="chase", radius=200, speed_multiplier=1.2, fallback="idle"):
        super().__init__(name)
        self.radius = radius
        self.speed_multiplier = speed_multiplier
        self.fallback = fallback

    def update(self, enemy, dt, ctx):
        player = ctx.player
        dist = enemy.pos.distance_to(player.pos)

        if dist > self.radius:
            if self.fallback:
                ctx.fsm.change_state(self.fallback, enemy, ctx)
            return

        dx, dy = player.pos.x - enemy.pos.x, player.pos.y - enemy.pos.y
        angle = math.atan2(dy, dx)
        enemy.dx = math.cos(angle) * enemy.speed * self.speed_multiplier
        enemy.dy = math.sin(angle) * enemy.speed * self.speed_multiplier

class FleeState(State):
    def __init__(self, name="flee", radius=150, speed_multiplier=1.5, next_state="idle"):
        super().__init__(name)
        self.radius = radius
        self.speed_multiplier = speed_multiplier
        self.next_state = next_state

    def update(self, enemy, dt, ctx):
        player = ctx.player
        dist = enemy.pos.distance_to(player.pos)

        if dist > self.radius:
            ctx.fsm.change_state(self.next_state, enemy, ctx)
            return

        dx, dy = enemy.pos.x - player.pos.x, enemy.pos.y - player.pos.y
        angle = math.atan2(dy, dx)
        enemy.dx = math.cos(angle) * enemy.speed * self.speed_multiplier
        enemy.dy = math.sin(angle) * enemy.speed * self.speed_multiplier

class StrafeState(State):
    def __init__(self, name="strafe", radius=180, fallback="idle", duration=2.0):
        super().__init__(name)
        self.radius = radius
        self.fallback = fallback
        self.duration = duration

    def enter(self, enemy, ctx):
        ctx.fsm.timer = self.duration

        # Lock the perpendicular direction at entry
        player = ctx.player
        dx = player.pos.x - enemy.pos.x
        dy = player.pos.y - enemy.pos.y

        # Get fixed perpendicular vector (random left/right)
        if random.random() < 0.5:
            perp_x = dy
            perp_y = -dx
        else:
            perp_x = -dy
            perp_y = dx

        length = math.hypot(perp_x, perp_y)
        if length == 0:
            perp_x, perp_y = 1, 0  # fallback direction
        else:
            perp_x /= length
            perp_y /= length

        # Store in context for use during update
        ctx._strafe_vector = pygame.Vector2(perp_x, perp_y)

    def update(self, enemy, dt, ctx):
        player = ctx.player
        dist = enemy.pos.distance_to(player.pos)

        if dist > self.radius * 1.5:
            ctx.fsm.change_state(self.fallback, enemy, ctx)
            return

        # Apply locked direction
        v = ctx._strafe_vector
        enemy.dx = v.x * enemy.speed
        enemy.dy = v.y * enemy.speed

        if ctx.fsm.timer <= 0:
            ctx.fsm.change_state(self.fallback, enemy, ctx)