"""Приклад 2 — КОНСПЕКТ-приклад пошуку: ``("Being a developer is not easy", "developer")`` → ``8``.

Відтворює головний приклад конспекту дослівно. Драйвер
``rabin_karp_search(main_string, substring)`` + ``print(...)`` виводить РІВНО
**Substring found at index 8** (англійський літерал коду — НЕ перекладається).
Друкує хеш шаблону, повне трасування пошуку (одне вікно на рядок: видно хеш
кожного вікна, збіг/незбіг із хешем шаблону, **колізію** на зміщенні 6 — хеш 35
збігся, а «a develop» ≠ «developer» — і справжній збіг на 8) та результат; усе це
дослівно наведене в README. Також показує кейс **НЕ ЗНАЙДЕНО** (друкує
«Substring not found»). Зберігає кадри пошуку й анімації.

Запуск:  ``python examples/02_search.py``      (українською → docs/images/)
         ``python examples/02_search.py en``   (англійською → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, save_anim, save_figure
from _searches import SEARCH_KONSPECT, SEARCH_NOT_FOUND

from rabin_karp_string_search.core import (  # noqa: E402
    polynomial_hash,
    rabin_karp_search,
    rabin_karp_search_steps,
)
from rabin_karp_string_search.i18n import t  # noqa: E402
from rabin_karp_string_search.visualization import (  # noqa: E402
    configure_style,
    draw_rolling_window,
    draw_search_evolution,
    print_result,
    print_search_trace,
)

EXAMPLE = SEARCH_KONSPECT
_DUR = {"init": 1300, "window": 700, "hash_match": 1200, "verify": 1200,
        "collision": 1800, "match_found": 2600, "roll": 600, "not_found": 2400,
        "final": 1600}


def _driver(main_string: str, substring: str) -> None:
    """Драйвер конспекту ДОСЛІВНО — друкує «Substring found at index 8»."""
    position = rabin_karp_search(main_string, substring)
    if position != -1:
        print(f"Substring found at index {position}")
    else:
        print("Substring not found")


def _animate(text: str, pattern: str, name: str) -> None:
    _, events = rabin_karp_search_steps(text, pattern)
    frames_ev = [e for e in events if e["kind"] != "final"]
    figures = [draw_rolling_window(e) for e in frames_ev]
    durations = [_DUR.get(e["kind"], 700) for e in frames_ev]
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів").format(name=name, n=len(figures)))


def main() -> None:
    configure_style()
    print(t("Приклад із конспекту: пошук «{p}»").format(p=EXAMPLE.pattern))
    print()

    # 1) хеш шаблону
    print(t("Хеш шаблону «{p}»: {h}").format(p=EXAMPLE.pattern,
                                             h=polynomial_hash(EXAMPLE.pattern)))
    print()

    # 2) драйвер конспекту ДОСЛІВНО — друкує РІВНО «Substring found at index 8»
    _driver(EXAMPLE.text, EXAMPLE.pattern)
    print()

    # 3) повне трасування пошуку (вікно за вікном; для README — text-блок)
    res, events = rabin_karp_search_steps(EXAMPLE.text, EXAMPLE.pattern)
    print(t("Трасування пошуку (одне вікно на рядок):"))
    print_search_trace(events)
    print()

    # 4) підсумок + лічильники
    print_result(events)
    print()

    # 5) кейс НЕ ЗНАЙДЕНО — друкує «Substring not found»
    print(t("Пошук відсутнього шаблону «{p}»:").format(p=SEARCH_NOT_FOUND.pattern))
    _driver(SEARCH_NOT_FOUND.text, SEARCH_NOT_FOUND.pattern)
    print()

    # 6) кадри: драбинка вікон конспекту (видно колізію на 6 та збіг на 8)
    save_figure(draw_search_evolution(events), "search_konspekt.png")
    match = next(e for e in events if e["kind"] == "match_found")
    save_figure(draw_rolling_window(match), "search_konspekt_match.png")
    collision = next(e for e in events if e["kind"] == "collision")
    save_figure(draw_rolling_window(collision), "search_konspekt_collision.png")

    # 7) анімації: конспект-пошук та не-знайдено
    _animate(EXAMPLE.text, EXAMPLE.pattern, "search_konspekt")
    _animate(SEARCH_NOT_FOUND.text, SEARCH_NOT_FOUND.pattern, "search_not_found")

    # 8) звірка з еталоном істини str.find()
    assert res == EXAMPLE.expected == EXAMPLE.text.find(EXAMPLE.pattern)
    print(t("Звірка: rabin_karp_search == str.find() == {r} ✓").format(r=res))

    print_saved_location()


if __name__ == "__main__":
    main()
