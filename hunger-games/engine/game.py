import json

from agents.agent import Agent
from engine.world import LOCATIONS, LOCATIONS_NAME
from engine.actions import get_available_actions, get_available_targets, is_legal
from engine.item import Item, add_item, take_item
from engine.item import best_weapon
from config import balance
from agents.perception import observe


class Game:
    def __init__(self, rng, seed, log_path, names):
        self.seq = 0
        self.events = []
        self.rng = rng
        self.agents = [Agent(a, rng) for a in names]
        # turns of the game
        self.turn = 0
        self.log_path = log_path

    def run_turn(self):
        self.turn += 1

        for agent in self.agents:
            if not agent.alive:
                continue
            self.choose_action(agent)
            agent.hunger += balance.HUNGER_TICK
            self.record(
                "HUNGER_TICK",
                agent=agent.name,
                delta=balance.HUNGER_TICK,
                new_value=agent.hunger,
            )
            self._resolve(agent)

    def choose_action(self, agent):
        # self : game, agent : agent
        obs = observe(self, agent)
        if not obs.legal_actions:
            action, target_name = None, None
        else:
            action, target_name = agent.controller.choose_action(obs)
        target = next((n for n in self.agents if n.name == target_name), None)
        legal, reason = is_legal(self, agent, action, target)
        if not legal:
            raise ValueError(reason)
        self.execute_actions(agent, action, target_name)
        return action

    def execute_actions(self, agent, action, target_name=None):
        target = None
        if target_name is not None:
            target = next(n for n in self.agents if n.name == target_name)
        legal, reason = is_legal(self, agent, action, target)
        if not legal:
            raise ValueError(reason)
        # checking if the agent makes any loud moves when he is hidden
        if action in {"MOVE", "SEARCH", "ATTACK", "FLEE"}:
            agent.hidden = False
        if action == "REST":
            # variance
            r = self.rng.randint(-balance.REST_VARIANCE, balance.REST_VARIANCE)
            # Health
            health_before = agent.health
            agent.health += balance.REST_HEALTH_GAIN + r
            agent.clamp()
            health_delta = agent.health - health_before
            # Hunger
            hunger_before = agent.hunger
            agent.hunger += self.rng.randint(*balance.REST_HUNGER_COST)
            agent.clamp()
            hunger_delta = agent.hunger - hunger_before
            # stamina
            stamina_before = agent.stamina
            agent.stamina += balance.REST_STAMINA_GAIN + r
            agent.clamp()
            stamina_delta = agent.stamina - stamina_before
            # record the data
            self.record(
                "REST",
                agent=agent.name,
                health_delta=health_delta,
                hunger_delta=hunger_delta,
                stamina_delta=stamina_delta,
            )
        elif action == "MOVE":
            position = agent.position
            destinations = [x for x in LOCATIONS_NAME if x != agent.position]
            agent.position = self.rng.choice(destinations)
            cost = self._spend_stamina(agent, "MOVE")
            self.record(
                "MOVE",
                agent=agent.name,
                from_=position,
                to=agent.position,
                stamina_delta=cost,
            )
        elif action == "SEARCH":
            found = self.rng.random() < LOCATIONS[agent.position]["food"]
            if found:
                # found food
                agent.hunger -= balance.SEARCH_FOOD_GAIN
                cost = self._spend_stamina(agent, "SEARCH")
                self.record(
                    "SEARCH",
                    agent=agent.name,
                    found_food=True,
                    hunger_delta=balance.SEARCH_FOOD_GAIN,
                    stamina_delta=cost,
                )
                # inventory
                if self.rng.random() < balance.DROP_RATE:
                    lines = balance.LOOT_TABLE
                    rate = [x[2] for x in lines]
                    # randomly choses the item based on the rate
                    r = self.rng.choices(lines, rate, k=1)[0]
                    item = Item(kind=r[0], name=r[1])
                    add_item(agent, item)
                    self.record(
                        "ITEM_DROP",
                        agent=agent.name,
                        kind=item.kind,
                        name=item.name,
                        inventory_size=len(agent.inventory),
                    )
            else:
                agent.hunger += balance.SEARCH_FAIL_HUNGER
                cost = self._spend_stamina(agent, "SEARCH")
                self.record(
                    "SEARCH",
                    agent=agent.name,
                    found_food=False,
                    hunger_delta=balance.SEARCH_FAIL_HUNGER,
                    stamina_delta=cost,
                )
        elif action == "USE_ITEM":
            self._use_medicine(agent)
        elif action == "ATTACK":
            self._attack(agent, target)
        elif action == "FLEE":
            self._attempt_flee(agent, target)
        elif action == "HIDE":
            self._attempt_hide(agent)
        elif action == "IGNORE":
            self.record(
                "IGNORE", agent=agent.name, reason="The agent choses to do nothing"
            )
            pass
        elif action == None:
            self.record(
                "IGNORE", agent=agent.name, reason="The agent has nothing to do"
            )
            pass

    def _attack(self, a, b):
        winner, loser = (a, b) if a.combat_value() >= b.combat_value() else (b, a)
        loser.health -= balance.ATTACK_DAMAGE
        # stamina
        stamina_loser_cost = self._spend_stamina(loser, "ATTACK")
        stamina_winner_cost = self._spend_stamina(winner, "ATTACK")
        self.record(
            "ATTACK",
            actor=a.name,
            target=b.name,
            winner=winner.name,
            loser=loser.name,
            damage=balance.ATTACK_DAMAGE,
            location=winner.position,
            stamina_delta_loser=stamina_loser_cost,
            stamina_delta_winner=stamina_winner_cost,
            winner_weapon=best_weapon(winner),
            loser_weapon=best_weapon(loser),
        )
        self._resolve(winner)
        self._resolve(loser)

    def _append_to_jsonl(self, event):
        with open(self.log_path, "a") as file:
            json_line = json.dumps(event, ensure_ascii=False)
            file.write(json_line + "\n")

    def _attempt_flee(self, agent, target):
        if agent.flee_value() > target.flee_value():
            position = agent.position
            dest = self.rng.choice(
                [loc for loc in LOCATIONS_NAME if loc != agent.position]
            )
            agent.position = dest
            stamina_agent_cost = self._spend_stamina(agent, "FLEE")
            self.record(
                "FLEE",
                actor=agent.name,
                target=target.name,
                success=True,
                location=position,
                escaped_to=dest,
                stamina_delta_agent=stamina_agent_cost,
            )
        else:
            stamina_agent_cost = self._spend_stamina(agent, "FLEE")
            self.record(
                "FLEE",
                actor=agent.name,
                target=target.name,
                success=False,
                location=agent.position,
                escaped_to=None,
                stamina_delta_agent=stamina_agent_cost,
            )

    def _attempt_hide(self, agent):
        # we use the hide value and the "cover" from the location
        skill_value = max(
            0,
            min(
                1,
                (agent.hide_value() - balance.MIN_HIDE_VALUE)
                / (balance.MAX_HIDE_VALUE - balance.MIN_HIDE_VALUE),
            ),
        )
        chance = (skill_value + LOCATIONS[agent.position]["cover"]) / 2
        hidden = self.rng.random() < chance
        cost = self._spend_stamina(agent, "HIDE")
        if hidden:
            agent.hidden = True
            self.record(
                "HIDE",
                actor=agent.name,
                success=True,
                location=agent.position,
                stamina_delta_agent=cost,
            )
        else:
            agent.hidden = False
            self.record(
                "HIDE",
                actor=agent.name,
                success=False,
                spotted=True,
                location=agent.position,
                stamina_delta_agent=cost,
            )

    def record(self, event_type, **data):
        self.seq += 1
        event = {"seq": self.seq, "turn": self.turn, "type": event_type, "data": data}
        self.events.append(event)
        self._append_to_jsonl(event)
        return event

    def event_per_turn(self, n):
        return [e for e in self.events if e["turn"] == n]

    def stamina_cost(self, agent, action):
        base = balance.STAMINA_COST[action]
        if agent.is_exhausted():
            return round(base * balance.EXHAUSTION_MULTIPLIER)
        return base

    def _spend_stamina(self, agent, action):
        cost = self.stamina_cost(agent, action)
        agent.stamina -= cost
        agent.clamp()
        return cost

    def _resolve(self, agent):
        was_alive = agent.alive
        alive, reason = agent.validate()
        if was_alive and not alive:
            self.record("DEATH", agent=agent.name, cause=reason)
            if len(agent.inventory) != 0:
                lost = [{"kind": i.kind, "name": i.name} for i in agent.inventory]
                self.record("ITEMS_LOST", agent=agent.name, items=lost)
                agent.inventory = []

    def _use_medicine(self, agent):
        item = take_item(agent, "medicine")
        if not item:
            self.record("ITEM_USED", agent=agent.name, ok=False, reason="no medicine")
            return
        health_before = agent.health
        agent.health += balance.MEDICINE_HEAL
        agent.clamp()
        wasted = (agent.health - health_before) == 0
        cost = self._spend_stamina(agent, "USE_ITEM")
        self.record(
            "ITEM_USED",
            agent=agent.name,
            ok=True,
            health_before=health_before,
            health_after=agent.health,
            wasted=wasted,
            stamina_delta=cost,
        )
