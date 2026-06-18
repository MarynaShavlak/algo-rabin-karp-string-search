"""Приклад 5 — покрокова візуалізація «код ↔ дані» ОКРЕМО для двох функцій.

Кожен крок = рядок із двох панелей: ліворуч код алгоритму з **підсвіченими
активними рядками** (колір показує гілку, що спрацювала), праворуч — **дані** саме
на цьому кроці. Логіку див. у ``rabin_karp_string_search/walkthrough.py``.

Дві функції — дві панелі:

* **хешування** ``polynomial_hash`` для ``"abc"`` (праворуч — символи й накопичений
  хеш, Horner-крок за кроком);
* **пошук** ``rabin_karp_search`` для компактного ``"for jar"`` / ``"jar"``
  (праворуч — ковзне вікно з хеш-бейджем; на зміщенні 0 — **колізія** «for» з хешем
  «jar», справжній збіг — на 4).

Кожна функція дає **статичну сітку** (усі кроки) і **повну анімацію**.

Запуск:  ``python examples/05_code_walkthrough.py``      (uk → docs/images/)
         ``python examples/05_code_walkthrough.py en``   (en → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, save_anim, save_figure

import matplotlib.pyplot as plt  # noqa: E402

from rabin_karp_string_search.i18n import t  # noqa: E402
from rabin_karp_string_search.visualization import configure_style  # noqa: E402
from rabin_karp_string_search.walkthrough import (  # noqa: E402
    build_hash_steps,
    build_search_steps,
    draw_code_walkthrough_grid,
    pick_illustrative,
    render_code_step,
)

# Тривалість кадру анімації за типом кроку (мс).
_DUR = {"init": 1500, "term": 1100, "final": 2400, "slide": 1100,
        "collision": 2000, "match": 2600, "not_found": 2400}


def _walkthrough(steps, grid_name: str, anim_name: str, grid_title: str) -> None:
    """Зберігає статичну сітку (усі кроки) і повну анімацію для одного журналу."""
    shown = pick_illustrative(steps)
    grid = draw_code_walkthrough_grid(shown, grid_title)
    save_figure(grid, grid_name + ".png")
    plt.close(grid)
    print(t("  {name}: сітка, {n} рядків").format(name=grid_name, n=len(shown)))

    figures = [render_code_step(s) for s in steps]
    durations = [_DUR.get(s["kind"], 1100) for s in steps]
    save_anim(figures, anim_name, durations)
    print(t("  {name}: анімація, {n} кадрів").format(name=anim_name, n=len(figures)))


def main() -> None:
    configure_style()
    print(t("Генерую покрокові панелі «код ↔ дані»…"))

    # 1) хешування: polynomial_hash для «abc» (Horner-акумуляція)
    _walkthrough(
        build_hash_steps("abc"),
        "code_hash_grid", "code_hash_walk",
        t("Поліноміальний хеш «abc»: код ↔ накопичений хеш"))

    # 2) пошук: rabin_karp_search для «for jar» / «jar» (колізія на 0, збіг на 4)
    _walkthrough(
        build_search_steps("for jar", "jar"),
        "code_search_grid", "code_search_walk",
        t("Пошук «jar» у «for jar»: код ↔ ковзне вікно"))

    print_saved_location()


if __name__ == "__main__":
    main()
