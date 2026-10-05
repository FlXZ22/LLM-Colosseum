from dataclasses import dataclass
import json

class Controller:
    def __init__(self, rng):
        self.rng = rng

    def choose_action(self, obs):
        action = self.rng.choice(obs.legal_actions)
        target = None
        if action in {"ATTACK", "FLEE"}:
            target = self.rng.choice(obs.legal_targets[action])
        return action, target


@dataclass(frozen=True)
class Intent:
    action: str
    raw_text: str = ""
    # Optional and default value
    target: str | None = None
    reason: str | None = None


def prompt_builder(personality, perception, memory, legal_actions):

    action_lines = []
    for action, target in legal_actions.items():
        # target is a list
        if target:
            action_lines.append(f"- {action} (targets: {', '.join(target)})")
        else:
            action_lines.append(f"- {action}")

    action_text = "\n".join(action_lines)
    prompt = f"""You are an agent in a survival simulation.

    PERSONALITY:
    {personality}

    CURRENT SITUATION:
    {perception}

    MEMORIES:
    {memory}

    LEGAL ACTIONS:
    {action_text}

    Choose exactly one action from LEGAL ACTIONS. If the action has targets, you MUST choose one valid target from its list.
    Respond ONLY with a valid JSON object matching this schema:
    {{"action": "ACTION_NAME", "target": "TARGET_NAME or null", "reason": "short explanation"}}
    """
    # returns the prompt without spaces
    return prompt.strip()


def parse_intent(legal_actions: dict, llm_responce: str) -> Intent | None:
    start = llm_responce.find("{")
    end = llm_responce.rfind("}")
    if start == -1 or end == -1 or start < end:
        return None
    json_llm = llm_responce[start:end+1]

    try:
        data = json.loads(json_llm)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(data, dict) or "action" not in data:
        return None

    chosen_action = str(data["action"]).upper()

    if chosen_action not in legal_actions:
        return None


    chosen_target = data.get("target") 
    legal_targets = legal_actions[chosen_action]

    if legal_targets is not None:
        if chosen_target not in legal_targets:
            return None
    else:
        chosen_target = None


    return Intent(
        action = chosen_action,
        raw_text = llm_responce,
        target = chosen_target,
        reason = data.get("reason")
    )
