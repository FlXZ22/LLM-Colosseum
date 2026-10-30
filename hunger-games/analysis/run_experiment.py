import subprocess, sys
from pathlib import Path

seeds = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 ,12, 13, 14, 15, 16, 17, 18, 19]
profiles = [[1,1], [1,2], [1,3], [2,1], [2,2], [2,3], [3,1], [3,2], [3,3]]
modes = [[0, 0]]

ROOT = Path(__file__).resolve().parent.parent

for p1, p2 in profiles:
    for seed in seeds:
        for m1, m2 in modes:
            subprocess.run(
                [sys.executable, "main.py", "-s", str(seed), "-p", str(p1), str(p2), "-m", str(m1), str(m2), "-o", f"runs/{p1}_{p2}_{seed}_{m1}_{m2}_game_data.jsonl"],
                cwd=ROOT,
                check=True,
            )

    


