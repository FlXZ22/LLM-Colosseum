# Day 9 — Turning Game Output into Events

Read this like a lesson, not a spec. The code snippets are **teaching examples** —
type your own version with your own names, don't paste them in. The goal is that
you understand *why* each step exists, not that you end up with my exact code.

## 1. The one-sentence idea

> Nothing in the engine is allowed to describe what happened by printing a
> sentence. It describes what happened by recording a small fact. Sentences
> are generated afterwards, from the facts.

Everything else in this guide is just applying that sentence to your codebase.

## 2. Why this matters for *this* project specifically

Look at `DESIGN.md`: the long-term plan is an engine ("server") that produces a
JSONL stream, consumed by a separate client (Godot or similar) for visuals.
That means the event log isn't a debugging nicety — it's the **API contract**
between two programs that don't share memory. If an event is missing or vague,
the client literally cannot render it, no matter how good your print statements
were. This is the reason "no print-only facts" is a hard rule, not a style
preference.

## 3. What you already have, and what's missing

You already write to `game_data.jsonl` once per turn (`game.py:151-154`). Good
habit, wrong unit. Right now one line = "everything about turn 3." We want one
line = "one thing that happened," and turn 3 might produce five or six such
lines.

Concretely, today these facts only exist as `print()` calls and are lost the
moment the game ends:
- `agent.py:25/28` — death by starvation vs. death by health, and *why*
- `game.py:116/119` — an agent ignoring, or having no action at all
- REST, MOVE, SEARCH never produce any record beyond the end-of-turn stat snapshot
- the hunger tick every agent gets every turn (`game.py:31`)

Those all need to become real events before anything else does.

## 4. The event shape (the envelope)

Every event, no matter its type, should carry the same three "envelope"
fields, plus a type-specific payload:

```python
# illustrative shape, not literal code to paste
{
    "seq": 12,          # increases by 1 for every event in the whole match
    "turn": 3,           # which turn it happened in
    "type": "ATTACK",    # a short constant string
    "data": { ... }       # only this part differs per event type
}
```

Two design choices worth understanding, not just copying:

- **`seq` is global, `turn` is not.** Two events can share a `turn` (a REST and
  an ATTACK both happen in turn 3). Only `seq` tells you which one came
  first. Without it, "reading the log in order tells the same story as the
  match" isn't actually true.
- **`data` only ever holds plain, serializable values** — strings, numbers,
  booleans, `None`. Never put an `Agent` object in there. Put `agent.name`.
  If you put the object in, `json.dumps` will crash the first time you try to
  write it, and even if it didn't, the client on the other side of that
  server/client boundary has no idea what a Python object is.

## 5. Step-by-step

### Step 0 — Decide where events live

Add one place on `Game` to hold the match history in memory, e.g. a plain
list you append to. This *replaces* `self.data["turns"]` — don't keep both,
you'll end up maintaining two versions of the truth again, which is the exact
bug you're fixing.

### Step 1 — One recording method

Write a single method, something like `record(self, type, **fields)`, that:
1. builds the envelope (`seq`, `turn`, `type`, `data=fields`),
2. appends it to the in-memory list,
3. writes that one dict as one jsonl line (reuse the append-to-file idea from
   your current `convert_jsonl`, just call it per-event instead of per-turn).

This is the *only* place that touches the jsonl file. If you ever want to add
a database later, or send events over a socket to the Godot client, this is
the one method you'd change.

```python
# illustrative — write your own version
def record(self, type_, **data):
    self._seq += 1
    event = {"seq": self._seq, "turn": self.turn, "type": type_, "data": data}
    self.events.append(event)
    self._append_to_jsonl(event)
    return event
```

### Step 2 — Convert ATTACK first

Pick the most complex branch (`_attack`) and convert it end to end, so you
learn the pattern once on the hardest case:

- Replace `print(f"{a.name} vs {b.name}")` and `print(f"{winner.name} wins")`
  with one call: `self.record("ATTACK", actor=a.name, target=b.name, winner=winner.name, loser=loser.name, damage=50, location=winner.position)`.
- Delete `encounter_data` / `turn_encounters` for this action — the event
  *is* the encounter record now, you don't need a second structure describing
  the same fight.
- Write a tiny separate function, e.g. `render(event) -> str`, with one
  branch per `type`, that turns this dict back into `"Agent-A hit Agent-B for
  50 (cornucopia)"`. Call `print(render(event))` right after `record(...)`
  returns it, so the terminal output looks the same as before — but now it's
  generated *from* the fact, not typed by hand at the call site.

Run a match. Confirm the printed line still reads sensibly and the jsonl now
has an `ATTACK`-typed line matching it.

### Step 3 — Do the same for FLEE and HIDE

Same pattern, different payload:
- `FLEE`: `actor`, `target`, `success`, `escaped_to` (only meaningful when
  `success` is true), `location`.
- `HIDE`: `actor`, `target`, `success`, `location`.

You can delete `encounter_data` entirely once these three are converted — it
existed only to build the old encounter shape.

### Step 4 — The "boring" actions: REST, MOVE, SEARCH

These currently only affect state silently (`game.py:87-108`) with no
print and no record at all. Add one `record(...)` call at the end of each
branch, capturing the deltas you just applied:

- `REST`: `agent`, `health_delta`, `hunger_delta`, `stamina_delta`
- `MOVE`: `agent`, `from_`, `to`
- `SEARCH`: `agent`, `found_food` (bool), `hunger_delta`, `stamina_delta`

Tip: compute the delta *before* mutating, or capture the before-value and
subtract after — either works, just be consistent, because "delta" is a fact
about the event, not something you want the reader to recompute from two
separate snapshots.

### Step 5 — IGNORE and "no action available"

Right now these are two different situations (`game.py:116` vs `119`)
printed almost identically. Make them two different `reason` values on one
`IGNORE` event, or two distinct event types (`IGNORE` vs `NO_ACTION`) — your
call, but pick one and be consistent, because a future reader (or the Godot
client) needs to distinguish "agent chose to do nothing" from "agent had
nothing it could do."

### Step 6 — Hunger tick and death

- The `agent.hunger += 5` in `game.py:31` happens to every agent, every turn,
  unconditionally. Record it as its own event (`HUNGER_TICK`, agent, delta,
  new_value) right after it's applied — this is the kind of fact that's
  trivial to forget precisely because it isn't tied to a player decision.
- `agent.validate()` (`agent.py:18-28`) is where death actually gets decided.
  This method lives on `Agent`, which doesn't have a `record()` method — so
  either give `validate()` a way to report back "this agent just died, here's
  why" to the caller (return value, or a small callback), or move the
  recording call into `Game` right after it calls `agent.validate()`, using
  `agent.alive` before/after to detect the transition. Either is fine; the
  wrong move is duplicating death-detection logic in two places.

### Step 7 — Delete the old parallel structures

Once every action type above records an event:
- delete `self.data`, `turn_data`, `convert_jsonl` in their old per-turn form,
- delete `encounter_data` / `turn_encounters`,
- `main.py:14`'s `open("game_data.jsonl", "w").close()` still makes sense —
  keep truncating the file at the start of a run.

If you want "what happened in turn N" for a summary print, get it by
filtering: `[e for e in self.events if e["turn"] == n]` — a query over the
log, not a second thing you maintain by hand.

### Step 8 — Verify against the brief's checklist

Go through the "Evidence that it works" list literally:
- Pick any one jsonl line at random, cover up every other line, and check you
  can still explain what it means. If you need the line before or after it to
  make sense, the event is missing a field.
- Grep your own `game.py`/`agent.py` for the word `print`. Every remaining
  hit should be inside your renderer function, never inside `execute_actions`,
  `_attack`, `_atemptflee`, `_atempthide`, or `validate()`.
- Replay the printed transcript in order and the jsonl in order side by side
  for one seeded run — they should tell the identical story, not two slightly
  different ones like today.

## 6. Common mistakes worth knowing before you hit them

- **Don't put live objects in `data`.** Only `agent.name` / `target.name`,
  never the `Agent` instance — it won't serialize, and it's meaningless to
  anything reading the log later without the exact same Python process.
- **Don't reset `seq` per turn.** If you do, you lose the ability to tell
  which of two same-turn events happened first.
- **Resist adding fields "just in case."** The brief explicitly says the
  shape should be able to *accept* future item/social events without
  pretending they exist now — that means don't add an empty `item: null` to
  every event today. Add new event *types* later; don't pad existing ones.
- **The renderer must not mutate anything.** If turning an event into a
  sentence changes agent state, you've put logic in the wrong place — it
  belongs in `execute_actions`, and the renderer only reads.

## 7. Suggested order to actually do the work in

1. Envelope + `record()` method, wired to file, no callers yet.
2. Convert `ATTACK` (hardest case, proves the pattern).
3. Convert `FLEE`, `HIDE`.
4. Convert `REST`, `MOVE`, `SEARCH`.
5. Convert `IGNORE` / no-action.
6. Convert hunger tick + death.
7. Delete the old per-turn structures.
8. Run the verification checklist in section 5, Step 8.

Budget: this matches the "2-3h, medium" estimate on the task — steps 2-6 are
the same fifteen-minute pattern repeated six times once you've done it once
for ATTACK.
