from engine.game import Game

game = Game()

while sum(a.alive for a in game.agents) > 1:
    game.run_turn()

successor = next(a for a in game.agents if a.alive)
print("In the battleground there is only one left!")
print(f"{successor.name} is the solo remaining winner of this hunger-game")