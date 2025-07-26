import pygame
import random
import math

class SoundManager:
    def __init__(self):
        def sfx(path): return pygame.mixer.Sound(f"./assets/sounds/{path}")

        self._sound_queue = []

        self.sounds = {
            "button_click": {
                "volume": 0.5,
                "variants": [
                    sfx("button_click.wav"),
                ]
            },
            "button_back": {
                "volume": 0.5,
                "variants": [
                    sfx("button_back.wav"),
                ]
            },
            "item_equip": {
                "volume": 0.5,
                "variants": [
                    sfx("item_equip_1.wav"),
                    sfx("item_equip_2.wav"),
                    sfx("item_equip_3.wav"),
                ]
            },
            "mining_strike": {
                "volume": 0.2,
                "variants": [
                    sfx("mining_strike_1.wav"),
                    sfx("mining_strike_2.wav"),
                    sfx("mining_strike_3.wav"),
                ]
            },
            "woodcutting_strike": {
                "volume": 0.2,
                "variants": [
                    sfx("woodcutting_strike.wav"),
                ]
            },
            "tool_ding": {
                "volume": 0.2,
                "variants": [
                    sfx("tool_ding_1.wav"),
                    sfx("tool_ding_2.wav"),
                    sfx("tool_ding_3.wav"),
                ]
            },
            "slime_hit": {
                "volume": 0.2,
                "variants": [
                    sfx("slime_hit_1.wav"),
                    sfx("slime_hit_2.wav"),
                    sfx("slime_hit_3.wav"),
                ]
            },
            "slime_jump": {
                "volume": 0.7,
                "variants": [
                    sfx("slime_jump_1.wav"),
                    sfx("slime_jump_2.wav"),
                    sfx("slime_jump_3.wav"),
                ]
            },
            "skeleton_hit": {
                "volume": 0.4,
                "variants": [
                    sfx("skeleton_hit_1.wav"),
                    sfx("skeleton_hit_2.wav"),
                    sfx("skeleton_hit_3.wav"),
                ]
            },
            "zombie_hit": {
                "volume": 0.4,
                "variants": [
                    sfx("zombie_hit_1.wav"),
                    sfx("zombie_hit_2.wav"),
                    sfx("zombie_hit_3.wav"),
                ]
            },
            "enemy_death": {
                "volume": 0.25,
                "variants": [sfx("ding.wav")]
            },
            "level_up_skill": {
                "volume": 0.5,
                "variants": [sfx("level_up_skill.wav")]
            },
            "level_up_beastiary": {
                "volume": 0.5,
                "variants": [sfx("level_up_beastiary.wav")]
            },
            "drop": {
                "volume": 0.25,
                "variants": [sfx("drop.wav")]
            },
            "task_ready": {
                "volume": 0.75,
                "variants": [sfx("task_ready.wav")]
            },
            "task_claim": {
                "volume": 0.75,
                "variants": [sfx("task_claim.wav")]
            },
            "zap": {
                "volume": 0.75,
                "variants": [sfx("zap.wav")]
            },
            "fire_aura_hit": {
                "volume": 0.5,
                "variants": [sfx("fire_aura_hit.wav")]
            },
        }


    def queue(self, sound_id):
        if sound_id in self.sounds:
            self._sound_queue.append(sound_id)

    def queue_positional(self, sound_id, source_pos, listener_pos, max_distance=400):
        sx, sy = source_pos
        lx, ly = listener_pos

        dx = sx - lx
        dy = sy - ly
        distance = math.hypot(dx, dy)

        if distance > max_distance:
            return

        entry = self.sounds.get(sound_id)
        if not entry:
            return

        volume_scale = 1.0 - (distance / max_distance)
        volume_scale = max(0.0, min(1.0, volume_scale))

        self._sound_queue.append((sound_id, volume_scale))

    def flush(self):
        seen = set()
        for item in self._sound_queue:
            if isinstance(item, tuple):
                sound_id, volume_override = item
            else:
                sound_id, volume_override = item, None

            if sound_id in seen:
                continue

            entry = self.sounds.get(sound_id)
            if not entry:
                continue

            variants = entry.get("variants", [])
            if not variants:
                continue

            sound = random.choice(variants)
            volume = volume_override if volume_override is not None else entry.get("volume", 1.0)
            sound.set_volume(volume)

            channel = pygame.mixer.find_channel()
            if channel:
                channel.play(sound)

            seen.add(sound_id)

        self._sound_queue.clear()


    def play_positional(self, sound_id, source_pos, listener_pos, max_distance=600, power=2):
        entry = self.sounds.get(sound_id)
        if not entry:
            return

        dx = source_pos[0] - listener_pos[0]
        dy = source_pos[1] - listener_pos[1]
        distance = math.hypot(dx, dy)
        if distance >= max_distance:
            return

        volume = (1 - (distance / max_distance)) ** power
        volume = max(0.05, min(volume, 1.0))  # keep faint ambience

        pan = dx / max_distance  # -1 (left) to +1 (right)
        pan = max(-1, min(pan, 1))
        left_volume = volume * (1 - pan) if pan > 0 else volume
        right_volume = volume * (1 + pan) if pan < 0 else volume

        volume_modifier = entry.get("volume", 0.2)

        sound = random.choice(entry["variants"])
        sound.set_volume(volume * volume_modifier)
        sound.play()