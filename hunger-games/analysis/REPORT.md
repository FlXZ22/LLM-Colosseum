# Does personality change behaviour? Pilot report (Day 20)

**Short answer: yes, in the pilot it does, strongly for the aggressor, but the sample is too small to call it proven.**

## What was run
- **Control (free):** the full random-brain run, 9 profile pairs x 20 seeds = 180 matches (`runs/*_0_0_*.jsonl`).
- **Pilot (LLM, paid):** 3 same-personality pairs (1-1, 2-2, 3-3) x 5 seeds (0-4) = 15 matches, both agents on the LLM (`runs/llm_pilot/`), run by `analysis/run_llm_pilot.py`.
- **Counting:** `analysis/metrics.py`. Rates are counted only over decisions where the action was offered. A zero denominator is shown as `n/a`.
- No predictions were committed before this run, so it is a **pilot**, not the official experiment.

## Control: the pipeline is clean
With random brains, Rocky, Flint and Mike get exactly the same numbers (attack 16.9%, flee 16.7%, hide 25.4%, search 41.9%). The profile never touches the game's random number generator, so the same seed gives the same game. That is the null result we want: any difference seen with the LLM comes from the personality prompt, not from the engine.

## LLM pilot (5 matches per profile, so 10 agents each)
| Profile | attack | flee | hide | search | first action when ATTACK first offered |
|---|---|---|---|---|---|
| Rocky (aggressor) | 100% (8/8) | 0% | 9% | 100% | ATTACK x8 |
| Flint (survivalist) | 0% (0/31) | 10% | 91% | 83% | HIDE x6, FLEE x3, MOVE x1 |
| Mike (diplomat) | 0% (0/12) | 0% | 0% (0/12) | 99% | IGNORE x6, MOVE x2 |

Fallback to random was 0% for all three: every action in the pilot came from the LLM, not from the error path.

## Reading
- **Aggressor vs the rest:** Rocky attacks every time it can, the others never do. This is the clearest result and matches the intended personality.
- **Survivalist vs diplomat:** both avoid attacking, but Flint hides and flees (91% hide when offered), while Mike never hides and mostly searches or ignores. The difference is in the expected direction.
- Two or more metrics differ in the predicted direction (attack, hide), so the "done when" bar is met for the pilot.

## Caveats (read before trusting it)
1. **Small sample.** 5 seeds per profile. The numbers are a first look, not evidence.
2. **Aggressor matches are short.** Rocky vs Rocky usually ends on turn 1 (one attack kills). So its search rate and later behaviour rest on few turns, and the 8/8 attack figure is partly an effect of the match ending right after.
3. **Same-personality pairs only.** Rocky always met Rocky. In a mixed pair, behaviour may change; this pilot does not test that.
4. **Actions vs reasons.** Only actions were counted. The issue notes that reasons and actions sometimes disagree.
5. **Single model** (`xiaomi/mimo-v2.6-pro`), one prompt version.

## Next step
Write the predictions and the opponent choice in a decision record, commit them, then run the full set (20 seeds) in the same way. If the pattern holds, the result stands; if it fades with more seeds, report it as a null result.
