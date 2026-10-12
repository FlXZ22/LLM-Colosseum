from dataclasses import dataclass
import json
from llm.request import ask


# This is currenty the random controller
class Controller:
    def __init__(self, rng):
        self.rng = rng

    def random_choose_action(self, obs):
        action = self.rng.choice(obs.legal_actions)
        target = None
        if action in {"ATTACK", "FLEE"}:
            target = self.rng.choice(obs.legal_targets[action])
        return action, target

    def choose_action(self, obs, agent):

        actions_targets = {
            action: obs.legal_targets.get(action) for action in obs.legal_actions
        }
        # personality, perception, legal_actions
        prompt = prompt_builder(agent.profile, obs, actions_targets)

        intent = None
        # Only 2 chances
        for _ in range(2):
            llm_responce = ask(prompt)
            if not llm_responce:
                continue
            intent = parse_intent(actions_targets, llm_responce)
            if intent is not None:
                break

        if intent is None:
            return self.random_choose_action(obs)
        else:
            action = intent.action
            #           raw_text = intent.raw_responce
            #           reason = intent.reason
            target = None
            if action in {"ATTACK", "FLEE"}:
                target = intent.target
            return action, target


@dataclass(frozen=True)
class Intent:
    action: str
    raw_text: str = ""
    # Optional and default value
    target: str | None = None
    reason: str | None = None


def prompt_builder(personality, perception, legal_actions: dict):

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
    {personality.to_prompt()}

    CURRENT SITUATION:
    {perception.to_prompt()}

    LEGAL ACTIONS:
    {action_text}

    Choose exactly one action from LEGAL ACTIONS. If the action has targets, you MUST choose one valid target from its list.
    Respond ONLY with a valid JSON object matching this schema:
    {{"action": "ACTION_NAME", "target": "TARGET_NAME or null", "reason": "short explanation"}}
    """
    # returns the prompt without spaces
    return prompt.strip()


def parse_intent(legal_actions: dict, llm_responce: str) -> Intent | None:

    # 2nd check
    if llm_responce is None:
        return None

    start = llm_responce.find("{")
    end = llm_responce.rfind("}")
    if start == -1 or end == -1 or start > end:
        return None
    json_llm = llm_responce[start : end + 1]

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
        action=chosen_action,
        raw_text=llm_responce,
        target=chosen_target,
        reason=data.get("reason"),
    )
