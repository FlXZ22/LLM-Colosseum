import argparse
from io import StringIO
import random

from engine.game import Game
from config import balance
from llm.profiles import PROFILES


parser = argparse.ArgumentParser()

parser.add_argument("-s", "--seed", type=int, help="put in the seed you want the game to run.")
parser.add_argument("-m", "--mode", type=int, default=0, nargs=2, help="1: llm, 0: random")
parser.add_argument("-p", "--personality", type=int, choices=[1, 2, 3], nargs=2)
parser.add_argument("-o", "-output", default="runs/game_data.jsonl")
args = parser.parse_args()


# while True:
#   raw = input("Give me the seed(default=0): ")
#   if raw == "":
#       seed = 0
#       break
#   try:
#       seed = int(raw)
#       break
#   except ValueError:
#       print("Please provide a valid seed, it should be an integer!")
#       continue
if args.seed != 0 and not args.seed:
    raise ValueError("Please input the seed")
if not args.personality:
    raise ValueError("Please input the personality [aggressor, survivalist, diplomat]")

log_path = args.output
rng = random.Random(args.seed)
PROFILE_CHOICES = {"1": "aggressor", "2": "survivalist", "3": "diplomat"}

profiles = [PROFILES[PROFILE_CHOICES[str(args.personality[0])]], PROFILES[PROFILE_CHOICES[str(args.personality[1])]]]

if args.mode == [0, 1]:
    brains = ["random", "llm"]
elif args.mode == [1, 0]:
    brains = ["llm", "random"]
elif args.mode == [1, 1]:
    brains = ["llm", "llm"]
else:
    brains = ["random", "random"]


game = Game(rng, args.seed, log_path, balance.AGENT_NAMES, profiles, brains = brains )

game.record("SEED", seed=args.seed)

while sum(a.alive for a in game.agents) > 1 and game.turn < balance.MAX_TURNS:
    game.run_turn()

alive = [a for a in game.agents if a.alive]
if len(alive) == 1:
    game.record("RESULT", result=f"{alive[0].name} is the winner of this hunger-game")
elif len(alive) == 0:
    game.record("RESULT", result="no survivors left")
else:
    game.record("RESULT", result="turn limit reached, no winner")
