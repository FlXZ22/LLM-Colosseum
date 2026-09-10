import random
import json

from engine.game import Game
from engine.world import LOCATIONS_NAME
from config import balance


def new_game(seed, log_path="runs/_sweep.jsonl"):
    rng = random.Random(seed)
    game = Game(rng, seed, log_path, balance.AGENT_NAMES)
    open(log_path, "w").close()
    game.record("SEED", seed=seed)
    return game


def alive_agents(game):
    return [a for a in game.agents if a.alive]


def run_match(seed, log_path="runs/_sweep.jsonl"):
    game = new_game(seed, log_path)
    while sum(a.alive for a in game.agents) > 1 and game.turn < balance.MAX_TURNS:
        game.run_turn()

    alive = [a for a in game.agents if a.alive]
    if len(alive) == 1:
        game.record(
            "RESULT", result=f"{alive[0].name} is the winner of this hunger-game"
        )
    elif len(alive) == 0:
        game.record("RESULT", result="no survivors left")
    else:
        game.record("RESULT", result="turn limit reached, no winner")

    return game, game.events


def actor_name(e):
    agent = e["data"].get("agent")
    actor = agent if agent else e["data"].get("actor")
    return actor


def _check_log(events):
    problems = []
    for i, e in enumerate(events):
        if e["seq"] != i + 1:
            problems.append(f"expected seq: {str(i+1)} found: {str(e["seq"])}")
        if not all(k in e for k in ("seq", "turn", "type", "data")):
            problems.append(f"event without any base key: {str(e)}")
        try:
            json.dumps(e)
        except Exception:
            problems.append(f"event not serializable seq: {str(e["seq"])}")
    turns = [e["turn"] for e in events]
    if turns != sorted(turns):
        problems.append("turns are not in order")
    return problems


def _check_agents(game, events):
    problems = []
    for a in game.agents:
        # health, hunger, stamina
        if a.hunger < 0:
            problems.append(f"{a.name} hunger is negative")
        if a.health > balance.MAX_HEALTH:
            problems.append(f"{a.name} health is out of range")
        if not (0 <= a.stamina <= a.max_stamina):
            problems.append(f"{a.name} stamina is out of range")
        # healht, stamina
        if a.alive and a.hunger >= balance.HUNGER_DEATH:
            problems.append(f"{a.name} is alive, but it should be death due to hunger")
        if a.alive and a.health <= 0:
            problems.append(
                f"{a.name} is alive, but it should be death due to low health"
            )
        # records and position
        if not a.alive and not any(
            e["type"] == "DEATH" and e["data"].get("agent") == a.name for e in events
        ):
            problems.append(f"{a.name} is dead, but there is not record")
        if a.position not in LOCATIONS_NAME:
            problems.append(f"{a.name} is in a not registerd place: {a.position}")
    return problems


ACTION_TYPES = {
    "REST",
    "MOVE",
    "SEARCH",
    "ATTACK",
    "FLEE",
    "HIDE",
    "USE_ITEM",
    "IGNORE",
    "ITEM_USED",
    "ITEM_DROP",
}


def _check_no_action_after_death(game, events):
    problems = []
    for a in game.agents:
        DEATH_TURN = None
        for e in events:
            if e["type"] == "DEATH" and e["data"].get("agent") == a.name:
                DEATH_TURN = e["turn"]
                break
        if DEATH_TURN == None:
            continue
        for e in events:
            if (
                DEATH_TURN < e["turn"]
                and e["type"] in ACTION_TYPES
                and actor_name(e) == a.name
            ):
                problems.append(
                    f"{a.name} has executed an action in turn: {e["turn"]} after death in turn: {DEATH_TURN}"
                )
    return problems


def _check_termination(game):
    problems = []
    if game.turn > balance.MAX_TURNS:
        problems.append(
            f"the game turns: {game.turn} are bigger that the maximum consented tuns: {balance.MAX_TURNS}"
        )
    alive = sum(a.alive for a in game.agents)
    if alive > 1 and game.turn < balance.MAX_TURNS:
        problems.append(
            f"the game is finished, but there are still {alive} agents alive"
        )
    return problems


def _check_items(game, events):
    problems = []
    for a in game.agents:
        input_item = sum(
            1
            for e in events
            if e["type"] == "ITEM_DROP" and e["data"].get("agent") == a.name
        )
        used_item = sum(
            1
            for e in events
            if e["type"] == "ITEM_USED"
            and e["data"].get("agent") == a.name
            and e["data"].get("ok") is True
        )
        lost_item = sum(
            len(e["data"]["items"])
            for e in events
            if e["type"] == "ITEMS_LOST" and e["data"].get("agent") == a.name
        )
        remaining_item = len(a.inventory)
        if input_item != remaining_item + lost_item + used_item:
            problems.append(
                f"{a.name}: entrati {input_item} ≠ rimasti+usati+persi {remaining_item + used_item + lost_item}"
            )
    return problems


def _check_events(events, alive_agent_names):
    problems = []
    for e in events:
        t = e["type"]
        d = e["data"]

        if t == "MOVE":
            if d["from_"] == d["to"]:
                problems.append(
                    f"Move seq {e["seq"]} the from_ == to, from_: {d["from_"]} ,to: {d["to"]}"
                )
        if t == "FLEE":
            if d["success"] is True and d["escaped_to"] is None:
                problems.append(
                    f"seq: {e["seq"]}. the agent successfully fleed, but did not escape"
                )
            if d["success"] is False and d["escaped_to"] is not None:
                problems.append(
                    f"seq: {e["seq"]}. the agent did not flee, but he escaped"
                )

        if t in ("ATTACK", "FLEE"):
            for name in (d["actor"], d["target"]):
                if name not in alive_agent_names:
                    problems.append(f"seq: {e["seq"]}. name outside of alive_agents")
    return problems


def check_invariants(game, events):
    alive_agent_names = [a.name for a in game.agents]
    return (
        _check_log(events)
        + _check_agents(game, events)
        + _check_no_action_after_death(game, events)
        + _check_termination(game)
        + _check_items(game, events)
        + _check_events(events, alive_agent_names)
    )


def sweep(n=500):
    broken = []
    for seed in range(n):
        try:
            game, events = run_match(seed)
            v = check_invariants(game, events)
        except Exception as err:
            v = [f"Crash: {repr(err)}"]
        if v:
            broken.append((seed, v))
    print(f"{str(len(broken))} are broken seeds out of {str(n)}")
    return broken
