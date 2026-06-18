"""Приклад 4 — СКЛАДНІСТЬ і ПОВНЕ порівняння ЧОТИРЬОХ рядкових алгоритмів.

Два сюжети:

1. **Складність Рабіна-Карпа**: середній/найкращий :math:`O(n+m)` (колізії
   рідкісні, хеш розподіляє рівномірно) проти найгіршого :math:`O(n\\cdot m)`
   (багато колізій → багато прямих порівнянь підрядків);
2. **Капстоун серії** — порівняння **чотирьох** рядкових алгоритмів за кількістю
   **посимвольних** порівнянь на тих самих входах: наївний :math:`O(n\\cdot m)` /
   KMP :math:`O(n+m)` гарантовано / Боєра-Мура (швидкий на практиці) /
   Рабіна-Карпа (порівнює здебільшого ХЕШІ, char-перевірки — лише на збігу хешів).

Друкує порівняльну таблицю (саме вона — у README) і зберігає графік складності та
стовпчикову діаграму чотирьох алгоритмів.

Запуск:  ``python examples/04_complexity.py``      (українською → docs/images/)
         ``python examples/04_complexity.py en``   (англійською → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, save_figure
from _searches import SEARCH_KONSPECT

from rabin_karp_string_search.core import (  # noqa: E402
    count_boyer_moore_comparisons,
    count_kmp_comparisons,
    count_naive_comparisons,
    rabin_karp_metrics,
)
from rabin_karp_string_search.i18n import t  # noqa: E402
from rabin_karp_string_search.visualization import (  # noqa: E402
    configure_style,
    draw_compare_four,
    draw_complexity,
)

# Входи для порівняння: конспект-приклад + патологічний (наївний вибухає).
_INPUTS = [
    (SEARCH_KONSPECT.text, SEARCH_KONSPECT.pattern, t("конспект «developer»")),
    ("a" * 24, "a" * 5 + "b", t("патологічний «aaaa…» / «aaaaab»")),
]


def _row(text, pattern):
    naive = count_naive_comparisons(text, pattern)
    kmp = count_kmp_comparisons(text, pattern)
    bm = count_boyer_moore_comparisons(text, pattern)
    rk = rabin_karp_metrics(text, pattern)
    return naive, kmp, bm, rk["char_comparisons"], rk["hash_comparisons"]


def main() -> None:
    configure_style()

    # === порівняльна таблиця чотирьох алгоритмів (для README — text-блок) ====
    print(t("Чотири рядкові алгоритми: посимвольні порівняння на тих самих входах"))
    print()
    w = max(len(label) for _t, _p, label in _INPUTS) + 2
    head = (f"  {t('вхід'):<{w}}| {t('наївний'):^7} | {'KMP':^5} | "
            f"{t('Боєра-Мура'):^11} | {t('Рабіна-Карпа (char + hash)')}")
    print(head)
    print("  " + "-" * (len(head) - 2))
    for text, pattern, label in _INPUTS:
        naive, kmp, bm, rk_char, rk_hash = _row(text, pattern)
        rk_cell = t("{c} char + {h} hash").format(c=rk_char, h=rk_hash)
        print(f"  {label:<{w}}| {naive:^7} | {kmp:^5} | {bm:^11} | {rk_cell}")
    print()

    print(t("Висновок: Рабін-Карп робить НАЙМЕНШЕ посимвольних порівнянь — бо"))
    print(t("здебільшого порівнює ХЕШІ (цілі числа), а символи звіряє лише на збігу хешів."))
    print()

    # === графіки ============================================================
    save_figure(draw_complexity(), "complexity.png")
    save_figure(draw_compare_four(SEARCH_KONSPECT.text, SEARCH_KONSPECT.pattern),
                "compare_four.png")
    # додатковий графік на патологічному вході — наочніший контраст
    save_figure(draw_compare_four("a" * 24, "a" * 5 + "b"), "compare_four_worst.png")

    print_saved_location()


if __name__ == "__main__":
    main()
