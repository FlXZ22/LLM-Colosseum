import re
import time
from dataclasses import dataclass, field, replace
import json
from llm.request import ask


# This is currenty the random controller
class Controller:
    def __init__(self, rng, brain="llm"):
        self.rng = rng
        self.brain = brain

    def random_choose_action(self, obs, status_code, error_type):
        action = self.rng.choice(obs.legal_actions)
        target = None
        if action in {"ATTACK", "FLEE"}:
            targets = obs.legal_targets.get(action)
            target = self.rng.choice(targets) if targets else None

        error = {
            "random": (
                "Random brain",
                "Random brain activated"
            ),
            "Timeout": (
                "Timeout of the request",
                "The request took longer that timeout"
            ),
            "ConnectionError": (
                "Connection error",
                "The connection failed"
            ),
            "BudgetCall": (
                "Budgetcall reached",
                "The limit of the Budgetcall reached"
            ),
            "RequestException": (
                "Request erro",
                "The request had a RequestException error"
            ),
            "NullContent": (
                "The responce is empty/null",
                "The llm responce is empty/null"
            ),
            "JsonError": (
                "Error parsing json",
                "Error when parsing json responce"
            )
        }

        error_code = {
            200: (
                "invalid action",
                "Invalid json responce"
            ),
            401: (
                "401 Invalid credentials",
                "Invalid credentials: the key is wrong or disabled"
            ),
            402: (
                "402 Insufficient credits",
                "Insufficient credits: you’re out of money"
            ),
            403: (
                "403 Forbidden",
                "Forbidden: a moderation or guardrail block"
            ),
            404: (
                "404 Not found",
                "Not found, the request was not found"
            ),
            429: (
                "429 Too many requests",
                "Rate limited: too many requests"
            ),
            502: (
                "502 Server Error",
                "The model is down or gave an invalid response"
            ),
            503: (
                "Service is unavailible",
                "The service is termporary unavailble"
            ),
        }

        if error_type in error:
            reason, raw_text = error[error_type]
        elif status_code in error_code:
            reason, raw_text = error_code[status_code]
        else:
            reason = f"Error: {status_code}"
            raw_text = f"Unexpected HTTP status_code: {status_code}, error_type: {error_type}"



        return Intent(
            action=action,
            raw_text=raw_text,
            target=target,
            reason=reason,
            is_random=True,
        )

    def choose_action(self, obs, agent, budget):
        # start the timer
        start = time.perf_counter()
        # this is the line of code for random brain
        if self.brain == "random":
            return self.random_choose_action(obs, status_code="random", error_type="random")

        actions_targets = {
            action: obs.legal_targets.get(action) for action in obs.legal_actions
        }
        # personality, perception, legal_actions
        prompt = prompt_builder(agent.profile, obs, actions_targets)

        intent = None
        error_type = "Success"
        status_code = 200
        # a list of all the errors
        attempts = []
        # Only 2 chancesk
        for attempt in range(2):

            if budget.take():
                # LLM request using ask()
                error_type, llm_responce, code = ask(prompt)
                status_code = code
                attempts.append({"attempt": attempt + 1, "error_type" : error_type, "status_code": status_code})
            else:
                error_type = "BudgetCall"
                break

            if error_type in {"Timeout", "ConnectionError"}:
                if attempt == 0:
                    time.sleep(1)
                    continue
                else:
                    break

            if error_type in {"NullContent", "JsonError"}:
                continue

            # these code should NOT continue, but break
            if code in {400, 401, 402, 403, 404}:
                break

            elif code in {x for x in range(500, 600)} or code == 429:
                if attempt == 0:
                    time.sleep(1)
                    continue
                else:
                    break

            if not llm_responce:
                continue

            intent = parse_intent(actions_targets, llm_responce)
            # if parse_intent return None this mean that the llm responce was not correct
            if intent is None:
                attempts[-1]["error_type"] = "InvalidIntent"
            else:
                break

        if intent is None:
            # if the intent has nothing we fallback to the random_choose_action()
            intent = self.random_choose_action(obs, status_code, error_type)
        # in the intent class replace attempt with this attempt
        end = time.perf_counter()
        # latency in ms
        latency = (end - start) * 1000
        return replace(intent, attempts=attempts, latency=latency)


@dataclass(frozen=True)
class Intent:
    action: str
    raw_text: str = ""
    # Optional and default value
    target: str | None = None
    reason: str | None = None
    attempts: list[dict] = field(default_factory=list)
    latency: float = 0.0
    is_random: bool = False


class BudgetCall:
    def __init__(self, used, limit):
        self.used = used
        self.limit = limit

    def take(self):
        # if the limit is reached
        if self.used >= self.limit:
            return False
        # if there is stil limit available
        else:
            self.used += 1
            return True
            
            


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

    # we only accept str as the input, so no INT
    # if it's not a string
    if not isinstance(llm_responce, str):
        return None

    start = llm_responce.find("{")
    # we use rfint to find the next bracket (next occurences)
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

    # default list
    attempts = []

    return Intent(
        action=chosen_action,
        raw_text=llm_responce,
        target=chosen_target,
        reason=data.get("reason"),
        attempts=attempts,
        is_random=False,
    )
