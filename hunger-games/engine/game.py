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
        def attack(a, b):
            print(f"{a.name} vs {b.name}")
            winner = random.choice([a, b])
            if winner == a:
                loser = b
            else:
                loser = a
            print(f"{winner.name} wins")
            loser.health -= 25
            if loser.health <= 0:
                loser.health = 0
                loser.alive = False
        def possible_location(agent, locations):
            p_locations = locations.copy()
            p_locations.remove(agent.position)
            return p_locations
        # print agent a and agent b actions
        print(f"{a.name} chooses {action_a}")
        print(f"{b.name} chooses {action_b}")
        # possible outcome
        if action_a == "IGNORE" and action_b == "IGNORE":
            print("Nothing happens")
        if action_a == "ATTACK" and action_b == "IGNORE":
            attack(a, b)
        if action_b == "ATTACK" and action_a == "IGNORE":
            attack(a, b)
        if action_a == "FLEE":
            p_locations = possible_location(a, locations)
            a.position = random.choice(p_locations)
            print(f"{a.name} escaped to {a.position}")
        if action_b == "FLEE":
            p_locations = possible_location(b, locations)
            b.position = random.choice(p_locations)
            print(f"{b.name} escaped to {b.position}")
        if action_a == "ATTACK" and action_b == "ATTACK":
            attack(a, b)
            
                
    def validate(self, agent):
        agent.hunger = max(agent.hunger, 0)
        if agent.hunger >= 100 or agent.health <= 0:
            agent.alive = False
            
  
    
