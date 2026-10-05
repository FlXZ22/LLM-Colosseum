from dataclasses import dataclass
from config import balance

# salience
SALIENCE = balance.SALIANCE
# max memory cap
SUBJECT_BONUS = balance.SUBJECT_BONUS

@dataclass(frozen=True)
class Memory:
    id : str 
    turn : int
    kind : str
    subject : str
    text : str
    saliance : int

@dataclass(frozen=True)
class MemoryProfile:
    capacity: int
    fidelity: float
    decay_value: float

MEMORY_PROFILES = {
    "very_low":  MemoryProfile(capacity=4, fidelity=2, decay_value=0.25),
    "low":       MemoryProfile(capacity=8, fidelity=4, decay_value=0.15),
    "medium":    MemoryProfile(capacity=14, fidelity=6, decay_value=0.8),
    "high":      MemoryProfile(capacity=20, fidelity=8, decay_value=0.04),
    "very_high": MemoryProfile(capacity=30, fidelity=10, decay_value=0.01),
}

def memory_profile(intelligence):
    if intelligence < 35:
        # returns a memory_profile obgect
        return MEMORY_PROFILES["very_low"]
    elif intelligence < 50:
        return MEMORY_PROFILES["low"]
    elif intelligence < 65:
        return MEMORY_PROFILES["medium"]
    elif intelligence < 80:
        return MEMORY_PROFILES["high"]
    else:
        return MEMORY_PROFILES["very_high"]

def _get_field(event, field_name):
    # we check if there is a name in event
    if hasattr(event, field_name):
        return getattr(event, field_name)
    # we check if the event is a dict and then we search 
    if isinstance(event, dict):
        if field_name in event:
            return event[field_name]
    # we check if there is a data inside the event and then if it is a dict and the we are searching
    if "data" in event and isinstance(event["data"], dict):
        return event["data"].get(field_name)

def _first_person(event, active):
    loc = _get_field(event, "location")
    where = f"in the {loc}" if loc else ""

    actor = _get_field(event, "actor") or _get_field(event, "agent")
    target = _get_field(event, "target")
    other = target if active else actor

    event_type = (_get_field(event, "type") or "").lower()

    if event_type == "attack":
        if active:
            return f"You attacked {other} {where}." 

            return f"{other} attacked you {where}." 

# for the future beacuse there is no event named help and betrayed
#    if event_type == "help":
#        if active:
#            return f"You helped {other} {where}."
#        else:
#            return f"{other} helped you {where}"
#     for the future beacuse ther is no betrayal
#    if event_type == "betrayal":
#        if active:
#            return f"You betrayed {other} {where}." 
#        else:
#            return f"{other} betrayed you {where}." 
#
#    if event_type == "alliance":
#        return f"You and {other} agreed to work together {where}"

    if event_type in ("item", "item_drop"):
        name = _get_field(event, "name")
        return f"You found {name} {where}."
    if event_type == "flee":
        if active:
            return f"You ran from {other} {where}"
        else:
            return f"{other} ran from you {where}"

    if event_type == "death":
        return f"You watched {other} die {where}"
    
    return f"{event_type} {where}"


def remember(agent, event):
    raw_type = _get_field(event, "type")
    if not raw_type:
        return None
    # we are using lowercase to reduce confusion
    event_type = raw_type.lower()
    # this is the part that does not count some action like move and etc.
    saliance = SALIENCE.get(event_type)

    if saliance is None:
        return None

    actor = _get_field(event, "actor") or _get_field(event, "agent")
    target = _get_field(event, "target")

    # control check agent
    if agent.name not in (actor, target):
        return None
    # subject is the other person in the memory and action
    if actor == agent.name:
        active = True
        subject = target
    if target == agent.name:
        active = False
        subject = actor

    text = _first_person(event, active)
    turn = _get_field(event, "turn") or 0

    agent.memory_seq += 1
    
    # we are going to fill up the memory class
    memory = Memory(
        id = f"{agent.name}-m{agent.memory_seq:04d}",
        turn = turn,
        kind = event_type,
        subject = subject,
        text = text,
        saliance = saliance
    )
    # we are adding this memory to a list in the agent's class
    agent.memories.append(memory)
    # this uses intelligence to determine the memory_capacity of the agent
    memory_cap = memory_profile(agent.intelligence).capacity

    if len(agent.memories) > memory_cap:
        # first we sort the memories by saliance and turns 
        agent.memories.sort(key= lambda x: (x.saliance, x.turn))
        # second we remove the 13th
        agent.memories.pop(0)

    return memory

def relevance(memory, present, turn, agent):
    score = float(memory.saliance)
    # if the is the subject (the other person that cause this)
    # then we add the SUBJECT_BONUS to the relevance score
    if memory.subject and memory.subject in present:
        score += SUBJECT_BONUS
    # the memorys get less and less relevant with the time
    age = max(turn - memory.turn, 0)
    # intelligence that influence the decay rate
    decay = memory_profile(agent.intelligence).decay_value
    score -= age * decay
    score = max(0.0, score)
    return score

def recall(agent, present, turn, k=4):
    # we sort them by the score from relevance()
    ranked = sorted(
        agent.memories,
        key = lambda m : relevance(m, present, turn, agent),
        reverse = True,
    )
    # this way we choose the highest relevance memories
    chosen = ranked[:k]
    # we want it to be sorted even with the turns
    return sorted(chosen, key= lambda x : x.turn)

# this function calles the m.text from the memories from recall
def recall_text(agent, present, turn, k=4):
    fidelity = memory_profile(agent.intelligence).fidelity
    memories = recall(agent, present, turn, k)
    return [degrade(m, fidelity) for m in memories] 

def degrade(memory, fidelity):

    chance = (memory.saliance + fidelity) / 2
    
    # Level 3 (remember everything)
    if chance >= 8:
        return memory.text
    # Level 2 (Simply no locaiton)
    elif chance >= 5:
        text = memory.text
        if " in the " in text:
            text = text.split(" in the ")[0] + '.'
        return text
    
    # Level 1 (Simply no locaiton and name)
    text = memory.text
    if memory.subject and memory.subject in text:
        replacement = "Someone" if text.startswith(memory.subject) else "someone"
        text = text.replace(memory.subject, replacement)
    if " in the " in text:
        text = text.split(" in the ")[0] + '.'
    return text




