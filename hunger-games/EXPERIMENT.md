# Experiment: does personality change LLM behaviour?

I want to test weather a personality is going to affect the decition of an LLM, and we are going to write some previews on what is the most probable llm move.

## 1. Setup
- **Question:** same LLM, same intelligence (75), only the personality changes. Does behaviour change?
- **Opponent:** both agents have the same personality (pairs 1-1, 2-2, 3-3).
- **Seeds:** 0 to 19 (20 seeds), the same for every profile.
- **Brain:** LLM for both agents (`-m 1 1`).

## 2. Metrics
Every rate is counted only over the turns where the action was offered. No offered turns means "no data", not 0.

| Metric | Meaning |
|---|---|
| attack rate | ATTACK chosen / turns where ATTACK was offered |
| flee rate | FLEE chosen / turns where FLEE was offered |
| hide rate | HIDE chosen / turns where HIDE was offered |
| search rate | SEARCH chosen / turns where SEARCH was offered |
| first encounter | the action chosen the first time ATTACK was offered |

## 3. Predictions

| Metric | Aggressor | Survivalist | Diplomat |
|---|---|---|---|
| attack | ~80% | <10% | <15% |
| flee | ~0% | 70-80% | low (<20%) |
| hide | ~0% | 70-80% | low (<20%) |
| search | medium | high | high |
| first encounter | ATTACK | HIDE or FLEE | IGNORE / talk, no attack |

Diplomat is less hide than survivalist that tries to hide and not engage and get in safe.

## 4. What counts as failure
Personality does **not** work if:
- the attack rates of the three profiles are within 10 points of each other, or
- the survivalist and the diplomat look the same (hide rate within 10 points).

Personality **works** if the aggressor attacks at least twice as much as the other two, and the survivalist hides clearly more than the diplomat.

## 5. Known limits
- Intelligence is fixed at 75 on purpose, so the aggressor and the survivalist are equally smart. This is a limit, not a bug.
- One model, one prompt version, same-personality pairs only.



