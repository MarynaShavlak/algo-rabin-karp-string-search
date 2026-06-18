"""Приклад 1 — ПОЛІНОМІАЛЬНИЙ ХЕШ (рядок → число), фаза хешування.

Головний новий герой розбору. Перетворюємо рядок на число за формулою
:math:`h(s) = \\sum_i s[i]\\cdot b^{\\,n-i-1} \\bmod m`. Відтворюємо еталони конспекту:

* ``"abc"`` → ``6382179`` без модуля → ``90`` (mod 101) — СИГНАТУРНИЙ приклад;
* ``"developer"`` → ``35``;
* ``"general"`` → ``82``.

Друкує хеші у форматі конспекту (саме воно дослівно — у README) та повну
покрокову Horner-акумуляцію. Зберігає сигнатурні кадри хешу й кадри побудови,
а також збирає **анімацію** Horner-акумуляції. Наприкінці звіряє
:func:`polynomial_hash` з очікуваними значеннями.

Запуск:  ``python examples/01_polynomial_hash.py``      (українською → docs/images/)
         ``python examples/01_polynomial_hash.py en``   (англійською → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, save_anim, save_figure
from _searches import HASH_ABC, HASH_CASES, HASH_DEVELOPER, HASH_GENERAL

import matplotlib.pyplot as plt  # noqa: E402

from rabin_karp_string_search.core import (  # noqa: E402
    polynomial_hash,
    polynomial_hash_raw,
    polynomial_hash_steps,
)
from rabin_karp_string_search.i18n import t  # noqa: E402
from rabin_karp_string_search.visualization import (  # noqa: E402
    configure_style,
    draw_hash_build_step,
    draw_polynomial_hash,
)

# Тривалість кадру анімації за типом події (мс).
_DUR = {"init": 1200, "term": 950, "final": 2400}


def main() -> None:
    configure_style()
    print(t("Поліноміальний хеш (рядок → число)"))
    print()

    # 1) хеші у форматі конспекту — РІВНО 90, 35, 82 (для README — text-блок)
    for case in HASH_CASES:
        print(f'polynomial_hash("{case.s}") = {polynomial_hash(case.s)}')
    print()

    # 2) «abc» без модуля: велике число 6382179, тоді mod 101 = 90 (сигнатурний приклад)
    a, b, c = (ord(ch) for ch in "abc")
    print(t('«abc» без модуля: ord("a")·256² + ord("b")·256¹ + ord("c")·256⁰ ='
            ' {a} + {b} + {c} = {raw}').format(
        a=a * 256 ** 2, b=b * 256, c=c, raw=polynomial_hash_raw("abc")))
    print(t("{raw} mod 101 = {h}").format(raw=polynomial_hash_raw("abc"),
                                          h=polynomial_hash("abc")))
    print()

    # 3) покрокова Horner-акумуляція «developer» (для README — text-блок)
    print(t("Покрокова Horner-акумуляція для «{s}»:").format(s=HASH_DEVELOPER.s))
    _, events = polynomial_hash_steps(HASH_DEVELOPER.s)
    for e in events:
        if e["kind"] == "term":
            print(t("  i={i}: + ord(«{c}»)·{p} → hash = {h}").format(
                i=e["i"], c=e["char"], p=int(e["power"]), h=int(e["hash_value"])))
    print()

    # 4) сигнатурні кадри хешу для основних рядків
    save_figure(draw_polynomial_hash(HASH_ABC.s), "hash_abc.png")
    save_figure(draw_polynomial_hash(HASH_DEVELOPER.s), "hash_developer.png")
    save_figure(draw_polynomial_hash(HASH_GENERAL.s), "hash_general.png")

    # 5) кадри Horner-акумуляції «developer» (init + кілька термів + final)
    _, ev = polynomial_hash_steps(HASH_DEVELOPER.s)
    for nn, e in enumerate(ev):
        if e["kind"] in ("init", "final") or e["i"] in (0, 1, 8):
            save_figure(draw_hash_build_step(e), f"hash_build_{HASH_DEVELOPER.name}_{nn:02d}.png")
            plt.close("all")

    # 6) анімація Horner-акумуляції «developer»
    figures = [draw_hash_build_step(e) for e in ev]
    durations = [_DUR.get(e["kind"], 900) for e in ev]
    save_anim(figures, "hash_build", durations)
    print(t("  hash_build: {n} кадрів").format(n=len(figures)))

    # 7) звірка з еталонами конспекту
    for case in HASH_CASES:
        assert polynomial_hash(case.s) == case.expected, (case.s, case.expected)
    assert polynomial_hash_raw("abc") == 6382179
    print(t("Звірка: polynomial_hash збігається з еталонами конспекту (90, 35, 82) ✓"))

    print_saved_location()


if __name__ == "__main__":
    main()
