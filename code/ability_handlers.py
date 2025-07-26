from data.ability_data import ABILITY_DATA

def ability_handler(phase):
    def decorator(fn):
        fn.phase = phase
        return fn
    return decorator

@ability_handler("pre_damage")
def handle_sharpness(context, level):
    context["base_damage"] += 5 * level
    print(f"Applying sharpness effect at level {level}, new base damage: {context['base_damage']}")

@ability_handler("pre_crit")
def handle_crit_boost(context, level):
    context["crit_chance"] += 5 * level
    print(f"Applying crit boost effect at level {level}, new crit chance: {context['crit_chance']}%")

@ability_handler("post_crit")
def handle_first_hit_bonus(context, level):
    if context.get("is_first_hit", False):
        bonus_multiplier = 1.5 + 0.1 * (level - 1)
        print(f"Applying first hit bonus effect at level {level}, multiplier: {bonus_multiplier}")
        context["damage"] *= bonus_multiplier

@ability_handler("post_damage")
def handle_lifesteal(context, level):
    enemy_max_hp = context["target"].combat.max_hp
    player_max_hp = context["player"].combat.max_hp

    # Scaling factor based on level
    percent_of_enemy_max_hp = 0.05 * level  # 5% per level
    heal_amount = int(enemy_max_hp * percent_of_enemy_max_hp)

    # Cap at 10% of player max HP
    max_allowed_heal = int(player_max_hp * 0.10)
    heal_amount = min(heal_amount, max_allowed_heal)

    print(f"Healing for {heal_amount} due to lifesteal (enemy_max_hp: {enemy_max_hp}, player_max_hp: {player_max_hp})")
    context["player"].combat.heal(heal_amount)

@ability_handler("on_kill")
def handle_speed_on_kill(context, level):
    player = context["player"]
    player.stats.add_temp_stat_bonus("speed", 10 * level, duration=3.0)
    print(f"Applying speed on kill effect at level {level}, speed bonus: {10 * level}")

@ability_handler("on_hit_received")
def handle_thorns(context, level):
    attacker = context["attacker"]
    reflect_damage = int(context["incoming_damage"] * (0.1 * level))
    attacker.hit(reflect_damage)
    print(f"Reflecting {reflect_damage} damage back to attacker due to thorns at level {level}")

@ability_handler("periodic")
def handle_slime_regen(context, level):
    values = ABILITY_DATA["slime_regen"]["values"]
    interval = values["interval"]
    regen_percent = values["regen_percent"]

    now = context["now"]
    last_tick = context["last_tick"]

    if now - last_tick >= interval:
        heal_amount = int(context["combat_entity"].max_hp * regen_percent)
        context["combat_entity"].heal(heal_amount)
        print(f"Regenerating {heal_amount} HP due to slime regeneration at level {level}")
        return True
    return False

@ability_handler("on_hit_received")
def handle_bone_thorns(context, level):
    values = ABILITY_DATA["bone_thorns"]["values"]
    reflect_percent = values["reflect_percent"]

    attacker = context["attacker"]
    reflect_damage = int(context["incoming_damage"] * reflect_percent)
    attacker.hit(reflect_damage)
    print(f"Reflecting {reflect_damage} damage back to attacker due to bone thorns at level {level}")

@ability_handler("on_hit_received")
def handle_slime_shield(context, level):
    values = ABILITY_DATA["slime_shield"]["values"]
    reduction_percent = values["damage_reduction_percent"]

    attacker = context["attacker"]
    if not attacker or getattr(attacker, "type", None) != "mob":
        return  # only affects mobs

    attacker_id = getattr(attacker, "id", "")
    if not attacker_id.startswith("slime"):
        return  # only reduces damage from enemies whose id starts with 'slime'

    # Apply reduction
    reduction_factor = (1.0 - reduction_percent / 100.0)
    context["incoming_damage"] *= reduction_factor
    print(f"Reducing damage from slime by {reduction_percent}%, new incoming damage: {context['incoming_damage']}")

@ability_handler("post_damage")
def handle_chain_lightning(context, level):
    target_enemy = context["target"]
    zone = context.get("zone")
    player = context["player"]

    if not zone:
        return

    print(f"Handling chain lightning for target {target_enemy.id} at level {level}")

    current_source = target_enemy
    chained_enemies = {target_enemy}

    base_percent = 0.5
    falloff_factor = 0.8
    current_percent = base_percent
    base_damage = context["damage"]

    for bounce in range(level):
        # Find nearest un-hit enemy
        nearby_enemies = [
            e for e in zone.enemies
            if e not in chained_enemies and e.combat.hp > 0
            and e.distance_to(current_source) <= 200
        ]

        if not nearby_enemies:
            break

        nearby_enemies.sort(key=lambda e: e.distance_to(current_source))
        chain_target = nearby_enemies[0]

        damage = int(base_damage * current_percent)

        result = chain_target.combat.take_damage(damage, attacker_entity=player, reason="chain_lightning")
        zone.pending_enemy_results.append(result)

        if "effect_hooks" in context:
            zone.queue_effect("chain_lightning", {
                "from_pos": current_source.rect.center,
                "to_pos": chain_target.rect.center,
            })

        print(f"Chain Lightning bounce {bounce + 1} → dealing {damage} to {chain_target.id}")

        chained_enemies.add(chain_target)
        current_source = chain_target

        current_percent *= falloff_factor


@ability_handler("periodic")
def handle_phoenix_aura(context, level):
    values = ABILITY_DATA["phoenix_aura"]["values"]
    interval = values["interval"]
    aoe_damage = values["aoe_damage"]

    now = context["now"]
    last_tick = context["last_tick"]
    zone = context.get("zone")
    player = context["player"]

    if now - last_tick >= interval:
        if zone:
            for enemy in zone.enemies:
                if enemy.combat.hp > 0 and enemy.distance_to(player) <= 100:
                    result = enemy.combat.take_damage(
                        aoe_damage, attacker_entity=player, reason="phoenix_aura"
                    )
                    zone.pending_enemy_results.append(result)

                    if "effect_hooks" in context:
                        zone.queue_effect("phoenix_aura_hit", {
                            "x": enemy.rect.centerx,
                            "y": enemy.rect.centery,
                        })
        return True
    return False

@ability_handler("post_damage")
def handle_cleave(context, level):
    zone = context.get("zone")
    player = context.get("player")
    origin_target = context.get("target")
    final_damage = context.get("damage")

    if not zone or not player or not origin_target or final_damage <= 0:
        return

    base_radius = ABILITY_DATA.get("cleave", {}).get("values", {}).get("radius", 100)
    percent = 0.15 * level  # 15%, 30%, 45%
    affected = 0

    for enemy in zone.enemies:
        if enemy == origin_target or enemy.combat.hp <= 0:
            continue
        if origin_target.distance_to(enemy) <= base_radius:
            cleave_damage = int(final_damage * percent)
            result = enemy.combat.take_damage(
                cleave_damage, attacker_entity=player, reason="cleave"
            )
            zone.pending_enemy_results.append(result)

            if "effect_hooks" in context:
                zone.queue_effect("cleave_hit", {
                    "x": enemy.rect.centerx,
                    "y": enemy.rect.centery,
                })

            affected += 1

    if affected > 0 and "effect_hooks" in context:
        zone.queue_effect("cleave", {
            "x": origin_target.rect.centerx,
            "y": origin_target.rect.centery,
        })

    print(f"[Cleave] Hit {affected} enemies around {origin_target.id} for {percent:.0%} of {final_damage} damage")

ABILITY_HANDLERS = {
    "sharpness": handle_sharpness,
    "crit_boost": handle_crit_boost,
    "first_hit_bonus": handle_first_hit_bonus,
    "lifesteal": handle_lifesteal,
    "speed_on_kill": handle_speed_on_kill,
    "thorns": handle_thorns,
    "bone_thorns": handle_bone_thorns,
    "slime_regen": handle_slime_regen,
    "slime_shield": handle_slime_shield,
    "chain_lightning": handle_chain_lightning,
    "phoenix_aura": handle_phoenix_aura,
    "cleave": handle_cleave,
}