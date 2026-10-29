from dataclasses import dataclass
import json
from llm.request import ask


# This is currenty the random controller
class Controller:
    def __init__(self, rng, brain="llm"):
        self.rng = rng
        self.brain = brain

    def random_choose_action(self, obs, status_code):
        action = self.rng.choice(obs.legal_actions)
        target = None
        if action in {"ATTACK", "FLEE"}:
            targets = obs.legal_targets.get(action)
            target = self.rng.choice(targets) if targets else None

        if not status_code:
            reason = "Network Error."
            raw_text = "No text came back."
        elif status_code == 401:
            reason = "401 Invalid credentials"
            raw_text = "Invalid credentials: the key is wrong or disabled"
        elif status_code == 402:
            reason = "402 Insufficient credits"
            raw_text = "Insufficient credits: you’re out of money"
        elif status_code == 403:
            reason = "403 Forbidden"
            raw_text = "Forbidden: a moderation or guardrail block"
        elif status_code == 408:
            reason = "408 Timeout"
            raw_text = "Request timed out"
        elif status_code == 429:
            reason = "429 Too many requests"
            raw_text = "Rate limited: too many requests"
        elif status_code == 502:
            reason = "502 Server Error"
            raw_text = "The model is down or gave an invalid response"
        elif status_code == 503:
            reason = "503 Server Error"
            raw_text = "No provider available"
        elif status_code == 200:
            reason = "Invalid Action"
            raw_text = "Invalid Action: a bad json response"
        elif status_code == "random":
            reason = "random brain"
            raw_text = "random brain actions"
        else:
            reason = f"{status_code} Error"
            raw_text = f"Unexpected HTTP {status_code}"

        return Intent(
            action=action,
            raw_text=raw_text,
            target=target,
            reason=reason,
            is_random=True,
        )

    def choose_action(self, obs, agent):
        ## this is the line of code for random brain

        if self.brain == "random":
            return self.random_choose_action(obs, status_code="random")

        actions_targets = {
            action: obs.legal_targets.get(action) for action in obs.legal_actions
        }
        # personality, perception, legal_actions
        prompt = prompt_builder(agent.profile, obs, actions_targets)

        intent = None
        # default
        status_code = 200
        # Only 2 chancesk
        for _ in range(2):
            llm_responce, code = ask(prompt)
            if code != 200 and status_code == 200:
                status_code = code
            if not llm_responce:
                continue
            intent = parse_intent(actions_targets, llm_responce)
            if intent is not None:
                break

        if intent is None:
            return self.random_choose_action(obs, status_code)
        else:
            # we return an Intent object
            return intent


@dataclass(frozen=True)
class Intent:
    action: str
    raw_text: str = ""
    # Optional and default value
    target: str | None = None
    reason: str | None = None
    is_random: bool = False


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
        is_random=False,
    )
