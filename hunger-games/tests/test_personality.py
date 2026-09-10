import unittest
from llm.personality import Personality

TRAITS = {
    "openness": "low",
    "conscientiousness": "high",
    "extraversion": "high",
    "agreeableness": "low",
    "neuroticism": "low",
}


class TestPersonality(unittest.TestCase):
    def test_valid_personality_and_prompt(self):
        p = Personality("Rocky", "Career tribute", TRAITS, ("Win",), ("Defeat",))
        self.assertEqual(p.name, "Rocky")
        prompt = p.to_prompt()
        self.assertIn("Name: Rocky", prompt)
        self.assertIn("Openness: low", prompt)
        self.assertIn("Goals: Win", prompt)
        self.assertIn("Fears: Defeat", prompt)

    def test_invalid_traits(self):
        # Missing traits
        with self.assertRaises(ValueError):
            Personality("Rocky", "Bg", {"openness": "low"}, ("Win",), ("Defeat",))

        # Invalid level value
        bad_level = {**TRAITS, "openness": "extreme"}
        with self.assertRaises(ValueError):
            Personality("Rocky", "Bg", bad_level, ("Win",), ("Defeat",))


if __name__ == "__main__":
    unittest.main()
