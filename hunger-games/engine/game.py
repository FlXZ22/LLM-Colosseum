import json

from agents.agent import Agent
from engine.world import locations
from engine.actions import get_avalible_actions, get_avalible_targets, is_legal

class Game:
    def __init__(self, rng, seed):
        self.data = {
            "seed" : seed,
            "turns" : []
        }
        self.rng = rng
        self.agents = [
            Agent("Agent-A", rng),
            Agent("Agent-B", rng)
        ]
        # turns of the game
        self.turn = 0
    
    def run_turn(self):
        self.turn_data = {}
        self.turn += 1
        print(f"\n -- turn {self.turn} --")
        actions = {}
        
        for agent in self.agents:
            action = self.choose_action(agent) 
            actions[agent.name] = action
            agent.hunger += 5
            agent.validate()
            
            print(
                f"Name : {agent.name} |"
                f"Health : {agent.health} |"
                f"Position : {agent.position} |"
                f"Hunger : {agent.hunger} |"
                f"Action : {action} |"
            )
        
        encounter_data = self.encounter()
        turn_data = {
            "turn" : self.turn,
            "agents" : [],
            "encounter" : encounter_data
        }
        for agent in self.agents:
            agent_data = {
                "name" : agent.name,
                "health" : agent.health,
                "position" : agent.position,
                "hunger" : agent.hunger,
                "alive" : agent.alive,
                "action" : actions.get(agent.name),
            }
            turn_data["agents"].append(agent_data)    
        self.data["turns"].append(turn_data)
        # covert into jsonl
        self.convert_jsonl(turn_data)
    
    def choose_action(self, agent):
        avalible = get_avalible_actions(self, agent)
        if not avalible:
            action = None
        else:
            action = agent.choose_action(avalible)
        target = None
        if action in {"ATTACK", "FLEE", "HIDE"}:
            targets = get_avalible_targets(self, agent, action)
            target = self.rng.choice(targets)
        legal, reason = is_legal(self, agent, action, target)
        if not legal:
            raise ValueError(reason)
        if target == None:
            self.execute_actions(agent, action, None)
        else:
            self.execute_actions(agent, action, target.name)
        return action
            
    def execute_actions(self, agent, action, target_name=None):
        legal, reason = is_legal(self, agent, action, target_name)
        if not legal:
            raise ValueError(reason)
        
        target = None
        
        if target_name is not None:
            target = next(n for n in self.agents if n.name == target_name)
        if action == "REST":
            # Health
            agent.health += 15
            agent.health +=  self.rng.randint(-5, +5)
            # Hunger
            agent.hunger += 10
            agent.hunger +=  self.rng.randint(-5, +5)
        elif action == "MOVE":
            destinations = [x for x in locations if x != agent.position]
            agent.position = self.rng.choice(destinations)
        elif action == "SEARCH":
            choice = self.rng.randint(0, 1)
            if choice == 0:
                # found food
                agent.hunger -= 35
            else:
                agent.hunger += 10
        elif action == "ATTACK":
            self._attack(agent, target)
        elif action == "FLEE":
            self._atemptflee(agent, target)
        elif action == "HIDE":
            self._atempthide(agent, target)
        elif action == None:
            print(f"{agent.name} cannot do anything!")
            pass
        
    def _hide(self, agent):
        print(f"{agent.name} is succesfully hidden") 
    
    def _flee(self, agent): 
        dest = self.rng.choice([loc for loc in locations if loc != agent.position])
        agent.position = dest
        print(f"{agent.name} escaped to {agent.position}")

    def _attack(self, a, b):
        print(f"{a.name} vs {b.name}")
        winner, loser = (a, b) if a.combat_value() >= b.combat_value() else (b, a)
        print(f"{winner.name} wins")
        loser.health -= 50
        a.validate()
        b.validate()
    
    def convert_jsonl(self, turn_data):
        with open("game_data.jsonl", "a") as file:
            json_line = json.dumps(turn_data, ensure_ascii=False)
            file.write(json_line + "\n")
        
    def _atemptflee(self, agent, target):
        if agent.flee_value() > target.flee_value():
            self._flee(agent)
        else:
            print(f"{target.name} caught {agent.name}")
            action = self.choose_action(target)

    def _atempthide(self, agent, target):
        if agent.hide_value() > target.hide_value():
            self._hide(agent)
        else:
            print(f"{target.name} caught {agent.name}")
            action = self.choose_action(target)

            
