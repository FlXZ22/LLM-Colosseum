import random

from agents.agent import Agent
from engine.world import locations


class Game:
    def __init__(self):
        self.agents = [
            Agent("Agent-A"),
            Agent("Agent-B")
        ]
        # turns of the game
        self.turn = 0
    
    def run_turn(self):
        self.turn += 1
        print(f"\n -- turn {self.turn} --")
        for agent in self.agents:
            if not agent.alive:
                continue
            action = agent.choose_action()
            agent.hunger += 5
            self.validate(agent)
            print(
                f"Name : {agent.name} |"
                f"Health : {agent.health} |"
                f"Position : {agent.position} |"
                f"Hunger : {agent.hunger} |"
                f"Action : {action} |"
            )
        self.encounter()    
    
    def encounter(self):
        a, b = self.agents[0], self.agents[1]
        if a.alive and b.alive and a.position == b.position:
            print(f"{a.name} meets {b.name} in {a.position}")
            action_a = a.choose_encounter()
            action_b = b.choose_encounter()
            self.resolve_encounter(a, b, action_a, action_b)
    
    def resolve_encounter(self, a, b, action_a, action_b):    
        print(f"{a.name} chooses {action_a}")
        print(f"{b.name} chooses {action_b}")
        
        match (action_a, action_b):
            case ("IGNORE", "IGNORE"):
                print("Nothing happens")
            case ("ATTACK", "IGNORE"):
                self._attack(a, b)
            case ("IGNORE", "ATTACK"):
                self._attack(a, b)
            case ("ATTACK", "FLEE" | "HIDE"):
                print(f"{a.name} tried to attack {b.name}, but he was gone!")
            case ("FLEE" | "HIDE", "ATTACK"):
                print(f"{b.name} tried to attack {a.name}, but he was gone!")
            case (("HIDE", "HIDE") | ("HIDE", "IGNORE") | ("IGNORE", "HIDE")):
                print("No one saw no one!")
        
        if action_a == "FLEE":
            self._flee(a)
        if action_b == "FLEE":
            self._flee(b)
        
    def _flee(self, agent):
        dest = random.choice([loc for loc in locations if loc != agent.position])
        agent.position = dest
        print(f"{agent.name} escaped to {agent.position}")
        
    def _attack(self, a, b):
        print(f"{a.name} vs {b.name}")
        winner, loser = (a, b) if a.combat_value() >= b.combat_value() else (b, a)
        print(f"{winner.name} wins")
        loser.health -= 25
        self.validate(a)
        self.validate(b)
                    
                 
    def validate(self, agent):
        agent.hunger = max(agent.hunger, 0)
        if agent.hunger >= 100:
            agent.alive = False
            print(f"{agent.name} has starved to death")
        elif agent.health <= 0:
            agent.alive = False
            print(f"{agent.name} has died due to low health")
            
  
    
