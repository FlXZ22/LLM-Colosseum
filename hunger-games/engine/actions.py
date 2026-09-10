from engine.item import has_item


def get_available_actions(game, agent):
    if not agent.alive:
        return []
    enemies = [
        n
        for n in game.agents
        if n != agent and n.alive and n.position == agent.position and not n.hidden
    ]
    if enemies:
        candidates = ["MOVE", "HIDE", "FLEE", "IGNORE"]
        if agent.hunger < 50 and agent.health > 50:
            candidates.append("ATTACK")
    else:
        candidates = ["MOVE", "REST", "SEARCH"]
    if has_item(agent, "medicine"):
        candidates.append("USE_ITEM")
    affordable = [a for a in candidates if game.stamina_cost(agent, a) <= agent.stamina]
    if not affordable:
        affordable = ["IGNORE"] if enemies else ["REST"]
    return sorted(affordable)


def get_available_targets(game, agent, action):
    target_actions = {"ATTACK", "FLEE"}
    if action not in target_actions:
        return []
    return sorted(
        [
            n
            for n in game.agents
            if n != agent and n.alive and n.position == agent.position and not n.hidden
        ],
        key=lambda x: x.name,
    )


# check if the LLM gave us a legal move
def is_legal(game, agent, action, target):
    available = get_available_actions(game, agent)
    # actions
    if not available and action is None:
        return True, "no actions are available"
    if action not in available:
        return False, f"{action} not available"
    # target
    if action in {"ATTACK", "FLEE"}:
        targets = get_available_targets(game, agent, action)
        if target is None:
            return False, f"{action} requires a target"
        if target not in targets:
            return False, f"{target} is invalid"
    else:
        if target is not None:
            return False, f"{action} does not require a target"
    return True, "Action is legal"
