from enum import Enum

class GameState(Enum):
    PAUSED = 0
    PLAYING = 1
    INVENTORY = 2
    BEASTIARY = 3
    MESSAGE_LOG = 4