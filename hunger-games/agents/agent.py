from engine.world import locations


class Agent:
    def __init__(self, name, rng):
        self.name = name
        self.rng = rng
        self.health = 100
        self.strength = self.rng.randint(25, 100)
        self.speed = self.rng.randint(25, 100)
        self.stamina = self.rng.randint(25, 100)
        self.intelligence = self.rng.randint(25, 100)
        self.stealth = self.rng.randint(25, 100)
        self.hunger = 0
        self.position = "cornucopia"
        self.alive = True
    
    def validate(self):
        self.hunger = max(0, self.hunger)
        if self.hunger >= 100:
            self.alive = False
            print(f"{self.name} has starved to death")
        elif self.health <= 0:
            self.alive = False
            print(f"{self.name} has died due to low health")
    
    def choose_action(self, avalible_actions):
        return self.rng.choice(avalible_actions)
    
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
        # adding randomality
        value += self.rng.randint(-10, 10)
        self.validate()
        return value
    
    def flee_value(self):
        # flee_value
        flee_value = (self.speed * 0.40) + (self.stamina * 0.40) + (self.hunger * 0.20)
        flee_value += self.rng.randint(-10, 10)
        return flee_value
    def hide_value(self):
        # hide_value
        hide_value = (self.stealth * 0.40) + (self.intelligence * 0.40) + (self.stamina * 0.20)
        hide_value += self.rng.randint(-10, 10)
        return hide_value
    
        
            
            
