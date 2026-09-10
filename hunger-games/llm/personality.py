from dataclasses import dataclass

# these are from the OCEAN Personality traits reserach and they are the most accurate for Personalitys
TRAIT_NAMES = (
    "openness",
    "conscientiousness",
    "extraversion",
    "agreeableness",
    "neuroticism",
)
ALLOWED_LEVELS = {"high", "medium", "low"}


@dataclass(frozen=True)
class Personality:
    name: str
    background: str
    traits: dict
    goals: tuple
    fears: tuple

    def __post_init__(self):
        if set(self.traits.keys()) != set(TRAIT_NAMES):
            raise ValueError(f"Traits must exactly match {TRAIT_NAMES}")
        for traits, level in self.traits.items():
            if level not in ALLOWED_LEVELS:
                raise ValueError(f"Traits level must be in {ALLOWED_LEVELS}")

    def to_prompt(self):
        traits_line = "\n".join(
            f"{k.capitalize()}: {v}" for k, v in self.traits.items()
        )
        goals_line = ", ".join(self.goals)
        fears_line = ", ".join(self.fears)

        return (
            f"Name: {self.name}\n"
            f"Background: {self.background}\n"
            f"Traits:\n{traits_line}\n"
            f"Goals: {goals_line}\n"
            f"Fears: {fears_line}"
        )
