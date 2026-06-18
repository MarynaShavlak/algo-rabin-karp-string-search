# Quick start

[🇺🇦 Українська](USAGE.md)  ·  **🇬🇧 English**

> Part of the documentation for the project [«The Rabin-Karp Algorithm (hashing): a step-by-step walkthrough»](README.en.md). Here are the commands to install, run the examples and the tests. For the repository structure see [PROJECT_STRUCTURE.en.md](PROJECT_STRUCTURE.en.md).

> **Python ≥ 3.8 required.** The code uses `from __future__ import annotations`, so it works on 3.8+ (developed and tested on 3.12).

```bash
# 1. Dependencies
pip install -r requirements.txt
# or install the package in development mode:
pip install -e .
# (optional) MP4 video for the animations without root — adds ffmpeg from imageio-ffmpeg:
pip install -e ".[video]"

# 2. Reproduce all figures and console outputs (in English → docs/images/en/)
python examples/00_intuition.py en            # intuition: string → hash; the sliding-window idea
python examples/01_polynomial_hash.py en      # PHASE 1: polynomial hash (abc→6382179→90; 35, 82)
python examples/02_search.py en               # PHASE 2: synopsis example «developer» → 8
python examples/03_rolling_collisions.py en   # rolling vs recompute; COLLISIONS; modular arithmetic
python examples/04_complexity.py en           # complexity + comparison of FOUR algorithms
python examples/05_code_walkthrough.py en     # «code ↔ data» panels for both functions
python examples/06_full_walkthrough.py en     # full synopsis trace (21 frames) + auto-block in README

# 3. The same in Ukrainian (→ docs/images/) — drop the `en` argument:
python examples/01_polynomial_hash.py
python examples/06_full_walkthrough.py
```

The seven scripts together generate **44 static figures** (`.png`, including 21 frames of the full trace in `docs/images/walkthrough/`), **7 GIF animations** (`.gif`) and **7 MP4 videos** (`.mp4`) in [`docs/images/`](docs/images), and print text outputs to the console; with the `en` argument the same media in English go to [`docs/images/en/`](docs/images/en). The example `06_full_walkthrough.py` additionally updates the full-trace block in the README between the `<!-- WALKTHROUGH:START/END -->` markers (idempotently). They run in a few seconds (the animations — up to half a minute). **MP4** is encoded only when `ffmpeg` is available (system or from `imageio-ffmpeg`); without it only GIFs are built — the build never fails.

Check the algorithm's correctness (results are cross-checked against the built-in `str.find()`):

```bash
python tests/test_core.py     # core correctness (no external dependencies)
python tests/test_smoke.py    # smoke: rendering, GIF and i18n do not fail (matplotlib, pillow)
# or both via pytest (pip install -e ".[dev]"):
pytest
```

The `test_core.py` tests cover: the polynomial hash matching the synopsis references (`abc → 90`, `developer → 35`, `general → 82`, `abc` without the modulus → `6382179`); `rabin_karp_search` matching the built-in `str.find()` (all cases + a series of random inputs); reproduction of the synopsis (`rabin_karp_search("Being a developer is not easy", "developer") == 8`); the **critical invariant** (the rolling hash of each window == the `polynomial_hash` of that window computed from scratch); **collisions** (a found pair of different strings with the same hash does not cause a false match — the char check saves us); `rabin_karp_search_all` (all occurrences); **agreement of the four algorithms** (`RK == naive == KMP == Boyer-Moore == str.find()` on random inputs); counters (best/avg — few char checks, worst under a small modulus — many); edge cases (empty pattern, pattern longer than the text → `-1`, pattern == text → `0`, single character). The `test_smoke.py` smoke tests verify that every drawing function of both phases and the GIF assembly run without errors, the full-trace invariant, and that **all Cyrillic labels have an English translation** (the `missing_translations` audit).

Minimal library usage:

```python
from rabin_karp_string_search import polynomial_hash, rabin_karp_search, rabin_karp_search_all

print(polynomial_hash("abc"))            # 90
print(polynomial_hash("developer"))      # 35
print(rabin_karp_search("Being a developer is not easy", "developer"))  # 8
print(rabin_karp_search_all("she sells sea shells by the sea shore", "sea"))  # [10, 28]
```
