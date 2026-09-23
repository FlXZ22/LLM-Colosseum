# LLM Hunger Games — Project Info

> Single source of truth for what this project is, how it is built today, and
> where it is going. Keep this file updated as the engine changes.
> Repo folder is currently named `LLM-Colosseum`; the project itself is
> **LLM Hunger Games** and lives under `hunger-games/`.
>
> Last synced with the code: **2026-09-03** (Week 2 closed: Day 13 leak-test +
> Day 14 invariant harness, both under `tests/`).

---

## 1. What this project is

### The research goal

The long-term point of this project is **behavioural analysis of LLMs**. We put
several LLMs into the same survival game, give each one a distinct personality,
and watch how they actually behave when they have to choose between cooperation
and violence.

Questions we want the game to help answer:

- Do some models consistently seek alliances while others play solo?
- Do models keep their word, or betray allies once it is convenient?
- How does personality (the system prompt) change a model's strategy?
- Which models are aggressive, which are avoidant, which are opportunistic?
- Are choices stable across seeds, or highly sensitive to small changes?

### The game

The environment is a simplified **Hunger Games**: tributes (agents) spawn at the
cornucopia, the map has four locations, and each turn every agent picks one
action. Agents can move, rest, search for food, hide, and — when they meet —
attack, flee, or ignore each other. Hunger rises every turn; an agent dies from
starvation or from losing fights. The match ends when one agent is left standing
(or the turn cap is hit, or everyone dies).

Planned social layer (not built yet): make/break alliances, form friendships or
rivalries, coordinate or betray.

### Current status (be honest about this)

The engine is a **deterministic toy simulation**. What exists:

- A roster of agents built from a name list (`balance.AGENT_NAMES`, currently
  `["Agent-A", "Agent-B"]`). The turn loop and rules are not hard-coded to 2 —
  3-agent smoke tests pass — but personalities/alliances don't exist yet.
- Agents choose actions **randomly** through a `Controller` object (seeded RNG).
  **There is no LLM in the loop yet.** `hunger-games/llm/` is an empty
  placeholder. The `Controller` is the seam an `LLMController` will plug into.
- A per-event **JSONL log** (`runs/game_data.jsonl`), envelope
  `{seq, turn, type, data}`, one fact per line. This log is the contract with a
  future visual client.
- Economy constants centralized in `config/balance.py`; the map is a data table
  in `engine/world.py`.

Recent work (2026-08): full event-log migration, a 21-item bug sweep (all
closed — see `hunger-games/BUG_CHECKLIST.md`), and a game-design rebalance so
matches aren't all "starve to death by turn 12". Combat now occasionally kills.

The "LLM" in the title is the destination, not the current state.

---

## 2. Repository layout

```
LLM-Colosseum/
├── DESIGN.md            # free-form roadmap notes (server/client split, creatures, intro cinematic)
├── DEVLOG.md            # day-by-day log of what was built
├── INFO.md              # this file
├── LICENSE              # MIT, © 2026 Metis
├── requirements.txt     # "stremlit" (typo for streamlit) — not needed to run the engine
└── hunger-games/
    ├── main.py                  # entry point: asks for a seed, runs turns until the match ends
    ├── README.md                # stub
    ├── BUG_CHECKLIST.md         # running list of bugs + fixes (21/21 closed)
    ├── EVENTS_GUIDE.md          # "Day 9" lesson: how to turn engine output into events
    ├── config/
    │   └── balance.py           # ALL tunable numbers: economy + value-function coefficients
    ├── engine/
    │   ├── world.py             # LOCATIONS table (food / danger / cover per room) + LOCATIONS_NAME
    │   ├── actions.py           # which actions are legal, target selection, legality check
    │   ├── item.py              # Item (frozen dataclass) + add_item / has_item / take_item
    │   └── game.py              # the turn loop, action execution, combat, event recording
    ├── agents/
    │   ├── agent.py             # Agent: stats + state, validate(), combat/flee/hide values
    │   ├── controller.py        # Controller: the decision seam (random today, LLM later)
    │   └── perception.py        # Observation + observe(game, agent): the view a controller reasons over
    ├── runs/
    │   └── game_data.jsonl      # per-event log, truncated + rewritten each run
    ├── llm/                     # (empty) future: model clients / prompting
    ├── analysis/                # (empty) future: post-match behavioural analysis
    ├── dashboard/               # (empty) future: streamlit or client-side viewer
    └── tests/                   # unittest suite (Week 2):
        ├── __init__.py             # empty — makes tests/ a package for discover
        ├── harness.py              # run_match, check_invariants, sweep, _check_* helpers
        ├── test_perception_leak.py # Day 13: to_prompt() leaks no numbers / hidden state
        └── test_integration.py     # Day 14: sweep + determinism + per-invariant tests
```

---

## 3. How to run

```
cd hunger-games
python3 main.py
```

- It prompts: `Give me the seed(default=0):` — enter an integer, or press Enter
  for seed `0`. A bad value re-prompts.
- Same seed ⇒ same match. **RNG call order is load-bearing**: a pure refactor
  must not add, remove, or reorder `rng` draws or the log changes.
- `main.py` truncates `runs/game_data.jsonl` at the start of every run, then
  appends one JSON object per line as events happen.
- When the loop ends it records a `RESULT` event: a winner, "no survivors left",
  or "turn limit reached, no winner".

Environment: Python 3.14, standard library only (`random`, `json`).

### Tests

```
cd hunger-games
python -m unittest discover -s tests -t .
```

Stdlib `unittest` (no `pytest`). 10 tests, ~0.6 s, all green. `harness.py` is
importable on its own for ad-hoc sweeps: `from tests.harness import sweep; sweep(1000)`.

---

## 4. Domain model (how the simulation works today)

### World (`engine/world.py`)

Four locations, fully connected (you can move from any one to any other). Each is
a row of three probabilities:

| location     | `food` | `danger` | `cover` |
|--------------|-------:|---------:|--------:|
| `cornucopia` |  0.35  |   0.70   |  0.10   |
| `river`      |  0.75  |   0.10   |  0.20   |
| `forest`     |  0.55  |   0.30   |  0.70   |
| `caves`      |  0.15  |   0.50   |  0.90   |

- `food` — SEARCH success chance in that room.
- `cover` — feeds HIDE success (see below).
- `danger` — **defined but not used yet** (future: ambient hazard / muttations).

`LOCATIONS_NAME = list(LOCATIONS)` preserves insertion order and is what
`rng.choice(...)` picks destinations from. All agents spawn at `cornucopia`.

### Agent (`agents/agent.py`)

Built from a name: `Agent(name, rng)`. The five stats are rolled in this fixed
order (matters for reproducibility): **strength, speed, max_stamina,
intelligence, stealth**.

| Field          | Initial value           | Notes |
|----------------|-------------------------|-------|
| `health`       | `MAX_HEALTH` (100)       | clamp ≤ 100; `≤ HEALTH_DEATH` (0) ⇒ dead |
| `hunger`       | `STARTING_HUNGER` (0)    | clamp ≥ 0; `+HUNGER_TICK` (5) every turn; `≥ HUNGER_DEATH` (100) ⇒ dead |
| `strength`     | random 25–100            | combat |
| `speed`        | random 25–100            | combat, fleeing |
| `max_stamina`  | random 25–100            | the stamina *capacity* (fixed) |
| `stamina`      | starts at `max_stamina`  | the *pool*; spent by actions; clamp to `[0, max_stamina]` |
| `intelligence` | random 25–100            | combat, fleeing, hiding |
| `stealth`      | random 25–100            | hiding |
| `position`     | `"cornucopia"`           | |
| `alive`        | `True`                   | |
| `hidden`       | `False`                  | set by a successful HIDE; makes the agent untargetable for a turn |
| `controller`   | `Controller(rng)`        | the decision-maker (see §4 "Controller") |
| `inventory`    | `[]`                     | list of `Item` (see §4 "Inventory"); starts empty |

`clamp()` bounds hunger/health/stamina — but **not symmetrically**: `hunger` is
floored at 0 only (no upper cap), `health` is capped at `MAX_HEALTH` only (no
lower floor), `stamina` is bounded both sides `[0, max_stamina]`. So on the turn
an agent dies, `hunger` can read > 100 and `health` can read < 0. Invariant
checks must only assert `hunger ≥ 0`, `health ≤ MAX_HEALTH` (accepted, not a bug —
see `BUG_CHECKLIST.md`). `validate()` clamps then decides death: `hunger ≥ 100` ⇒
`"Starved to death"`; else `health ≤ 0` ⇒ `"Died due to low health"`.

`is_exhausted()` ⇒ `stamina < max_stamina * EXHAUSTION_RATIO` (0.26). While
exhausted, every stamina cost is multiplied by `EXHAUSTION_MULTIPLIER` (1.6,
rounded).

### Controller (`agents/controller.py`)

The "brain", split out from `Agent` so it can be swapped:

```
Controller(rng).choose_action(legal_actions) -> one action string
```

Today it is `rng.choice(...)` — pure random. It receives an `Observation`
(§4 "Perception") and returns `(action, target_name)` — it picks the ATTACK/FLEE
target too. An `LLMController` will implement the same method and drop in without
touching `Agent` or `Game`.

### Actions

Solo actions (no other alive agent in the room):

| Action   | Effect |
|----------|--------|
| `REST`   | `health += 15 ± r`, `stamina += 15 ± r` (same `r ∈ [-5, 5]`), `hunger += 5–10`. Costs no stamina. Event carries the **real post-clamp deltas**. |
| `MOVE`   | move to a random *other* location, `stamina -= 12` |
| `SEARCH` | `rng.random() < LOCATIONS[pos]["food"]` ⇒ found: `hunger -= 35`; else: `hunger += 10`. Either way `stamina -= 10`. |

Encounter actions (another alive, non-hidden agent is in the room):

| Action   | Target? | Effect |
|----------|---------|--------|
| `ATTACK` | yes     | resolve a fight by `combat_value` (below). Gated: only offered if `hunger < 50` **and** `health > 50`. |
| `FLEE`   | yes     | `flee_value(self) > flee_value(target)` ⇒ move to a random other location; else stay. `stamina -= 20` either way (only the fleer pays). |
| `HIDE`   | **no**  | "hide from the room". Success ⇒ `hidden = True`. `stamina -= 8`. See below. |
| `IGNORE` | no      | do nothing on purpose |

`None` / no-action: recorded (as an `IGNORE` event) when an agent has literally
no legal action.

### Which actions are legal (`engine/actions.py`)

- Dead agent ⇒ `[]`.
- "Enemies" = other agents that are alive, in the same room, **and not
  `hidden`**. A hidden agent is invisible to everyone else for that turn.
- Enemy present ⇒ candidates `MOVE, HIDE, FLEE, IGNORE`, plus `ATTACK` iff
  `hunger < 50` and `health > 50`.
- Alone ⇒ candidates `MOVE, REST, SEARCH`.
- Then drop any candidate whose stamina cost exceeds current stamina. If nothing
  is left: `["IGNORE"]` with an enemy present, `["REST"]` when alone.
- The list is returned **sorted**.

`get_available_targets()` returns targets only for `ATTACK`/`FLEE` — other alive,
same-room, non-hidden agents, sorted by name.

`is_legal()` re-checks the chosen action and target against those lists before it
runs. An illegal choice raises `ValueError` (the guard that will catch a
misbehaving LLM later). `ATTACK`/`FLEE` must have a valid target; every other
action must have `target = None`.

### Combat, flee, hide values (`agents/agent.py`)

All coefficients live in `config/balance.py`.

```
combat_value = capacity * readiness * noise

  capacity  = strength·COMBAT_STRENGTH(.50)
            + speed·COMBAT_SPEED(.35)
            + intelligence·COMBAT_INTELLIGENCE(.15)          # weights sum to 1.0

  readiness = (health / MAX_HEALTH)
            * (1 - hunger / HUNGER_DEATH)
            * (stamina / max_stamina)                        # PRODUCT of three 0..1 factors

  noise     = rng.uniform(0.9, 1.1)                          # RANDOM_NOISE, multiplicative
```

- `readiness` is a **product**: one bad factor (starving, badly hurt, exhausted)
  collapses the fighter toward 0, regardless of raw stats.
- `noise` is a *factor near 1* — it can never zero the value or flip its sign.
- `_attack`: higher `combat_value` wins; a tie goes to the attacker `a`. Then
  `loser.health -= ATTACK_DAMAGE` (flat **50**), and **both** pay
  `stamina -= 20` (`_spend_stamina` for loser then winner). Damage does not scale
  with the gap yet — `combat_value` only picks the winner. Making the hit scale
  with the margin is a noted future lever.

```
flee_value = speed·FLEE_SPEED(.40) + stamina·FLEE_STAMINA(.40)
           + intelligence·FLEE_INTELLIGENCE(.20)
           + rng.randint(-10, 10)                            # RANDOM_ADD, additive

hide_value = stealth·HIDE_STEALTH(.40) + intelligence·HIDE_INTELLIGENCE(.40)
           + stamina·HIDE_STAMINA(.20)
           + rng.randint(-10, 10)                            # RANDOM_ADD, additive
```

`flee_value`/`hide_value` keep the old **additive** ±10 noise. Do not reuse
`RANDOM_NOISE` (the multiplicative one) here.

### HIDE resolution (`engine/game.py::_attempt_hide`)

HIDE is target-less. Success blends the room and the agent's skill:

```
skill  = clamp01( (hide_value() - MIN_HIDE_VALUE) / (MAX_HIDE_VALUE - MIN_HIDE_VALUE) )
         # MIN 10, MAX 110 — the true bounds of hide_value
         #   min: 25·.4 + 25·.4 + 0·.2 - 10   (stamina floor is 0, not 25)
         #   max: 100·.4 + 100·.4 + 100·.2 + 10
chance = (skill + LOCATIONS[pos]["cover"]) / 2               # equal weight, room and skill
hidden = rng.random() < chance
```

- Success ⇒ `agent.hidden = True`, event `HIDE success=True`.
- Failure ⇒ `agent.hidden = False`, event `HIDE success=True... spotted=True`.
  `spotted` is currently **log-only** — no mechanic reads it yet. The planned
  "batch 3" turns a failed HIDE into an `exposed` state that makes the next
  ATTACK against that agent an automatic loss.
- `hidden` clears the moment the agent takes a **loud** action
  (`MOVE / SEARCH / ATTACK / FLEE`) — to eat, you must break cover.
- Observed success rates (80-seed sweep): caves ~82%, forest ~53%,
  cornucopia ~38%, river ~33% — skill lifts the low-cover rooms and softens
  caves, exactly the "(skill + cover)/2" shape.

### Inventory (`engine/item.py`) — Day 10

`Item` is a **frozen dataclass** with exactly two fields: `kind`
(`"food" | "medicine" | "weapon"`) and `name` (flavour text, e.g. `"green herbs"`).
Frozen ⇒ immutable, hashable, value-equal. No weight / durability / rarity / slots.

Three module functions, all take the agent (RNG is never imported here):

- `add_item(agent, item)` — append to `agent.inventory`.
- `has_item(agent, kind)` — `any` item of that kind. (Unused until Day 11.)
- `take_item(agent, kind)` — find the **first** item of that kind, remove it,
  return it (or `None`). Find + remove + return in one call, so an item can't be
  used without being consumed.

**Discovery:** in `game.py`, SEARCH branch, only when food was found, *after* the
`SEARCH` event: `rng.random() < DROP_RATE` (0.35) ⇒ pick a row from
`balance.LOOT_TABLE` (`(kind, name, weight)` tuples) via `rng.choices`, build the
`Item`, `add_item`, record `ITEM_DROP`. This adds RNG draws ⇒ the JSONL log
diverges from the pre-Day-10 baseline by design.

**Loss:** in `_resolve`, on the alive→dead transition, `DEATH` is always recorded
first; then if `inventory` is non-empty, record `ITEMS_LOST` (`items` = list of
`{kind, name}`) and clear the list.

Effect logic (healing, weapon bonus) lives in the engine, never on `Item`.

### Weapons (`engine/item.py` + `combat_value`) — Day 12

`balance.WEAPON_MODIFIERS` maps a weapon `name` to a flat combat bonus:
`rusted knife` 8, `sharpened spear` 14, `old katana` 12 (all three already in
`LOOT_TABLE`).

- `weapon_modifier(agent) -> int` — the **max** modifier among the agent's
  weapons, `0` if none. Never a sum: carrying three weapons gives you the best
  one's bonus, not the total.
- `best_weapon(agent) -> str | None` — the `name` of that best weapon, for the
  log only.

`Agent.combat_value` gets one **additive** term at the end:
`capacity * readiness * noise + weapon_modifier(self)`. Flat, not a percentage;
it does not touch `readiness` or `noise`. Damage stays flat `ATTACK_DAMAGE` 50 —
the weapon only tilts *who wins*.

`game.py._attack` imports `best_weapon` and adds `winner_weapon` / `loser_weapon`
(name or `null`) to the `ATTACK` event.

Day 12 adds **no** RNG draws (`weapon_modifier` / `best_weapon` never touch
`rng`), so combat stays byte-identical for a given pre-weapon state; the log only
diverges because of Days 10–11. Balance note: with stats equalised the additive
term almost always beats the ±10% noise band (knife 0.93 / spear 1.00 win rate in
a 2000-roll test) — magnitude is a future balance lever, not a V1 blocker.

### Perception (`agents/perception.py`) — Day 13

`observe(game, agent) -> Observation` — a read-only, RNG-free snapshot of what one
agent can see. Fields:

- `name`, `position`, `turn`
- `health` / `hunger` / `stamina` — **qualitative phrases, not numbers**, from
  `health_phrase` / `hunger_phrase` / `stamina_phrase` (4–5 bands each; stamina
  buckets on the ratio `stamina / max_stamina`).
- `exhausted` — bool (kept; not a number).
- `room` — a phrase from `locations_phrase(position)` describing `cover` + `food`
  qualitatively (`danger` is deliberately left out — it has no mechanic yet).
- `others` — `describe_other(agent, other)` strings for each visible agent:
  coarser than self (3 health bands), no hunger, a weapon shows only as
  "clutching something you can't make out". Never their exact stats, item names,
  personality, or memory.
- `inventory` — **your own** item names (precise — they are yours).
- `legal_actions`, `legal_targets` — unchanged machine-readable lists/names; the
  `RandomController` still reads these directly.

`Observation.to_prompt()` renders the phrases into the exact text an LLM
controller will receive — no raw integers, `turn` is kept out of the text so a
`\d` regex leak-test can be strict.

`Observation` is a plain class (a box). `observe()` is the wall: the controller
gets the box, never `game`, so it cannot read hidden state.

**Verified:** 6-seed run stays byte-identical to baseline (no RNG touched);
`to_prompt()` contains no digit and none of the agent's real stat values; another
agent's health number / weapon name never appear in the observer's prompt.
**Leak-test (Day 14 session, 2026-09-03):** `tests/test_perception_leak.py` —
4 tests. `test_perception_leak` (8 seeds × 10 turns, `assertNotRegex(text, r"\d")`),
`test_no_raw_text` (no stat value as a substring), `test_secret` (place two agents
in one room + give the other a weapon → its name / health / strength never leak;
your own food name *does* show), `test_obs` (legal action/target lists non-empty).

### Turn loop (`engine/game.py::run_turn`)

`turn += 1`, then for each **alive** agent, in roster order:

1. `choose_action(agent)` — `observe()` the world, hand the `Observation` to the
   controller, get `(action, target_name)` back, verify with `is_legal()`,
   execute it immediately.
2. `hunger += HUNGER_TICK` (5), record a `HUNGER_TICK` event.
3. `_resolve(agent)` — `validate()`; on an alive→dead transition, record `DEATH`.

`main.py` loops `while (agents alive) > 1 and turn < MAX_TURNS` (200).

---

## 5. Event log / JSONL contract

See `hunger-games/EVENTS_GUIDE.md` for the full reasoning ("Day 9" lesson).

### Core principle

> The engine never describes what happened by printing a sentence. It records a
> small **fact** (an event). Sentences are generated afterwards, from the facts.

The future client (§6) shares no memory with the engine, so the event log **is
the API** between them. A missing or vague event = something the client cannot
draw.

### The envelope

```jsonc
{
  "seq": 12,      // +1 for every event in the whole match; global, never resets
  "turn": 3,      // which turn; NOT unique — many events share a turn
  "type": "ATTACK",
  "data": { ... } // payload; differs per event type. Plain values only:
                  // strings, numbers, booleans, null. NEVER an Agent object.
}
```

Reading the file top-to-bottom replays the match in exact order. One line = one
thing that happened, not "everything about turn 3". Derive "what happened in
turn N" by *filtering* (`Game.event_per_turn(n)`), never by keeping a second copy.

### Event types emitted by `game.py::record(...)`

| type          | key fields in `data` |
|---------------|----------------------|
| `SEED`        | `seed` |
| `HUNGER_TICK` | `agent`, `delta`, `new_value` |
| `REST`        | `agent`, `health_delta`, `hunger_delta`, `stamina_delta` (real, post-clamp) |
| `MOVE`        | `agent`, `from_`, `to`, `stamina_delta` |
| `SEARCH`      | `agent`, `found_food`, `hunger_delta`, `stamina_delta` |
| `ITEM_DROP`   | `agent`, `kind`, `name`, `inventory_size` — after a successful SEARCH, `rng` < `DROP_RATE` (event key is `ITEM_DROP`, singular, in code) |
| `ITEMS_LOST`  | `agent`, `items` (list of `{kind, name}`) — on death, if the agent carried anything |
| `ITEM_USED`   | `agent`, `ok`; on success also `health_before`, `health_after`, `wasted`, `stamina_delta`; on the (LLM-era) miss `ok=False`, `reason` |
| `ATTACK`      | `actor`, `target`, `winner`, `loser`, `damage`, `location`, `stamina_delta_loser`, `stamina_delta_winner`, `winner_weapon`, `loser_weapon` (name or `null`) |
| `FLEE`        | `actor`, `target`, `success`, `location`, `escaped_to`, `stamina_delta_agent` |
| `HIDE`        | `actor`, `success`, `location`, `stamina_delta_agent`, (`spotted` on failure) — **no `target`** |
| `IGNORE`      | `agent`, `reason` |
| `DEATH`       | `agent`, `cause` — recorded once, only on the alive→dead transition |
| `RESULT`      | `result` (winner sentence / "no survivors left" / "turn limit reached, no winner") |

The old per-turn-snapshot format and the parallel `self.data` / `convert_jsonl`
structures were removed during the migration. `record()` + `_append_to_jsonl()`
is the only writer; `self.events` is the only in-memory copy.

---

## 6. Architecture direction

### Target layers

| Layer | Responsibility | Where it is today |
|-------|----------------|-------------------|
| **State** | data only (`Agent`, world table) | mostly there; `Agent` still hosts the value functions |
| **Rules** | pure functions: legality, value scores | `actions.py` + the `*_value()` methods |
| **Engine** (`Game`) | turn loop; the *only* thing that mutates state and records events | there |
| **Controller** | `choose_action(obs) -> (action, target)` — random / utility / LLM, swappable | `controller.py`, done |
| **Perception** | `observe(game, agent) -> Observation` — the structured view a controller reasons over | `perception.py`, done |
| **Events** | envelope, recorder, jsonl writer, replay reader, renderer | recorder + writer done; reader/renderer are the client's job |

### Server / client split (from `DESIGN.md`)

- **Server = the engine.** Pure Python. Emits a JSONL event stream. Owns all
  rules and randomness.
- **Client = a separate program** (Godot is the current idea). Reads the JSONL,
  renders the map / tributes / fights / deaths. Owns nothing about the rules.
- The JSONL event log (§5) is the **only** interface between them.

### Future ideas (from `DESIGN.md`, not scheduled)

- **Human vs LLM**: a person plays a tribute against the models.
- **Creatures**: witcher, mage, muttations roaming the map (the `danger` column).
- **Intro cinematic** on the client: tributes arriving at the cornucopia with a
  narrator voice-over.

---

## 7. Timeline (`DEVLOG.md` has the detail)

| Phase | What was done |
|-------|---------------|
| Days 1–4 | Simplest engine: agents, validation, death by hunger/health, per-action effects, encounters (attack / flee / ignore) |
| Day 5 | Combat formula + light randomness; `match`/`case` refactor; run until one stands |
| Day 6 | Seeded RNG ⇒ reproducible matches |
| Day 7 | Export the match to JSON, then JSONL |
| Day 9 (guide) | `EVENTS_GUIDE.md`: plan to record per-event facts |
| Days 8+ | Event-log migration (single per-event log, old structures deleted); 21-bug sweep (all closed) |
| Redesign (2026-08) | `balance.py`, `world.py` table, SEARCH-by-`food`, agent roster, `Controller` seam, `Perception` seam, HIDE mechanic, `combat_value` rework |
| Day 10 (2026-08-31) | Tiny inventory: `engine/item.py` (`Item` + add/has/take), `Agent.inventory`, `LOOT_TABLE`, `ITEM_DROP` on SEARCH, `ITEMS_LOST` on death |
| Day 11 (2026-08-31) | Medicine: `USE_ITEM` action (offered iff `has_item(agent,"medicine")`), `game._use_medicine` (consume → heal `MEDICINE_HEAL` 40 → clamp), `ITEM_USED` event with `wasted` flag |
| Day 12 (2026-09-01) | Weapons: `WEAPON_MODIFIERS`, `weapon_modifier` (best, never summed) + `best_weapon`, additive term in `combat_value`, `winner_weapon`/`loser_weapon` in `ATTACK`. Baseline regenerated → 44/52/37/21/52/64 |
| Day 13 (2026-09-01) | Perception proper: `*_phrase` buckets, `describe_other` (vaguer), `locations_phrase`, `Observation` now carries phrases + `turn` + own `inventory` + `to_prompt()`. Mechanics done; leak-test deferred to Day 14 session |
| Day 14 (2026-09-03) | Test session, closes Week 2. `tests/` package: `harness.py` (`run_match`, 6 `_check_*` invariant helpers, `check_invariants` = concat of all 6, `sweep(n)` wrapping crashes as `"CRASH: ..."`), `test_perception_leak.py` (Day 13 debt, 4 tests), `test_integration.py` (6 tests: `sweep(500)`, determinism `run_match(0)==run_match(0)`, per-invariant, meta-test that a corrupted event *is* caught). **sweep(1000) = 0 broken seeds** → no regression file needed. Found: `clamp()` is not bilateral (documented, accepted) |

### The redesign, step by step (teach-only plan)

1. ✅ `config/balance.py` — economy constants centralized
2. ✅ `world.py` → `LOCATIONS` table + `LOCATIONS_NAME`
3. ✅ SEARCH success = `rng.random() < LOCATIONS[pos]["food"]`
4. ✅ roster: `Game(rng, seed, log_path, names)` from `balance.AGENT_NAMES`
5. ✅ Controller seam (`agents/controller.py`)
6. ✅ Perception seam (`agents/perception.py`) — `observe(game, agent) ->
   Observation`; controller now returns `(action, target)`
7. ⬜ ActionSpec registry — `{cost, needs_target, can(), apply() -> events}`
8. ⬜ extract a Recorder from `Game`

Also done outside the numbered list: `combat_value` = `capacity * readiness *
noise`; value-function coefficients moved to `balance.py` ("1b"); HIDE redesign
(Bug 14 + 18).

### Week 2 of the plan website (Days 8–14) — ✅ CLOSED (2026-09-03)

All of Days 8–14 done. Day 13 mechanics + its leak-test file, Day 14 invariant
sweep (`run_match(seed)`, `check_invariants` returning *all* violations,
`sweep(500)` under the turn cap). `sweep(1000)` came back clean so no
per-failing-seed regression file was needed. Next up is passo 7 (ActionSpec
registry) — internal, optional, not part of Week 2.

---

## 8. Roadmap (rough, in likely order)

1. ✅ Finish the event-log migration.
2. ✅ Fix the known engine bugs (21/21 in `BUG_CHECKLIST.md`).
3. 🟡 Generalize to N agents — roster is in; personalities are not.
4. Finish the architecture seams (Perception, ActionSpec, Recorder).
5. **Add personalities** — a description / prompt per agent.
6. **Plug in LLMs** — `llm/` module + an `LLMController`: give a model the legal
   actions + its `Observation`, get a choice, validate with `is_legal()`.
7. **Social layer** — alliances, friendship/rivalry, betrayal, messaging.
8. **Client** — Godot (or similar) reads the JSONL and renders the match.
9. **Analysis** — `analysis/` aggregates many matches into per-model profiles.
10. Later: human vs LLM, creatures, intro cinematic.

---

## 9. Open items / backlog

> `BUG_CHECKLIST.md` has the closed bugs (1–21). These are the live threads.

**Design / balance**

- Combat damage is flat `ATTACK_DAMAGE = 50` — `combat_value` only picks the
  winner. Consider scaling the hit with the `combat_value` margin.
- `danger` (per-room) is defined but unused.
- HIDE `spotted` is log-only. Planned "batch 3": failed HIDE ⇒ `exposed` ⇒ the
  next ATTACK against that agent skips the `combat_value` roll (attacker
  auto-wins) — the mirror of a successful hide.

**Contract / cleanup**

- Name convention for the LLM era (Bug 8b): the controller now returns a target
  **name** (string), but `is_legal` still wants an `Agent` object, so
  `Game.choose_action` resolves name→object just for that call. `is_legal` /
  `execute_actions` should be made string-native end to end.
- `agents/agent.py` still hosts `combat_value` / `flee_value` / `hide_value` —
  arguably Rules, not State.

**Minor**

- No dedicated `tests/` for inventory / medicine / weapons as *units* — but the
  Day 14 `_check_items` invariant (entered = remaining + used + lost) covers item
  conservation across a 500-seed sweep, so this is largely retired.
- Event key naming settled: code emits `ITEM_DROP` (singular). `ITEM_DROP` and
  `ITEMS_LOST` both use `agent=` in `data`. Older prose saying `ITEMS_DROP` /
  `actor=` is stale — this file is now the reference.
- Baseline regenerated 2026-09-01 after Days 10–12: seeds 0,1,2,3,5,7 =
  44/52/37/21/52/64 (was 59/47/52/21/52/83).
- `requirements.txt`: `stremlit` → `streamlit`.
- Spelling in code comments/strings: `avalible` (mostly fixed), "choses",
  `from_` trailing underscore is deliberate (avoids the `from` keyword).

---

## 10. Working rules for this project

**No AI-written code.** When asking for help:

- No AI generating code, no copy-paste of code snippets, no "here, paste this" —
  not even one line.
- The owner types every line themselves, to actually learn it.
- Assistance is limited to: explaining concepts, reviewing existing code,
  pointing at bugs and their cause, discussing design trade-offs, writing docs
  like this one, and laying out step-by-step *plans* the owner then implements.
- Schema-level pseudo-code (clearly marked "not to paste") is the ceiling.
- `EVENTS_GUIDE.md` is the model for the kind of help wanted: a lesson with
  illustrative (not paste-ready) examples, focused on *why*.

---

## 11. Glossary

| Term | Meaning |
|------|---------|
| **Tribute / agent** | one participant in the match |
| **Cornucopia** | starting location; the central spot from the source material |
| **Encounter** | two or more alive, non-hidden agents in the same location on the same turn |
| **Event** | one recorded fact, one line of JSONL |
| **Envelope** | the four fields every event shares: `seq`, `turn`, `type`, `data` |
| **`seq`** | global monotonically increasing event counter; defines total order |
| **Seed** | integer fed to `random.Random`; fixes the whole match's randomness |
| **Controller** | the object that turns "legal actions" into a choice (random today, LLM later) |
| **Perception** | (planned) the structured view of the state a controller reasons over |
| **capacity / readiness** | the two factors of `combat_value`: raw fighting stats × current condition |
| **`hidden`** | agent state set by a successful HIDE; makes the agent untargetable until it acts loudly |
| **`spotted`** | log field on a failed HIDE; no mechanic yet |
| **Server / engine** | the Python simulation; owns rules and RNG; emits events |
| **Client** | a separate future program that reads events and renders visuals |
