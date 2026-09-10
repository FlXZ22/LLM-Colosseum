import random

from engine.game import Game
from config import balance
while True:
    raw = input("Give me the seed(default=0): ")
    if raw == "":
        seed = 0
        break
    try:
        seed = int(raw)
        break
    except ValueError:
        print("Please provide a valid seed, it should be an integer!")
        continue
log_path = "runs/game_data.jsonl"
rng = random.Random(seed)
game = Game(rng, seed, log_path, balance.AGENT_NAMES)
open(log_path, "w").close()
game.record("SEED", seed=seed)
while sum(a.alive for a in game.agents) > 1 and game.turn < balance.MAX_TURNS:
    game.run_turn()

alive = [a for a in game.agents if a.alive]
if len(alive) == 1:
    game.record("RESULT", result=f"{alive[0].name} is the winner of this hunger-game")
elif len(alive) == 0:
    game.record("RESULT", result="no survivors left")
else:
    game.record("RESULT", result="turn limit reached, no winner")
