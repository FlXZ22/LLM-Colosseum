from config import balance
from agents.controller import Controller
from engine.item import weapon_modifier


class Agent:
    def __init__(self, name, rng):
        self.name = name
        self.rng = rng
        self.health = balance.MAX_HEALTH
        self.strength = self.rng.randint(*balance.STAT_RANGE)
        self.speed = self.rng.randint(*balance.STAT_RANGE)
        self.max_stamina = self.rng.randint(*balance.STAT_RANGE)
        self.stamina = self.max_stamina
        self.intelligence = self.rng.randint(*balance.STAT_RANGE)
        self.stealth = self.rng.randint(*balance.STAT_RANGE)
        self.hunger = balance.STARTING_HUNGER
        self.position = "cornucopia"
        self.alive = True
        self.hidden = False
        self.controller = Controller(rng)
        self.inventory = []

    def clamp(self):
        self.hunger = max(0, self.hunger)
        self.health = min(balance.MAX_HEALTH, self.health)
        self.stamina = min(self.max_stamina, max(0, self.stamina))

    def validate(self):
        self.clamp()
        reason = None
        if self.hunger >= balance.HUNGER_DEATH:
            self.alive = False
            reason = "Starved to death"
        elif self.health <= balance.HEALTH_DEATH:
            self.alive = False
            reason = "Died due to low health"
        return self.alive, reason

    def combat_value(self):
        capacity = (
            (self.strength * balance.COMBAT_STRENGTH)
            + (self.speed * balance.COMBAT_SPEED)
            + (self.intelligence * balance.COMBAT_INTELLIGENCE)
        )
        readiness = (
            (self.health / balance.MAX_HEALTH)
            * (1 - self.hunger / balance.HUNGER_DEATH)
            * (self.stamina / self.max_stamina)
        )
        noise = self.rng.uniform(*balance.RANDOM_NOISE)
        return capacity * readiness * noise + weapon_modifier(self)

    def flee_value(self):
        # flee_value
        flee_value = (
            (self.speed * balance.FLEE_SPEED)
            + (self.stamina * balance.FLEE_STAMINA)
            + (self.intelligence * balance.FLEE_INTELLIGENCE)
        )
        flee_value += self.rng.randint(*balance.RANDOM_ADD)
        return flee_value

    def hide_value(self):
        # hide_value
        hide_value = (
            (self.stealth * balance.HIDE_STEALTH)
            + (self.intelligence * balance.HIDE_INTELLIGENCE)
            + (self.stamina * balance.HIDE_STAMINA)
        )
        hide_value += self.rng.randint(*balance.RANDOM_ADD)
        return hide_value

    def is_exhausted(self):
        return self.stamina < self.max_stamina * balance.EXHAUSTION_RATIO
