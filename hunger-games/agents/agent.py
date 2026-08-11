import random

from engine.world import locations


class Agent:
    def __init__(self, name):
        self.name = name
        self.health = 100
        self.strength = random.randint(25, 100)
        self.speed = random.randint(25, 100)
        self.stamina = random.randint(25, 100)
        self.intelligence = random.randint(25, 100)
        self.hunger = 0
        self.position = "cornucopia"
        self.alive = True
    
    def validate(self):
        self.hunger = max(0, self.hunger)
        if self.hunger >= 100 or self.health <= 0:
            self.alive = False
    
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
        self.validate()
        return choice

    def choose_encounter(self):
        return random.choice([
            "ATTACK",
            "FLEE",
            "HIDE",
            "IGNORE"
        ])
    
    def combat_value(self):
        value = (self.strength * 0.30) + (self.speed * 0.25) + (self.intelligence * 0.20) + (self.stamina * 0.25)
        # checking the health
        if self.health >= 75:
            value += 15
        elif self.health <= 25:
            value -= 15
        # checking the hunger
        if self.hunger >= 75:
            value -= 10 
        elif self.hunger <= 15:
            value += 10
        # adding randomnality
        value += random.randint(-10, 10)
        self.validate()
        return value
    
    
        
            
            