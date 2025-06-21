- next
TOOLS ARE NOW BROKEN 

enchantment UI to apply even if just for debug

Expand enchantments
    - Requires gold and ??? magical resource ??? to apply
    - Item applies them?

add new type of applicable item
    - store buff in stat_bonuses
    - if metadata then will need to change add_item logic for stacking
    - capability to apply in inventory X times
    - buff_data proposed structure
        { 
            item_id: str, stat_bonuses: {}, max_uses: int
        }
    - new field in items "buffs": { "potato_book": "2" }
        - id used in lookup for buff_data
        - '2' number is the number of applications
        - lookup the effect in code and apply dynamically
        - cache the bonus in case its done every frame
    - item has apply_to_item_ function or weapon/tool has function   
    - sound to apply

show base_damage change in tooltip (+X) from any source

show stat_bonus buffs (+X) from any source (enchantments...)
    - Strength +5 (+2) <- 5 is base so 7 altogether

Give items unique flag and display in tooltip at bottom above rarity
    - no colour necessary just flag in case non-uniques roll stat ranges
    - check add_item stackable logic for uniques

Extend item damage and stat_bonuses to accept a range +(1, 3) strength
    - makes the item instanced
    Consider mouse hold (e.g. SHIFT) to show advanced stats in all panels
        - delay, range

Breaking power stat to tools to restrict nodes
    - Likewise stat added to resource nodes.

Add to tooltip to show recipe unlocks
Level 1
    Recipe: Slime Core
Level 2
Level 3
    Recipe: Slime Sword
...
Level 10

beastiary,mastery need collapsable entries and entry pane colours

Add crafting UI buttons
    - Craft all, x1, x5, ... for each recipe

Inventory
    - Salvage upgrade
        - button in inventory UI
            - craft all common, uncommon...
        - costs gold to do
        - costs gold and refined iron to unlock
        - returns logical base materials
            - iron sword returns 1 iron and 1 wood
        - or store salvage resources given in code
            - could give new crafting materials
                - salvage legendary gives a power core?

- features
use for gold
    - sink

resource mastery levels unlock recipes
    - Add field to recipes "required_mastery": {"stone": 3}

add zone mastery
    - tracks beastiary and mastery unlocks for each zone
    - unlock tiers
        - unlocking everything in a zone to give small bonus for THAT zone e.g. +1% xp, +1 magic find
            - make the system extensible because i will change mind for what bonus is
    - maxxing requries maxxing all enemies/nodes for that zone (very end-game)
    -Keep it modular: { "xp_bonus": 1.0, "mf_bonus": 1.0 }
    Track by zone ID, tie into both mastery and beastiary
    Tooltip panel showing % complete + tier rewards

add item collection
    - tracks crafted and dropped items
    - tiers for number of unique collected
    - awards magic find each tier 10 items/50/100, +1/+2/+3 magic find

Add zone modifiers
    - ZONE_MODIFIERS_DATA suggested structure
        {
            {
                "id": "increased_spider_damage",
                "enemy_modifier": {
                    "type": "spider",
                    "damage": 100,
                    # "hp": -50
                }
            },
            {
                "id": "increased_xp",
                "enemy_modifier": {
                    "xp": 100,
                }
            }
            {
                "id": "increased_xp",
                "node_modifier": {
                    "skill": "mining",
                    #"id": "coal",
                    "xp": 100,
                }
            }
        }
    - enemy_modifier takes a type or if no type specificed apply to all enemies in zone
    - node_modifiers can take a skill to check against nodes with or a specific node ID to effect
    - all values are +% modifiers
    - modifiers can be combined
        - Spiders deal 50% more damage
        - Enemies reward +100% more experience
    - Display in tooltip

Add support for weapon multi-hit (X enemies in radius)
    - Cleave enchantment % damage to all enemies in radius

Add slayer skill:
    Slayer UI that displays current task
        - Slayer level rewards

boss attack behaviours with flowstate logic
    -Boss Flowstate AI
    Define boss states: idle → attack1 → recover → attack2...
    Include:
        Windup time
        Predictable patterns
        Interruptibility (stun windows?)

dodge mechanic
    -Needs: i-frames, stamina/resource cost (future?), animation, sound
    Add cooldown and possibly an upgrade path (shorter cooldown, longer range)

stat tooltips
    - dps when hover something
    - attack speed - attacks per second

Hold alt during item tooltip displays ranges for each rolled stat (like poe)

skeleton ranged attack and fire and move behaviour
    -Do projectiles persist or disappear off-screen?
    AI: Should they flee or strafe if player gets too close?

inventoryUI moveable categories
    Click-and-drag tabs
    Item type filters (Weapon, Tool, Material)

Different classes with mastery level?

Debug Tools (for you as dev)
    XP boost toggle
    “Give item” hotkey
    Resource node/enemy spawn spawner for testing
    Beastiary/debug stat print in console

- tweaks / bugs
crash when enemy tries to drop item that doesnt exist
clamp ui panes to screen
lose focus player keeps moving even after refocus

- code cleanup
active item skill now redenundent or make into "default_skill"
    - Replace skill string in ActionItem with default_action (unified across tools/weapons)
resource node depletion timer moved into data
distance_to function in player class
zones have skill attribute still -> what is it for?