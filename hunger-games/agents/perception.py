from engine.world import LOCATIONS
from engine.actions import get_available_actions, get_available_targets


class Observation:
    def __init__(
        self,
        name,
        position,
        health,
        hunger,
        stamina,
        exhausted,
        room,
        others,
        legal_actions,
        legal_targets,
        turn,
        inventory,
    ):
        self.name = name
        self.position = position
        self.health = health
        self.hunger = hunger
        self.stamina = stamina
        self.exhausted = exhausted
        self.room = room
        self.others = others
        self.legal_actions = legal_actions
        self.legal_targets = legal_targets
        self.turn = turn
        self.inventory = inventory

    def to_prompt(self):
        line = []
        line.append("You are " + self.name + " in the " + self.position + ".")
        line.append(
            "You feel " + self.health + ", " + self.hunger + ", " + self.stamina + "."
        )
        line.append("Around you: " + self.room + ".")
        if self.others:
            line.append("Also here: " + "; ".join(self.others) + ".")
        else:
            line.append("You are alone here")
        line.append(
            "Your pack: "
            + (", ".join(self.inventory) if self.inventory else "empty")
            + "."
        )
        line.append("You can: " + ", ".join(self.legal_actions) + ".")
        return "\n".join(line)


def observe(game, agent):
    others = [
        describe_other(agent, n)
        for n in game.agents
        if n != agent and n.alive and n.position == agent.position and not n.hidden
    ]

    legal_actions = get_available_actions(game, agent)

    legal_targets = {
        "ATTACK": [x.name for x in get_available_targets(game, agent, "ATTACK")],
        "FLEE": [x.name for x in get_available_targets(game, agent, "FLEE")],
    }

    return Observation(
        name=agent.name,
        position=agent.position,
        health=health_phrase(agent.health),
        hunger=hunger_phrase(agent.hunger),
        stamina=stamina_phrase(agent.stamina, agent.max_stamina),
        exhausted=agent.is_exhausted(),
        room=locations_phrase(agent.position),
        others=others,
        legal_actions=legal_actions,
        legal_targets=legal_targets,
        turn=game.turn,
        inventory=[i.name for i in agent.inventory],
    )


def health_phrase(health):
    if health <= 20:
        return "on the brink"
    elif health <= 40:
        return "badly hurt"
    elif health <= 60:
        return "hurting"
    elif health <= 85:
        return "bruised"
    return "unhurt"


def hunger_phrase(hunger):
    if hunger >= 85:
        return "starving"
    elif hunger >= 60:
        return "very hungry"
    elif hunger >= 35:
        return "hungry"
    elif hunger >= 15:
        return "peckish"
    return "well fed"


def stamina_phrase(stamina, max_stamina):
    r = stamina / max_stamina
    if r < 0.15:
        return "exhausted"
    elif r < 0.35:
        return "tired"
    elif r < 0.60:
        return "winded"
    elif r < 0.85:
        return "steady"
    return "fresh"


def locations_phrase(position):
    r = LOCATIONS[position]
    cover = "well hidden" if r["cover"] >= 0.6 else "exposed"
    food = "food looks plentiful" if r["food"] >= 0.6 else "food looks scarce"
    # danger = "looks vulnerable from attacks" if r["danger"] >= 0.6 else "looks very protected from attacks"
    return cover + ", " + food  # + ", " + danger


def describe_other(agent, other):
    if other.health <= 40:
        condition = "looks badly hurt"
    elif other.health <= 75:
        condition = "looks hurt"
    else:
        condition = "looks unhurt"

    report = [other.name + " " + condition]

    if other.is_exhausted():
        report.append("moving slowly")

    if any(x.kind == "weapon" for x in other.inventory):
        report.append("clutching something you can't make out")

    return ", ".join(report)
