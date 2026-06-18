"""Дані прикладів — єдине джерело правди для всіх навчальних інстансів Рабіна-Карпа.

Три типи інстансів:

* :class:`HashCase` — для **фази хешування**: рядок + очікуваний поліноміальний хеш
  (під фіксованими ``256``/``101``) + підпис. На них будують хеші (фаза 1).
* :class:`SearchCase` — для **фази пошуку**: текст + шаблон + підпис + очікувана
  позиція першого входження. На них трасують пошук (фаза 2).
* :class:`CollisionCase` — пара **різних** рядків однакової довжини з **однаковим**
  хешем (знайдена скануванням простору під ``(256, 101)``) — для розділу про колізії.

Самі рядки-**дані** та хеш-числа мовно нейтральні й лишаються незмінними в **обох**
мовах — перекладаються лише підписи (``caption``). Дані конспекту (текст
``"Being a developer is not easy"``, шаблон ``"developer"``, хеші ``90``/``35``/``82``,
велике число ``6382179``) збережено **дослівно**. Приклади імпортують потрібний
інстанс звідси, тож дані визначені рівно один раз.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class HashCase:
    """Інстанс фази хешування: рядок + очікуваний хеш (mod 101) + підпис."""

    s: str
    expected: int                  # polynomial_hash(s, 256, 101)
    caption: str
    name: str = ""


@dataclass(frozen=True)
class SearchCase:
    """Інстанс фази пошуку: текст + шаблон + підпис + очікувана позиція."""

    text: str
    pattern: str
    caption: str
    expected: int                  # позиція першого входження (як str.find), або -1
    name: str = ""


@dataclass(frozen=True)
class CollisionCase:
    """Колізія: два різні рядки однакової довжини з однаковим хешем під (256, 101)."""

    s1: str
    s2: str
    hash: int                      # спільний polynomial_hash(s1) == polynomial_hash(s2)
    caption: str
    name: str = ""


# ---------------------------------------------------------------------------
# Дані з конспекту (НЕ перекладаються).
# Драйвер конспекту друкує РІВНО: Substring found at index 8
# ---------------------------------------------------------------------------
RAW = "Being a developer is not easy"
KONSPECT_PATTERN = "developer"


# ---------------------------------------------------------------------------
# ХЕШ-кейси (тільки рядок) — еталони конспекту
# ---------------------------------------------------------------------------
#: Конспект: "abc" → 90 (а без модуля → 6382179).
HASH_ABC = HashCase("abc", 90, caption="приклад із конспекту (і 6382179 без модуля)", name="abc")
#: Конспект: хеш патерну пошуку "developer" → 35.
HASH_DEVELOPER = HashCase("developer", 35, caption="хеш патерну пошуку", name="developer")
#: Конспект: "general" → 82.
HASH_GENERAL = HashCase("general", 82, caption="ще приклад із конспекту", name="general")

#: Усі ХЕШ-кейси (для тестів і прикладу 01).
HASH_CASES: List[HashCase] = [HASH_ABC, HASH_DEVELOPER, HASH_GENERAL]


# ---------------------------------------------------------------------------
# ПОШУК-кейси (текст, шаблон)
# ---------------------------------------------------------------------------
#: Головний приклад конспекту: позиція 8 (driver друкує «Substring found at index 8»).
SEARCH_KONSPECT = SearchCase(RAW, KONSPECT_PATTERN,
                             caption="головний приклад конспекту", expected=8,
                             name="konspekt")

#: МАЛО ЗБІГІВ (best/avg, ≈ O(n+m)): хеш шаблону рідко збігається → мало char-перевірок.
SEARCH_BEST = SearchCase("a polynomial hash maps a string to a number", "string",
                         caption="мало збігів (близько до O(n+m))", expected=25,
                         name="best")

#: КОЛІЗІЯ ПІД ЧАС ПОШУКУ: вікно «for» має той самий хеш (35), що «jar», але це не «jar».
#: char-перевірка відкидає колізію на зміщенні 0; справжній збіг — на 6.
SEARCH_COLLISION = SearchCase("for a jar of jam", "jar",
                              caption="колізія під час пошуку (хеш «for» = хеш «jar» = 35)",
                              expected=6, name="collision")

#: НЕ ЗНАЙДЕНО: шаблон відсутній → -1 (driver друкує «Substring not found»).
SEARCH_NOT_FOUND = SearchCase(RAW, "manager",
                              caption="шаблон відсутній", expected=-1, name="not_found")

#: МНОЖИННІ ВХОДЖЕННЯ: «sea» трапляється двічі; rabin_karp_search → перше (10),
#: rabin_karp_search_all → [10, 28].
SEARCH_MULTI = SearchCase("she sells sea shells by the sea shore", "sea",
                          caption="множинні входження", expected=10, name="multi")

#: НАЙГІРШИЙ (багато колізій під МАЛИМ модулем): текст «aaaa…», шаблон «aaa…b».
#: Під простим 101 — 0 колізій (RK швидкий); під модулем 1 — кожне вікно колізує
#: (RK вироджується в наївний, O(n·m)). Результат у будь-якому разі -1.
SEARCH_WORST = SearchCase("a" * 16, "a" * 7 + "b",
                          caption="найгірший: багато колізій під малим модулем",
                          expected=-1, name="worst")

#: Усі ПОШУК-кейси (для тестів).
SEARCH_CASES: List[SearchCase] = [
    SEARCH_KONSPECT, SEARCH_BEST, SEARCH_COLLISION, SEARCH_NOT_FOUND,
    SEARCH_MULTI, SEARCH_WORST,
]


# ---------------------------------------------------------------------------
# КОЛІЗІЇ-кейси (різні рядки однакової довжини — однаковий хеш під (256, 101))
# ---------------------------------------------------------------------------
#: «for» і «jar» → обидва 35 (та сама пара, що демонструє колізію під час пошуку).
COLLISION_FOR_JAR = CollisionCase("for", "jar", 35,
                                  caption="класична пара: різні слова, хеш 35", name="for_jar")
#: «heap» і «user» → обидва 12 (дві програмістські абревіатури колізують).
COLLISION_HEAP_USER = CollisionCase("heap", "user", 12,
                                    caption="довші слова: хеш 12", name="heap_user")

#: Усі КОЛІЗІЇ-кейси (для тестів і прикладу 03).
COLLISION_CASES: List[CollisionCase] = [COLLISION_FOR_JAR, COLLISION_HEAP_USER]


# ---------------------------------------------------------------------------
# Крайові випадки (для тестів)
# ---------------------------------------------------------------------------
#: (текст, шаблон, очікувана позиція) — порожній/довший/рівний/один символ.
EDGE_CASES = [
    ("abcabc", "", 0),         # порожній шаблон (str.find("abcabc","") == 0)
    ("ab", "abc", -1),         # шаблон довший за текст
    ("abc", "abc", 0),         # шаблон == текст
    ("abcabc", "c", 2),        # шаблон з одного символу
]
