import subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


# this is a test file wrote by claude for testing

ROOT = Path(__file__).resolve().parent.parent
SEEDS = range(20)
PAIRS = [(1, 1), (2, 2), (3, 3)]


def run(job):
    p1, p2, seed = job
    out = f"runs/llm_full/{p1}_{p2}_{seed}_1_1.jsonl"
    r = subprocess.run(
        [sys.executable, "main.py", "-s", str(seed), "-p", str(p1), str(p2), "-m", "1", "1", "-o", out],
        cwd=ROOT, capture_output=True, text=True,
    )
    print(out, "rc", r.returncode, r.stderr[-200:], flush=True)


jobs = [(p1, p2, s) for p1, p2 in PAIRS for s in SEEDS]
with ThreadPoolExecutor(5) as ex:
    list(ex.map(run, jobs))
