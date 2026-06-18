"""Тести коректності алгоритму Рабіна-Карпа.

Покривають те, про що йдеться в README:

* **поліноміальний хеш** дорівнює очікуваним еталонам конспекту
  (``abc → 90``, ``developer → 35``, ``general → 82``, ``abc`` без модуля → ``6382179``);
* **``rabin_karp_search``** повертає той самий індекс, що вбудований ``str.find()`` —
  на всіх навчальних кейсах, крайових випадках і серії **випадкових** входів
  (``str.find()`` — еталон істини);
* **відтворення конспекту**: ``rabin_karp_search("Being a developer is not easy", "developer") == 8``;
* **КРИТИЧНИЙ ІНВАРІАНТ**: rolling-хеш на кожному вікні (з журналу) **дорівнює**
  ``polynomial_hash`` цього вікна (rolling == перерахунок з нуля);
* **КОЛІЗІЯ**: знайдена пара різних рядків з однаковим хешем — хеші рівні, рядки
  різні, і ``rabin_karp_search`` НЕ дає хибного збігу (char-перевірка рятує);
* **``rabin_karp_search_all``** повертає всі стартові позиції (звірка з ручним
  find-циклом, зокрема перекривні входження);
* **чотири алгоритми**: ``RK == наївний == KMP == Боєра-Мура == str.find()`` на серії
  випадкових (текст, шаблон);
* **лічильники**: best/avg — мало char-перевірок; worst (форсовані колізії малим
  модулем) — багато; rolling рахується лінійно, перерахунок — як n·m;
* **крайові випадки**: порожній шаблон (готча ``pow(base, -1)``), шаблон довший за
  текст → ``-1``, шаблон == текст → ``0``, один символ;
* **узгодженість обох журналів подій** (на них стоять усі візуалізації).

Запуск::

    pytest                       # якщо встановлено pytest
    python tests/test_core.py    # без pytest (вбудований раннер)
"""

from __future__ import annotations

import os
import random
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "examples")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rabin_karp_string_search.core import (  # noqa: E402
    count_boyer_moore_comparisons,
    count_hash_char_ops,
    count_kmp_comparisons,
    count_naive_comparisons,
    find_collisions,
    polynomial_hash,
    polynomial_hash_raw,
    polynomial_hash_steps,
    rabin_karp_metrics,
    rabin_karp_search,
    rabin_karp_search_all,
    rabin_karp_search_recompute,
    rabin_karp_search_steps,
)
from _searches import (  # noqa: E402
    COLLISION_CASES,
    EDGE_CASES,
    HASH_CASES,
    KONSPECT_PATTERN,
    RAW,
    SEARCH_BEST,
    SEARCH_CASES,
    SEARCH_COLLISION,
    SEARCH_WORST,
)


# ---------------------------------------------------------------------------
# Незалежні еталони істини (брутфорс) для чотирьох алгоритмів
# ---------------------------------------------------------------------------
def _brute_all(text, pattern):
    """Усі стартові позиції входжень (зокрема перекривні) — ручний find-цикл."""
    m, n = len(pattern), len(text)
    if m == 0:
        return list(range(n + 1))
    return [i for i in range(n - m + 1) if text[i:i + m] == pattern]


def _naive_search(text, pattern):
    """Наївний пошук (позиція першого входження) — незалежний еталон."""
    m, n = len(pattern), len(text)
    for i in range(n - m + 1):
        if text[i:i + m] == pattern:
            return i
    return -1


def _kmp_search(text, pattern):
    """KMP-пошук (позиція першого входження) — незалежний еталон."""
    m, n = len(pattern), len(text)
    if m == 0:
        return 0
    lps = [0] * m
    length = 0
    i = 1
    while i < m:
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length != 0:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    i = j = 0
    while i < n:
        if pattern[j] == text[i]:
            i += 1
            j += 1
            if j == m:
                return i - j
        elif j != 0:
            j = lps[j - 1]
        else:
            i += 1
    return -1


def _bm_search(text, pattern):
    """Боєра-Мура (таблиця поганого символу) — незалежний еталон."""
    m, n = len(pattern), len(text)
    if m == 0:
        return 0
    if m > n:
        return -1
    last = {pattern[k]: k for k in range(m)}
    s = 0
    while s <= n - m:
        j = m - 1
        while j >= 0 and pattern[j] == text[s + j]:
            j -= 1
        if j < 0:
            return s
        s += max(1, j - last.get(text[s + j], -1))
    return -1


# ---------------------------------------------------------------------------
# Фаза 1 — поліноміальний хеш
# ---------------------------------------------------------------------------
def test_polynomial_hash_matches_konspekt():
    """polynomial_hash дорівнює еталонам конспекту: abc→90, developer→35, general→82."""
    for case in HASH_CASES:
        assert polynomial_hash(case.s) == case.expected, case.s
    assert polynomial_hash("abc") == 90
    assert polynomial_hash("developer") == 35
    assert polynomial_hash("general") == 82


def test_polynomial_hash_raw_abc():
    """«abc» без модуля → 6382179, і 6382179 % 101 == 90."""
    assert polynomial_hash_raw("abc") == 6382179
    assert 6382179 % 101 == 90 == polynomial_hash("abc")


def test_hash_steps_result_matches():
    """Інструментований polynomial_hash_steps дає той самий хеш, що polynomial_hash."""
    for s in ("abc", "developer", "general", "a", ""):
        h, events = polynomial_hash_steps(s)
        assert h == polynomial_hash(s), s
        assert events[0]["kind"] == "init" and events[-1]["kind"] == "final"


# ---------------------------------------------------------------------------
# Фаза 2 — пошук
# ---------------------------------------------------------------------------
def test_rabin_karp_matches_strfind_on_cases():
    """rabin_karp_search == str.find() на всіх навчальних пошук-кейсах."""
    for case in SEARCH_CASES:
        got = rabin_karp_search(case.text, case.pattern)
        assert got == case.text.find(case.pattern) == case.expected, case.name


def test_konspekt_reproduction():
    """Відтворення конспекту: rabin_karp_search(«Being a developer…», «developer») == 8."""
    assert rabin_karp_search(RAW, KONSPECT_PATTERN) == 8
    assert RAW.find(KONSPECT_PATTERN) == 8


def test_recompute_equals_rolling():
    """rabin_karp_search_recompute (хеш з нуля) == rabin_karp_search (rolling)."""
    for case in SEARCH_CASES:
        assert rabin_karp_search_recompute(case.text, case.pattern) == \
            rabin_karp_search(case.text, case.pattern), case.name


def test_search_all_matches_bruteforce():
    """rabin_karp_search_all == ручний find-цикл (зокрема перекривні входження)."""
    cases = [
        ("she sells sea shells by the sea shore", "sea"),  # [10, 28]
        ("aaaa", "aa"),                                    # [0, 1, 2] — перекривні
        ("ababab", "ab"),                                  # [0, 2, 4]
        ("for a jar of jam", "jar"),
        (RAW, KONSPECT_PATTERN),
    ]
    for text, pattern in cases:
        assert rabin_karp_search_all(text, pattern) == _brute_all(text, pattern), (text, pattern)
    assert rabin_karp_search_all("aaaa", "aa") == [0, 1, 2]
    assert rabin_karp_search_all("she sells sea shells by the sea shore", "sea") == [10, 28]


def test_random_fuzz_all_four_equal_strfind():
    """Серія випадкових (текст, шаблон): RK == наївний == KMP == BM == str.find()."""
    rng = random.Random(424242)
    for _ in range(1500):
        text = "".join(rng.choice("abc ") for _ in range(rng.randint(0, 30)))
        pattern = "".join(rng.choice("abc ") for _ in range(rng.randint(1, 6)))
        truth = text.find(pattern)
        assert rabin_karp_search(text, pattern) == truth, (text, pattern)
        assert _naive_search(text, pattern) == truth, (text, pattern)
        assert _kmp_search(text, pattern) == truth, (text, pattern)
        assert _bm_search(text, pattern) == truth, (text, pattern)
        assert rabin_karp_search_all(text, pattern) == _brute_all(text, pattern), (text, pattern)


# ---------------------------------------------------------------------------
# КРИТИЧНИЙ ІНВАРІАНТ: rolling-хеш кожного вікна == polynomial_hash вікна
# ---------------------------------------------------------------------------
def test_rolling_hash_equals_recompute_per_window():
    """Хеш вікна з журналу (rolling) ДОРІВНЮЄ polynomial_hash цього вікна (з нуля)."""
    rng = random.Random(20260618)
    inputs = [(c.text, c.pattern) for c in SEARCH_CASES]
    for _ in range(600):
        text = "".join(rng.choice("abcde ") for _ in range(rng.randint(1, 30)))
        pattern = "".join(rng.choice("abcde ") for _ in range(rng.randint(1, 6)))
        inputs.append((text, pattern))
    for text, pattern in inputs:
        _, events = rabin_karp_search_steps(text, pattern)
        for e in events:
            if e["kind"] == "window":
                window = str(e["window"])
                assert int(e["window_hash"]) == polynomial_hash(window), (text, pattern, window)


# ---------------------------------------------------------------------------
# КОЛІЗІЇ — рівні хеші ≠ рівні рядки; char-перевірка рятує
# ---------------------------------------------------------------------------
def test_collision_pairs_have_equal_hash_different_strings():
    """Знайдені пари: однакова довжина, різні рядки, ОДНАКОВИЙ хеш."""
    for cc in COLLISION_CASES:
        assert cc.s1 != cc.s2, cc
        assert len(cc.s1) == len(cc.s2), cc
        assert polynomial_hash(cc.s1) == polynomial_hash(cc.s2) == cc.hash, cc


def test_collision_does_not_cause_false_match():
    """Колізія НЕ дає хибного збігу: «jar» немає в «for» (хоч хеші рівні)."""
    # «for» і «jar» мають однаковий хеш 35, але це різні рядки
    assert polynomial_hash("for") == polynomial_hash("jar") == 35
    assert rabin_karp_search("for", "jar") == -1 == "for".find("jar")
    # колізія під час пошуку: «for» (хеш шаблону) відкинуто, справжній збіг на 6
    assert rabin_karp_search(SEARCH_COLLISION.text, SEARCH_COLLISION.pattern) == 6
    m = rabin_karp_metrics(SEARCH_COLLISION.text, SEARCH_COLLISION.pattern)
    assert m["collisions"] >= 1, m            # була хоча б одна колізія
    assert m["char_verifications"] == m["collisions"] + 1  # колізії + один справжній збіг


def test_find_collisions_scan():
    """find_collisions знаходить пари однакової довжини з однаковим хешем."""
    sample = ["for", "jar", "cat", "dog", "heap", "user", "tree", "node"]
    pairs = find_collisions(sample)
    same_len = [(a, b, h) for a, b, h in pairs if len(a) == len(b)]
    assert any({a, b} == {"for", "jar"} for a, b, _ in same_len)
    assert any({a, b} == {"heap", "user"} for a, b, _ in same_len)
    for a, b, h in same_len:
        assert polynomial_hash(a) == polynomial_hash(b) == h


# ---------------------------------------------------------------------------
# Лічильники: best/avg проти worst; rolling проти перерахунку
# ---------------------------------------------------------------------------
def test_metrics_best_case_few_verifications():
    """Best/avg: хеш рідко збігається → мало char-перевірок, без колізій."""
    m = rabin_karp_metrics(SEARCH_BEST.text, SEARCH_BEST.pattern)
    assert m["collisions"] == 0
    assert m["char_verifications"] <= 2          # лише навколо справжнього збігу
    assert m["hash_comparisons"] >= m["char_verifications"]


def test_metrics_worst_case_many_collisions_small_modulus():
    """Worst: малий модуль → багато колізій → багато char-порівнянь (RK = наївний)."""
    good = rabin_karp_metrics(SEARCH_WORST.text, SEARCH_WORST.pattern, modulus=101)
    bad = rabin_karp_metrics(SEARCH_WORST.text, SEARCH_WORST.pattern, modulus=1)
    assert good["collisions"] == 0               # просте 101 — без колізій
    assert bad["collisions"] >= good["collisions"] + 5   # модуль 1 — багато колізій
    naive = count_naive_comparisons(SEARCH_WORST.text, SEARCH_WORST.pattern)
    assert bad["char_comparisons"] == naive      # під модулем 1 RK = наївний


def test_rolling_cheaper_than_recompute():
    """Лічильник хешування: rolling лінійний, перерахунок — як n·m."""
    for n in (16, 32, 64):
        roll = count_hash_char_ops("a" * n, "abcd", rolling=True)
        recompute = count_hash_char_ops("a" * n, "abcd", rolling=False)
        assert roll < recompute, (n, roll, recompute)
    # квадратичний відрив: подвоєння n множить розрив
    r1 = count_hash_char_ops("a" * 32, "abcd", rolling=False)
    r2 = count_hash_char_ops("a" * 64, "abcd", rolling=False)
    assert r2 > 2 * r1 - 8                        # ~подвоюється (n·m)


# ---------------------------------------------------------------------------
# Крайові випадки
# ---------------------------------------------------------------------------
def test_edge_cases_strfind():
    """Крайові випадки (шаблон довший / == текст / один символ) == str.find()."""
    for text, pattern, expected in EDGE_CASES:
        if pattern == "":
            continue   # порожній шаблон — окремо нижче
        assert rabin_karp_search(text, pattern) == text.find(pattern) == expected, (text, pattern)


def test_empty_pattern():
    """Порожній шаблон: безпечні версії дають 0/усі позиції (готча pow(base,-1))."""
    # безпечна обробка в інструментованій/all-версіях
    result, _ = rabin_karp_search_steps("abc", "")
    assert result == 0 == "abc".find("")
    assert rabin_karp_search_all("abc", "") == [0, 1, 2, 3]
    assert rabin_karp_search_all("", "") == [0]


def test_pattern_longer_than_text():
    """Шаблон довший за текст → -1 (без падіння, хоч хеш першого зрізу рахується)."""
    assert rabin_karp_search("ab", "abc") == -1
    assert rabin_karp_search_steps("ab", "abc")[0] == -1
    assert rabin_karp_search_all("ab", "abcde") == []


def test_pattern_equals_text():
    assert rabin_karp_search("developer", "developer") == 0
    assert rabin_karp_search_all("abc", "abc") == [0]


def test_single_char_pattern():
    assert rabin_karp_search("abcabc", "c") == 2
    assert rabin_karp_search_all("abcabc", "a") == [0, 3]


# ---------------------------------------------------------------------------
# Узгодженість журналів подій
# ---------------------------------------------------------------------------
def test_hash_journal_consistency():
    """Журнал хешу узгоджений: init → терми → final; фінальний хеш = polynomial_hash."""
    h, events = polynomial_hash_steps("developer")
    assert events[0]["kind"] == "init"
    assert events[-1]["kind"] == "final"
    assert int(events[-1]["hash_value"]) == h == polynomial_hash("developer") == 35
    terms = [e for e in events if e["kind"] == "term"]
    assert len(terms) == len("developer")
    for e in events:
        assert e["phase"] == "hash"
        assert 0 <= int(e["hash_value"]) < 101    # завжди в межах модуля


def test_search_journal_consistency():
    """Журнал пошуку узгоджений: лічильники не спадають; кожна колізія — справжня."""
    result, events = rabin_karp_search_steps(RAW, KONSPECT_PATTERN)
    assert events[0]["kind"] == "init"
    assert events[-1]["kind"] == "final"
    assert int(events[-1]["result"]) == result == 8
    prev_hc = prev_cv = 0
    for e in events:
        assert e["phase"] == "search"
        assert int(e["hash_comparisons"]) >= prev_hc
        assert int(e["char_verifications"]) >= prev_cv
        prev_hc = int(e["hash_comparisons"])
        prev_cv = int(e["char_verifications"])
    # кожна подія collision: хеш вікна == хеш шаблону, але рядки різні
    for e in events:
        if e["kind"] == "collision":
            assert int(e["window_hash"]) == int(e["pattern_hash"])
            assert str(e["window"]) != str(e["pattern"])
    # лічильники узгоджені з метриками
    m = rabin_karp_metrics(RAW, KONSPECT_PATTERN)
    assert m["collisions"] == sum(1 for e in events if e["kind"] == "collision")


# ---------------------------------------------------------------------------
# Мінімальний раннер на випадок, якщо pytest не встановлено
# ---------------------------------------------------------------------------
def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} тестів пройдено")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_without_pytest() else 0)
