from dataclasses import dataclass

@dataclass
class EquipmentSlot:
    item_id: str
    metadata: dict

class PlayerEquipment:
    def __init__(self, player):
        self.player = player
        self.SLOTS = ["head", "body", "hands", "legs", "feet"]
        self.slots = {slot: None for slot in self.SLOTS}

    def equip(self, item_id, metadata=None):
        item_full_data = self.player.inventory.get_item_full_data(item_id)
        base_data = item_full_data.base_data
        metadata = item_full_data.metadata

        if not base_data or "slot" not in base_data:
            return False

        slot = base_data["slot"]

        if self.slots[slot]:
            self.unequip(slot)

        self.slots[slot] = EquipmentSlot(
            item_id=item_id,
            metadata=metadata or {}
        )

        self.player.inventory.remove_item(item_id)

        return True

    def unequip(self, slot):
        slot_entry = self.slots.get(slot)
        if not slot_entry:
            return False

        item_id = slot_entry.item_id
        metadata = slot_entry.metadata

        base_item_id = self.player.inventory.get_base_id(item_id)
        self.player.inventory.add_item(base_item_id, amount=1, metadata=metadata)

        self.slots[slot] = None
        return True
    
    def get_all_equipped_enchantments(self):
        enchantments = []

        for slot, slot_entry in self.slots.items():
            if not slot_entry:
                continue

            item_id = slot_entry.item_id
            metadata = slot_entry.metadata

            # Read enchantments safely
            item_enchants = metadata.get("enchantments", [])
            enchantments.extend(item_enchants)

        return enchantments
