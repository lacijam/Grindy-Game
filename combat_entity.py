import math

import pygame

from ability_handlers import ABILITY_HANDLERS
from dataclasses import dataclass, field

@dataclass
class CombatResult:
    target: object
    attacker: object = None
    final_damage: int = 0
    final_hit: bool = False
    final_xp: dict = field(default_factory=dict)
    reason: str = None

KNOCKBACK_FRICTION = 5

class CombatEntity:
    def __init__(self, owner, hp, max_hp=None, max_hp_getter=None, weight=1.0, regen_rate=None, regen_rate_getter=None, regen_interval=1000, damage_reduction_fn=None):
        self.owner = owner
        self.hp = hp
        self._max_hp_fixed = max_hp
        self.max_hp_getter = max_hp_getter
        self.weight = weight
        self.knockback_vector = pygame.Vector2(0, 0)
        self.just_took_damage = False
        self.last_damage_taken = 0

        self.regen_rate = regen_rate
        self.regen_rate_getter = regen_rate_getter
        self.regen_interval = regen_interval
        self._last_regen = 0

        self._last_periodic_tick_times = {}  # effect_id → last tick time
        self._active_effects = []
        
        self.damage_reduction_fn = damage_reduction_fn

    @property
    def max_hp(self):
        if self.max_hp_getter:
            return self.max_hp_getter()
        return self._max_hp_fixed

    def set_active_effects(self, effects):
        self._active_effects = list(effects)

    def update(self, dt):
        now = pygame.time.get_ticks()

        for effect in self._active_effects:
            handler_fn = ABILITY_HANDLERS.get(effect["id"])
            if handler_fn and getattr(handler_fn, "phase", None) == "periodic":
                last_tick = self._last_periodic_tick_times.get(effect["id"], 0)
                context = {
                    "player": self.owner,
                    "combat_entity": self,
                    "now": now,
                    "last_tick": last_tick,
                    "level": effect["tier"],
                    "zone": getattr(self.owner, "zone", None),
                    "effect_hooks": []
                }
                triggered = handler_fn(context, level=effect["tier"])
                if triggered:
                    self._last_periodic_tick_times[effect["id"]] = now
                    self.owner.zone.effect_hooks.extend(context.get("effect_hooks", []))


        self.update_regen()
        self.clamp_hp_to_max()
        self.apply_knockback(dt)

    def apply_combat_phase(self, phase, context):
        for effect in self._active_effects:
            handler_fn = ABILITY_HANDLERS.get(effect["id"])
            if handler_fn and getattr(handler_fn, "phase", None) == phase:
                handler_fn(context, level=effect["tier"])

    def take_damage(self, amount, knockback_vector=pygame.Vector2(0, 0), attacker_entity=None, reason=None):
        reduction = self.damage_reduction_fn() if self.damage_reduction_fn else 0.0
        reduced_amount = amount * (1.0 - reduction)

        context = {
            "incoming_damage": reduced_amount,
            "player": self.owner,
            "attacker": attacker_entity,
        }

        self.apply_combat_phase("on_hit_received", context)

        final_incoming_damage = context.get("incoming_damage", reduced_amount)
        print(f"CombatEntity {self.owner.id} took {final_incoming_damage} damage (reduced from {amount} by {reduction * 100:.2f}%)")

        self.hp -= final_incoming_damage
        self.knockback_vector = knockback_vector / self.weight
        self.just_took_damage = True
        self.last_damage_taken = int(round(final_incoming_damage))

        result = CombatResult(
            target=self.owner,
            attacker=attacker_entity,
            final_damage=self.last_damage_taken,
            final_hit=self.hp <= 0,
            reason=reason
        )

        xp = getattr(self.owner, "reward_xp", None)
        if result.final_hit and xp is not None:
            result.final_xp["combat"] = xp

        return result

    def revive(self):
        print(f"CombatEntity {self.owner.id} revived")
        self.hp = self.max_hp

    def update_regen(self):
        now = pygame.time.get_ticks()
        regen_rate = self.regen_rate_getter() if self.regen_rate_getter else self.regen_rate

        if regen_rate > 0 and self.hp < self.max_hp:
            if now - self._last_regen >= self.regen_interval:
                self.heal(regen_rate)
                self._last_regen = now

    def heal(self, amount):
        if amount <= 0:
            return
        print(f"CombatEntity {self.owner.id} healed for {amount} HP")
        self.hp = min(self.max_hp, self.hp + amount)

    def apply_knockback(self, dt):
        self.owner.pos += self.knockback_vector * dt
        self.knockback_vector *= math.exp(-KNOCKBACK_FRICTION * dt)

    def clamp_hp_to_max(self):
        self.hp = min(self.hp, self.max_hp)
