class Controller:
    def __init__(self, rng):
        self.rng = rng

    def choose_action(self, obs):
        action = self.rng.choice(obs.legal_actions)
        target = None
        if action in {"ATTACK", "FLEE"}:
            target = self.rng.choice(obs.legal_targets[action])
        return action, target
