"""Count behaviour metrics per personality from JSONL logs.
Usage: python analysis/metrics.py <glob> [...]
Rates only over decisions where the action was offered; no denominator -> 'n/a'."""
import glob, json, sys
from collections import defaultdict


# this is a test file wrote by claude for testing

ACTIONS = ["ATTACK", "FLEE", "HIDE", "SEARCH", "USE_ITEM"]


def load(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def collect(paths):
    st = defaultdict(lambda: defaultdict(int))
    first = defaultdict(lambda: defaultdict(int))
    matches = defaultdict(int)
    for p in paths:
        ev = load(p)
        prof = next(e for e in ev if e["type"] == "PROFILES")["data"]["profiles"]
        seen = set()
        for e in ev:
            if e["type"] != "LLM":
                continue
            d = e["data"]
            who = prof[d["agent"]]
            s = st[who]
            s["decisions"] += 1
            s["fallback"] += bool(d["is_random"])
            for a in ACTIONS:
                if a in d["available_actions"]:
                    s[a + "_offered"] += 1
                    s[a + "_taken"] += d["action"] == a
            if "ATTACK" in d["available_actions"] and (d["agent"], p) not in seen:
                seen.add((d["agent"], p))
                first[who][d["action"]] += 1
        for who in set(prof.values()):
            matches[who] += 1
    return st, first, matches


def rate(s, a):
    o = s[a + "_offered"]
    return f"{100 * s[a + '_taken'] / o:5.1f}% ({s[a + '_taken']}/{o})" if o else "n/a"


def report(label, paths):
    st, first, matches = collect(paths)
    print(f"\n## {label}  ({len(paths)} matches)")
    print("profile | " + " | ".join(a.lower() for a in ACTIONS) + " | fallback")
    for who in sorted(st):
        s = st[who]
        fb = f"{100 * s['fallback'] / s['decisions']:.0f}%" if s["decisions"] else "n/a"
        print(who, "|", " | ".join(rate(s, a) for a in ACTIONS), "|", fb)
    print("first action when ATTACK was first offered:")
    for who in sorted(first):
        print(" ", who, dict(first[who]))


if __name__ == "__main__":
    for pat in sys.argv[1:]:
        report(pat, sorted(glob.glob(pat)))
