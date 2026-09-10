from dataclasses import dataclass
from config import balance


@dataclass(frozen=True)
class Item:
    kind: str
    name: str


def add_item(agent, item):
    agent.inventory.append(item)


def has_item(agent, kind):
    item = any(item.kind == kind for item in agent.inventory)
    if item:
        return True
    else:
        return False


def take_item(agent, kind):
    for item in agent.inventory:
        if item.kind == kind:
            agent.inventory.remove(item)
            return item
    return None


def weapon_modifier(agent):
    mods = [
        balance.WEAPON_MODIFIERS[i.name]
        for i in agent.inventory
        if i.kind == "weapon" and i.name in balance.WEAPON_MODIFIERS
    ]
    return max(mods) if mods else 0


def best_weapon(agent):
    weapons = [
        i
        for i in agent.inventory
        if i.kind == "weapon" and i.name in balance.WEAPON_MODIFIERS
    ]
    if not weapons:
        return None
    return max(weapons, key=lambda x: balance.WEAPON_MODIFIERS[x.name]).name
