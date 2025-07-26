from dataclasses import dataclass
from data.item_data import ITEMS
from data.enchantment_data import ENCHANTMENT_DATA

@dataclass
class ItemInstance:
    item_id: str
    metadata: dict

@dataclass
class ItemFullData:
    item_id: str
    base_data: dict
    metadata: dict
    is_instance: bool

class PlayerInventory:
    def __init__(self, player):
        self.player = player
        self.items = {}
        self.item_instances = {}  # instance_id → ItemInstance
        self.next_instance_id = 1
        self.hotbar = [None] * 5
        self.selected_hotbar_index = 0

    def _is_item_stackable(self, item_id):
        return ITEMS.get(item_id, {}).get("stackable", True)

    def add_item(self, item_id, amount=1, metadata=None, log_callback=None):
        if amount <= 0:
            return

        item_data = ITEMS.get(item_id, {})
        stackable = item_data.get("stackable", True)
        force_unique = item_data.get("unique", False)

        treat_as_unique = (
            not stackable
            or force_unique
            or (metadata is not None and metadata != {})
        )

        if not treat_as_unique:
            self._add_stackable_item(item_id, amount, log_callback)
        else:
            self._add_unique_item_instances(item_id, amount, metadata)

    def _add_stackable_item(self, item_id, amount, log_callback):
        self.items[item_id] = self.items.get(item_id, 0) + amount
        if log_callback:
            log_callback(item_id, amount)

    def _add_unique_item_instances(self, item_id, amount, metadata):
        for _ in range(amount):
            instance_id = self.next_instance_id
            self.next_instance_id += 1
            self.item_instances[instance_id] = ItemInstance(
                item_id=item_id,
                metadata=metadata or {}
            )

    def remove_item(self, item_id, amount=1):
        if self.is_item_instance(item_id):
            instance_id = self._split_instance_id(item_id)[1]
            self._remove_item_instance(instance_id)
            return

        stackable = self._is_item_stackable(item_id)
        if stackable:
            self._remove_stackable_item(item_id, amount)
            return

        self._remove_item_instances_by_base_id(item_id, amount)

    def _remove_item_instance(self, instance_id):
        if instance_id in self.item_instances:
            del self.item_instances[instance_id]

    def _remove_stackable_item(self, item_id, amount):
        if item_id not in self.items:
            return

        self.items[item_id] -= amount
        if self.items[item_id] <= 0:
            del self.items[item_id]

    def _remove_item_instances_by_base_id(self, base_item_id, amount):
        instances_to_remove = [
            instance_id for instance_id, item_instance in self.item_instances.items()
            if item_instance.item_id == base_item_id
        ][:amount]

        for instance_id in instances_to_remove:
            self._remove_item_instance(instance_id)

    def assign_to_hotbar(self, item_id, index):
        self._remove_item_from_hotbar(item_id)

        self.hotbar[index] = item_id

        if self.selected_hotbar_index == index:
            self.player.change_active_item(index)

    def _remove_item_from_hotbar(self, item_id):
        for slot_index, existing_id in enumerate(self.hotbar):
            if existing_id == item_id:
                self.hotbar[slot_index] = None

    def get_enchantments_for_item(self, item_id, metadata_override=None):
        if metadata_override is not None:
            return metadata_override.get("enchantments", [])

        if not self.is_item_instance(item_id):
            return []

        instance_id = self._split_instance_id(item_id)[1]
        instance = self.item_instances.get(instance_id)
        if instance:
            return instance.metadata.get("enchantments", [])
        return []

    def get_enchantment_stat_bonuses_for_item(self, item_id, metadata_override=None):
        bonuses = {}

        if metadata_override:
            enchantments = metadata_override.get("enchantments", [])
        else:
            enchantments = self.get_enchantments_for_item(item_id)

        for enchant in enchantments:
            ench_data = ENCHANTMENT_DATA.get(enchant["id"], {})
            per_level = ench_data.get("stat_bonuses_per_level", {})

            for stat, value_per_level in per_level.items():
                bonuses[stat] = bonuses.get(stat, 0) + value_per_level * enchant["level"]

        return bonuses

    def get_item_full_data(self, item_id):
        is_instance = self.is_item_instance(item_id)
        base_item_id = self.get_base_id(item_id)
        base_data = ITEMS.get(base_item_id, {})
        metadata = {}

        if is_instance:
            instance_id = self._split_instance_id(item_id)[1]
            instance = self.item_instances.get(instance_id)
            if instance:
                metadata = instance.metadata
                base_item_id = instance.item_id

        return ItemFullData(
            item_id=base_item_id,
            base_data=base_data,
            metadata=metadata,
            is_instance=is_instance
        )

    def get_base_id(self, item_id):
        if self.is_item_instance(item_id):
            base_item_id, instance_id = self._split_instance_id(item_id)
            instance = self.item_instances.get(instance_id)
            if instance:
                return instance.item_id
            return base_item_id
        return item_id

    def get_item_metadata(self, item_id):
        if not self.is_item_instance(item_id):
            return {}

        instance_id = self._split_instance_id(item_id)[1]
        instance = self.item_instances.get(instance_id)
        if instance:
            return instance.metadata
        return {}

    def is_item_instance(self, item_id):
        if not item_id:
            return False
        return "__instance__" in item_id

    def _split_instance_id(self, item_id):
        base_item_id, rest = item_id.split("__instance__", 1)
        instance_id = int(rest)
        return base_item_id, instance_id
