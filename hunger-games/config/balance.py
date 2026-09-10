# all the variables
# is () means randint
STARTING_HUNGER = 0
STAT_RANGE = (25, 100)
MAX_HEALTH = 100

HUNGER_TICK = 5
HUNGER_DEATH = 100
HEALTH_DEATH = 0

STAMINA_COST = {
    "MOVE": 12,
    "REST": 0,
    "SEARCH": 10,
    "HIDE": 8,
    "ATTACK": 20,
    "FLEE": 20,
    "IGNORE": 0,
    "USE_ITEM": 0,
}
EXHAUSTION_RATIO = 0.26
EXHAUSTION_MULTIPLIER = 1.6

REST_HEALTH_GAIN = 15
REST_STAMINA_GAIN = 15
REST_VARIANCE = 5
REST_HUNGER_COST = (5, 10)

SEARCH_FOOD_GAIN = 35
SEARCH_FAIL_HUNGER = 10

ATTACK_DAMAGE = 50

MAX_TURNS = 200

AGENT_NAMES = ["Agent-A", "Agent-B"]

# Combat_value
COMBAT_STRENGTH = 0.50
COMBAT_SPEED = 0.35
COMBAT_INTELLIGENCE = 0.15

# Flee_value
FLEE_SPEED = 0.40
FLEE_STAMINA = 0.40
FLEE_INTELLIGENCE = 0.20

# Hide_value
HIDE_STEALTH = 0.40
HIDE_INTELLIGENCE = 0.40
HIDE_STAMINA = 0.20
MAX_HIDE_VALUE = 110
MIN_HIDE_VALUE = 10

# Random noise
RANDOM_NOISE = (0.9, 1.1)
RANDOM_ADD = (-10, 10)

# inventory
LOOT_TABLE = [
    # (kind, name, wheight)
    ("medicine", "bandage", 3),
    ("medicine", "medkit", 1),
    ("medicine", "green herbs", 2),
    ("weapon", "rusted knife", 2),
    ("weapon", "sharpened spear", 1),
    ("weapon", "old katana", 1),
]

DROP_RATE = 0.35

# medicine
MEDICINE_HEAL = 40

# weapon
WEAPON_MODIFIERS = {
    "rusted knife": 8,
    "sharpened spear": 14,
    "old katana": 12,
}
