import random

from engine.game import Game

seed_input = input("Give me the seed(default=0): ")
if not seed_input:
    seed = 0
else:
    seed = int(seed_input)
rng = random.Random(seed)
print(f"seed: {seed}")

game = Game(rng, seed)
open("game_data.jsonl", "w").close()
while sum(a.alive for a in game.agents) > 1:
    game.run_turn()

successor = next(a for a in game.agents if a.alive)
if not successor:
    print("They are both dead at the same time!")
else:
    print("In the battleground there is only one left!")
    print(f"{successor.name} is the solo remaining winner of this hunger-game")
