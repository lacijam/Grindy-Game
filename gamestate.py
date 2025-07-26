from enum import Enum

class GameState(Enum):
    PAUSED = 0
    PLAYING = 1
    INVENTORY = 2
    CRAFTING = 3
    BEASTIARY = 4
    MESSAGE_LOG = 5
    TASKS = 6