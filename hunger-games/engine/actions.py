def get_avalible_actions(game, agent):
    if agent.alive == False:
        return []
    enemies = [n for n in game.agents if n != agent and n.alive and n.position == agent.position]    
    if agent.stamina <= 0:
        if enemies:
            return ["IGNORE"]
        return ["REST"]
    if enemies:
        actions = ["MOVE", "HIDE", "FLEE", "IGNORE"]
        if agent.hunger < 50 and agent.health > 50:
            actions.append("ATTACK")
            # we sort by name
        return sorted(actions)
    return ["MOVE", "REST", "SEARCH"]

def get_avalible_targets(game, agent, action):
    target_actions = {"ATTACK", "FLEE", "HIDE"}
    if action not in target_actions:
        return []
    return sorted([n for n in game.agents if n != agent and n.alive and n.position == agent.position], key=lambda x : x.name)

# check if the LLM gave us a legal move
def is_legal(game, agent, action, target):
    avalible = get_avalible_actions(game, agent)
    if action not in avalible:
        return False, f"{action} not avalible"
    if action == "ATTACK":
        targets = get_avalible_targets(game, agent, action)
        if target not in targets:
            return False, f"{target} not here"
    return True, "Action is legal"                  
    
