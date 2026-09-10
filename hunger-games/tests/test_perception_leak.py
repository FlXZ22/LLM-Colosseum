import unittest

from agents.perception import observe
from config import balance
from tests.harness import new_game, alive_agents
from engine.item import Item


class TestPerceptionLeak(unittest.TestCase):
    """this function test if the .to_prompt() function has any number
    if it does then it will assertNotRegex
    beacuse we do not want any numbers in that function"""

    def test_perception_leak(self):
        for seed in [0, 1, 2, 3, 4, 5, 6, 7]:
            game = new_game(seed)
            for _ in range(10):
                game.run_turn()
                for agent in alive_agents(game):
                    text = observe(game, agent).to_prompt()
                    with self.subTest(seed=seed, agent=agent.name, turn=game.turn):
                        self.assertNotRegex(text, r"\d")

    """ this function test if the parameters
    are not in the to_prompt function """

    def test_no_raw_text(self):
        for seed in range(0, 11):
            game = new_game(seed)
            for _ in range(10):
                game.run_turn()
                for agent in alive_agents(game):
                    text = observe(game, agent).to_prompt()
                    for v in (
                        agent.health,
                        agent.hunger,
                        agent.stamina,
                        agent.max_stamina,
                        agent.strength,
                        agent.speed,
                        agent.intelligence,
                        agent.stealth,
                    ):
                        self.assertNotIn(str(v), text)

    """ this function check if the inventory is working correctly
        by adding an element and food and weapon and checking in the to_prompt
        function is saying it's name beacuse it should not """

    def test_secret(self):
        for seed in range(0, 11):
            game = new_game(seed)
            alive = alive_agents(game)
            if len(alive) < 2:
                continue
            A, B = alive[0], alive[1]
            A.position = B.position
            B.inventory.append(Item(kind="weapon", name="old katana"))
            text = observe(game, A).to_prompt()
            self.assertNotIn("katana", text)
            self.assertNotIn(str(B.health), text)
            self.assertNotIn(str(B.strength), text)
            A.inventory.append(Item(kind="food", name="stale bread"))
            self.assertIn("stale bread", observe(game, A).to_prompt())

    def test_obs(self):
        for seed in range(0, 11):
            game = new_game(seed)
            obs = observe(game, alive_agents(game)[0])
            self.assertTrue(len(obs.legal_actions) > 0)
            self.assertIn("ATTACK", obs.legal_targets)
            self.assertIn("FLEE", obs.legal_targets)
