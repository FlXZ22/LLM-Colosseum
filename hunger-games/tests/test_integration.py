import unittest

from config import balance
from tests.harness import (
    run_match,
    check_invariants,
    sweep,
    _check_no_action_after_death,
    _check_items,
)


class TestIntegration(unittest.TestCase):
    def test_clean_sweep(self):
        broken = sweep(500)
        self.assertEqual([], broken, msg=f"{len(broken)} broken seeds: {broken}")

    def test_every_game_terminates(self):
        for seed in range(100):
            game, _ = run_match(seed)
            with self.subTest(seed=seed):
                self.assertLessEqual(
                    game.turn,
                    balance.MAX_TURNS,
                    msg=f"game.turn: {game.turn} is bigger than max_turns: {balance.MAX_TURNS}",
                )

    def test_seed_same_log(self):
        for seed in range(100):
            _, event_1 = run_match(seed)
            _, event_2 = run_match(seed)
            self.assertEqual(event_1, event_2)

    def test_no_action_after_death(self):
        for seed in range(100):
            game, events = run_match(seed)
            prob = _check_no_action_after_death(game, events)
            with self.subTest(seed=seed):
                self.assertEqual([], prob, msg=f"seed: {seed}, promblems: {prob}")

    def test_item_conservation(self):
        for seed in range(100):
            game, events = run_match(seed)
            prob = _check_items(game, events)
            with self.subTest(seed=seed):
                self.assertEqual([], prob, msg=f"seed: {seed}, promblems: {prob}")

    def test_checker(self):
        game, events = run_match(0)
        events[2]["seq"] = 999999
        self.assertNotEqual([], check_invariants(game, events))


if __name__ == "__main__":
    unittest.main()
