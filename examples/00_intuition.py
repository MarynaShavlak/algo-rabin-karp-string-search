"""Приклад 0 — інтуїція алгоритму Рабіна-Карпа.

Ілюстрації для розділу «Інтуїція» README: головний концептуальний поворот —
порівнювати **не символи, а ХЕШІ** (числа). Рядок перетворюється на число
(поліноміальний хеш), і замість того, щоб на кожному вирівнюванні звіряти символи,
ми порівнюємо два цілих; посимвольну перевірку робимо лише на збігу хешів. Плюс
ідея **ковзного вікна** завдовжки з шаблон. Один маленький приклад. Усі рисунки
зберігаються в ``docs/images/``.

Запуск:  ``python examples/00_intuition.py``      (українською → docs/images/)
         ``python examples/00_intuition.py en``   (англійською → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, save_figure
from _searches import HASH_ABC

from rabin_karp_string_search.core import rabin_karp_search_steps  # noqa: E402
from rabin_karp_string_search.i18n import t  # noqa: E402
from rabin_karp_string_search.visualization import (  # noqa: E402
    configure_style,
    draw_polynomial_hash,
    draw_search_evolution,
)


def main() -> None:
    configure_style()

    # 1) рядок → число: головний новий герой розбору (хеш «abc» = 90)
    save_figure(draw_polynomial_hash(HASH_ABC.s), "intuition_hash.png")

    # 2) ідея ковзного вікна: вікна та їхні хеші проти хешу шаблону (малий приклад)
    _, events = rabin_karp_search_steps("ababab", "bab")
    save_figure(draw_search_evolution(events), "intuition_window.png")

    print(t("Збережено рисунки інтуїції: рядок → хеш та ідея ковзного вікна."))
    print_saved_location()


if __name__ == "__main__":
    main()
