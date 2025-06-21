from enum import Enum

class GameState(Enum):
    PAUSED = 0
    PLAYING = 1
    INVENTORY = 2
    CRAFTING = 3
    BEASTIARY = 4
    MASTERY = 5
    MESSAGE_LOG = 6
    TASKS = 7