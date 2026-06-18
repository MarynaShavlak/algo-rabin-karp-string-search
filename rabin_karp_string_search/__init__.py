"""Навчальна реалізація та візуалізація алгоритму Рабіна-Карпа (Rabin-Karp).

Пакет розділено на модулі:

* :mod:`rabin_karp_string_search.core` — самі алгоритми (``polynomial_hash``,
  ``rabin_karp_search``, ``rabin_karp_search_all``, варіант без rolling,
  інструментовані ``*_steps``), метрики/лічильники та утиліта пошуку колізій;
* :mod:`rabin_karp_string_search.visualization` — функції малювання поліноміального
  хешу, ковзного вікна, rolling-оновлення, порівняння хешів, **колізії**, еволюції
  пошуку, графіків складності та порівняння чотирьох алгоритмів (потребують
  ``matplotlib``);
* :mod:`rabin_karp_string_search.walkthrough` — покрокові панелі «код ↔ дані»
  окремо для ``polynomial_hash`` і для ``rabin_karp_search`` (потребує ``matplotlib``);
* :mod:`rabin_karp_string_search.animation` — збірка анімацій GIF (Pillow) +
  MP4 (ffmpeg).

``core`` та ``i18n`` не тягнуть ``matplotlib``, тож ``import
rabin_karp_string_search`` лишається легким; модулі малювання імпортують явно
(``from rabin_karp_string_search.visualization import …``).

Приклад::

    from rabin_karp_string_search import polynomial_hash, rabin_karp_search

    print(polynomial_hash("abc"))        # 90
    print(polynomial_hash("developer"))  # 35
    print(rabin_karp_search("Being a developer is not easy", "developer"))  # 8
"""

from .core import (
    Event,
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
from .i18n import get_lang, set_lang, t

__all__ = [
    "polynomial_hash",
    "polynomial_hash_raw",
    "polynomial_hash_steps",
    "rabin_karp_search",
    "rabin_karp_search_all",
    "rabin_karp_search_recompute",
    "rabin_karp_search_steps",
    "rabin_karp_metrics",
    "count_hash_char_ops",
    "count_naive_comparisons",
    "count_kmp_comparisons",
    "count_boyer_moore_comparisons",
    "find_collisions",
    "Event",
    # двомовні підписи (uk/en) — без важких залежностей, тож безпечно тут
    "t",
    "set_lang",
    "get_lang",
]

# Єдине джерело правди для версії пакета: pyproject.toml читає його звідси через
# [tool.setuptools.dynamic] version = { attr = "rabin_karp_string_search.__version__" }.
__version__ = "1.0.0"
