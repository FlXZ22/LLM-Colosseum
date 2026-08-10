import random

from engine.world import locations


class Agent:
    def __init__(self, name):
        self.name = name
        self.health = 100
        self.hunger = 0
        self.position = "cornucopia"
        self.alive = True
    def choose_action(self):
        choice = random.choice([
            "MOVE",
            "REST",
            "SEARCH_FOOD"
        ])
        if choice == "MOVE":
            self.position = random.choice(locations)
        elif choice == "REST":
            self.health = min(100, self.health + 5)
        elif choice == "SEARCH_FOOD" and random.random() < 0.5:
            self.hunger = max(0, self.hunger - 20)
        return choice

    def choose_encounter(self):
        return random.choice([
            "ATTACK",
            "HIDE",
            "FLEE",
            "IGNORE"
        ])