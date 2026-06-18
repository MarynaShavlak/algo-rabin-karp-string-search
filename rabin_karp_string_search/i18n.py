# -*- coding: utf-8 -*-
"""Двомовні підписи для візуалізацій (uk за замовчуванням / en).

Замість важкої інфраструктури ``gettext``/``.po`` тут застосовано прийом
**«вихідний рядок — це і є ключ»**: ключем у словнику перекладів виступає сам
український рядок. Наслідки:

* **Мова за замовчуванням лишається байт-у-байт незмінною.** Коли ``LANG == "uk"``,
  :func:`t` повертає аргумент *без жодного пошуку* — український вивід (і всі
  раніше згенеровані рисунки) ідентичні тим, що були б і без i18n узагалі.
* **Відсутній переклад «деградує» безпечно** до вихідного рядка (``_EN.get(s, s)``):
  забули перекласти — отримаєте український підпис, а не ``KeyError`` чи ``"???"``.
* **Нуль інфраструктури** — один Python-файл, жодних білд-кроків.

Оркестратор (скрипти ``examples/``) перемикає мову через :func:`set_lang`
(``"en"`` із аргументів CLI) і кладе рисунки в ``docs/images/en/``. Той самий код
малювання, той самий білдер — змінюється лише глобальний ``LANG``, і всі виклики
:func:`t` всередині повертають переклад. Жодна функція-фігура не знає про мову.

Самі рядки-**дані** мовно нейтральні й **НЕ перекладаються**: шаблони ``"developer"``,
``"jar"`` тощо, головний рядок конспекту (``"Being a developer is not easy"``),
хеш-числа (``90``, ``35``, ``82``, ``6382179``) та **літеральний вивід коду**
(``"Substring found at index 8"``) лишаються незмінними в обох мовах. Перекладаємо
лише **підписи**.

Правила вживання у коді фігур:

* обгортайте **шаблон**, а не результат: ``t("…{x}…").format(x=v)``, ніколи
  ``t(f"…{v}…")`` — інакше ключ щоразу інакший і переклад не знайдеться;
* ключ у :data:`_EN` має збігатися з рядком у коді **символ-у-символ**, включно з
  пробілами, переносами ``\\n``, тире (``–`` en-dash ≠ ``-`` дефіс), стрілками
  (``→``, ``↔``, ``↘``) та позначками ``✓``/``✗``;
* суто символьні/числові рядки (без жодного українського слова — напр.
  ``"h = ord·bⁿ⁻¹"``) у словник НЕ заносимо: :func:`t` поверне їх незмінними.
"""

from __future__ import annotations

import re
from typing import Dict, Set

#: Мова за замовчуванням (= вихідна мова рядків-ключів у коді).
LANG = "uk"

#: Будь-яка кирилична літера — ознака «це український рядок, а не формула/символи».
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")

#: Аудит повноти перекладу: рядки з кирилицею, які в режимі ``en`` НЕ знайшлися в
#: :data:`_EN` (тобто лишилися б українськими). Наповнюється на льоту в :func:`t`;
#: має бути порожнім після повного прогону ``en`` — це й перевіряють тести/збірка.
missing_translations: Set[str] = set()


def set_lang(lang: str) -> None:
    """Встановити мову підписів: ``"uk"`` (типово) або ``"en"``."""
    global LANG
    assert lang in ("uk", "en"), lang
    LANG = lang


def get_lang() -> str:
    """Повернути поточну мову підписів (``"uk"`` або ``"en"``)."""
    return LANG


def t(s: str) -> str:
    """Повернути підпис мовою :data:`LANG` (ключ — вихідний український рядок).

    Для ``LANG == "uk"`` повертає ``s`` без змін (нульовий ризик регресій); для
    ``"en"`` — переклад із :data:`_EN`, а якщо його немає — безпечно сам ``s``.
    Якщо в режимі ``en`` рядок містить кирилицю, але перекладу немає, він
    запам'ятовується в :data:`missing_translations` (мовчазний аудит — не падаємо,
    лише фіксуємо «забутий» ключ).
    """
    if LANG == "uk":
        return s                # мова за замовчуванням: жодного пошуку, байт-у-байт
    out = _EN.get(s)
    if out is None:
        if _CYRILLIC.search(s):
            missing_translations.add(s)   # забутий/неточний ключ — фіксуємо для аудиту
        return s                # відсутній ключ -> безпечно повертаємо вихідний рядок
    return out


# ---------------------------------------------------------------------------
# Словник перекладів (uk -> en).
#
# Згруповано за місцем появи. Шаблони з {плейсхолдерами} перекладені цілком — у
# коді їх викликають як t(шаблон).format(...). НЕ перейменовуйте плейсхолдери:
# їхні імена мусять збігатися з тими, що у виклику .format().
# ---------------------------------------------------------------------------
_EN: Dict[str, str] = {
    # --- visualization: спільні підписи рядків текст/шаблон --------------------
    "текст": "text",
    "шаблон": "pattern",
    "вікно": "window",
    "індекс": "index",
    "шукаємо шаблон: «{p}»": "searching for pattern: «{p}»",
    "хеш": "hash",
    "хеш вікна": "window hash",
    "хеш шаблону": "pattern hash",
    "хеш шаблону = {h}": "pattern hash = {h}",

    # --- visualization: поліноміальний хеш -------------------------------------
    "Поліноміальний хеш рядка «{s}»": "Polynomial hash of «{s}»",
    "Символ": "Symbol",
    "Індекс": "Index",
    "код ord": "code ord",
    "степінь bⁿ⁻ⁱ⁻¹ mod m": "power bⁿ⁻ⁱ⁻¹ mod m",
    "внесок": "contribution",
    "сума за модулем": "sum modulo",
    "база b = {b}, модуль m = {m}": "base b = {b}, modulus m = {m}",
    "h(«{s}») = {raw} = {h} (mod {m})": "h(«{s}») = {raw} = {h} (mod {m})",
    "велике число {raw} → {h} (mod {m})": "big number {raw} → {h} (mod {m})",
    "Крок Horner-акумуляції: i = {i}": "Horner accumulation step: i = {i}",
    "Старт: hash = 0": "Start: hash = 0",
    "Готово: hash = {h}": "Done: hash = {h}",
    "+ ord(«{c}»)·{p} = {contrib}  →  hash = {h}":
        "+ ord(«{c}»)·{p} = {contrib}  →  hash = {h}",

    # --- visualization: ковзне вікно / порівняння хешів ------------------------
    "Вікно на зміщенні {i}: хеш {hw} проти хешу шаблону {hp}":
        "Window at offset {i}: hash {hw} vs pattern hash {hp}",
    "збіг хешу: {hw} = {hp} → перевіряємо символи":
        "hash match: {hw} = {hp} → verify characters",
    "хеші різні: {hw} ≠ {hp} → ковзаємо далі":
        "hashes differ: {hw} ≠ {hp} → slide on",
    "справжній збіг: «{w}» = «{p}» ✓": "real match: «{w}» = «{p}» ✓",
    "КОЛІЗІЯ: хеші рівні ({h}), але «{w}» ≠ «{p}» ✗":
        "COLLISION: equal hashes ({h}), yet «{w}» ≠ «{p}» ✗",

    # --- visualization: rolling-оновлення --------------------------------------
    "Rolling hash: вікно котиться на 1 за O(1)": "Rolling hash: the window rolls by 1 in O(1)",
    "виходить «{c}»": "«{c}» leaves",
    "входить «{c}»": "«{c}» enters",
    "− ord(«{out}»)·{mult}, ×{b}, + ord(«{in}»)  →  {h}":
        "− ord(«{out}»)·{mult}, ×{b}, + ord(«{in}»)  →  {h}",
    "хеш: {a} → {b}": "hash: {a} → {b}",

    # --- visualization: колізія (окремий кадр) ---------------------------------
    "Колізія під (b={b}, m={m}): різні рядки — однаковий хеш":
        "A collision under (b={b}, m={m}): different strings, same hash",
    "однакові рядки → однакові хеші ЗАВЖДИ; однакові хеші → рядки ⟍ не завжди":
        "equal strings → equal hashes ALWAYS; equal hashes → strings not always",
    "ось навіщо потрібна посимвольна перевірка на збігу хешів":
        "this is why a character check is needed when hashes match",

    # --- visualization: rolling проти перерахунку ------------------------------
    "Rolling O(1) проти перерахунку з нуля O(m)": "Rolling O(1) vs recompute-from-scratch O(m)",
    "перерахунок із нуля ≈ n·m": "recompute from scratch ≈ n·m",
    "rolling ≈ n (лінійно)": "rolling ≈ n (linear)",
    "довжина тексту n": "text length n",
    "довжина тексту n (шаблон m ≈ n/2)": "text length n (pattern m ≈ n/2)",
    "символьних операцій хешування": "hashing character operations",

    # --- visualization: складність ---------------------------------------------
    "Скільки char-порівнянь? Рабін-Карп O(n+m) проти O(n·m)":
        "How many char comparisons? Rabin-Karp O(n+m) vs O(n·m)",
    "Рабін-Карп — середній ≈ n + m": "Rabin-Karp — average ≈ n + m",
    "Рабін-Карп — найгірший ≈ n·m (багато колізій)":
        "Rabin-Karp — worst ≈ n·m (many collisions)",
    "кількість порівнянь (приблизно)": "number of comparisons (approx.)",

    # --- visualization: порівняння чотирьох алгоритмів -------------------------
    "Чотири рядкові алгоритми: посимвольні порівняння на «{t}» / «{p}»":
        "Four string algorithms: character comparisons on «{t}» / «{p}»",
    "посимвольних порівнянь": "character comparisons",
    "наївний": "naive",
    "Боєра-Мура": "Boyer-Moore",
    "Рабіна-Карпа (char-перевірки)": "Rabin-Karp (char checks)",

    # --- visualization: підсумкові заголовки / вердикти пошуку -----------------
    "Пошук Рабіна-Карпа: вікна та їхні хеші": "Rabin-Karp search: windows and their hashes",
    "Готово: знайдено на позиції {i}": "Done: found at position {i}",
    "Готово: шаблон відсутній (-1)": "Done: pattern absent (-1)",
    "Шаблон не знайдено": "Pattern not found",
    "порівнянь хешів: {hc} · char-перевірок: {cv} · колізій: {col}":
        "hash comparisons: {hc} · char checks: {cv} · collisions: {col}",
    "порівнянь хешів: {hc} · char-перевірок: {cv} · колізій: {col} · rolling: {r}":
        "hash comparisons: {hc} · char checks: {cv} · collisions: {col} · rolling: {r}",

    # --- visualization: таблиця кроків / друк у консоль ------------------------
    "вердикт": "verdict",
    "хеші різні": "hashes differ",
    "збіг хешу": "hash match",
    "колізія (char-перевірка відкидає)": "collision (char check rejects)",
    "справжній збіг": "real match",
    "Текст:   {s}": "Text:    {s}",
    "Шаблон:  {p}": "Pattern: {p}",
    "Хеш шаблону: {h}": "Pattern hash: {h}",
    "Результат: знайдено на позиції {r}": "Result: found at position {r}",
    "Результат: шаблон не знайдено (-1)": "Result: pattern not found (-1)",

    # --- walkthrough: легенда підсвічування коду -------------------------------
    "активний рядок": "active line",
    "збіг хешу (кандидат)": "hash match (candidate)",
    "підтверджено / знайдено": "confirmed / found",
    "колізія / не знайдено": "collision / not found",
    "rolling-оновлення": "rolling update",

    # --- examples/00_intuition -------------------------------------------------
    "Збережено рисунки інтуїції: рядок → хеш та ідея ковзного вікна.":
        "Saved the intuition figures: string → hash and the sliding-window idea.",

    # --- examples/01_polynomial_hash -------------------------------------------
    "Поліноміальний хеш (рядок → число)": "Polynomial hash (string → number)",
    '«abc» без модуля: ord("a")·256² + ord("b")·256¹ + ord("c")·256⁰ = {a} + {b} + {c} = {raw}':
        '«abc» without the modulus: ord("a")·256² + ord("b")·256¹ + ord("c")·256⁰ = {a} + {b} + {c} = {raw}',
    "Покрокова Horner-акумуляція для «{s}»:":
        "Step-by-step Horner accumulation for «{s}»:",
    "  hash_build: {n} кадрів": "  hash_build: {n} frames",
    "Звірка: polynomial_hash збігається з еталонами конспекту (90, 35, 82) ✓":
        "Cross-check: polynomial_hash matches the konspekt references (90, 35, 82) ✓",

    # --- examples/02_search ----------------------------------------------------
    "Приклад із конспекту: пошук «{p}»": "Konspekt example: searching for «{p}»",
    "Хеш шаблону «{p}»: {h}": "Hash of pattern «{p}»: {h}",
    "Трасування пошуку (одне вікно на рядок):": "Search trace (one window per row):",
    "Пошук відсутнього шаблону «{p}»:": "Searching for the absent pattern «{p}»:",
    "  {name}: {n} кадрів": "  {name}: {n} frames",
    "Звірка: rabin_karp_search == str.find() == {r} ✓":
        "Cross-check: rabin_karp_search == str.find() == {r} ✓",

    # --- examples/03_rolling_collisions ----------------------------------------
    "Rolling hash: O(1)-оновлення проти перерахунку з нуля O(m)":
        "Rolling hash: O(1) update vs recompute-from-scratch O(m)",
    "  n={n:>2}: rolling {roll} символьних операцій, перерахунок {rec}":
        "  n={n:>2}: rolling {roll} character operations, recompute {rec}",
    "Колізії під (base=256, modulus=101): різні рядки — однаковий хеш":
        "Collisions under (base=256, modulus=101): different strings, same hash",
    "  «{a}» і «{b}»: hash = {h} (а рядки різні!)":
        "  «{a}» and «{b}»: hash = {h} (yet the strings differ!)",
    "  скануванням знайдено колізій у вибірці: {k}":
        "  collisions found by scanning the sample: {k}",
    "Пошук «{p}» у «{t}»:": "Searching for «{p}» in «{t}»:",
    "  порівнянь хешів {hc}, char-перевірок {cv}, з них колізій {col}, збіг на {r}":
        "  hash comparisons {hc}, char checks {cv}, collisions among them {col}, match at {r}",
    "Модульна арифметика: навіщо модуль і чому просте число":
        "Modular arithmetic: why a modulus and why a prime",
    "  без модуля хеш «developer» = {raw} (≈ {d} цифр) — переповнення":
        "  without the modulus the hash of «developer» = {raw} (≈ {d} digits) — overflow",
    "    модуль 101 (просте): колізій {c1}, char-порівнянь {cc1} — RK швидкий":
        "    modulus 101 (prime): collisions {c1}, char comparisons {cc1} — RK is fast",
    "    модуль 1 (найгірший): колізій {c2}, char-порівнянь {cc2} — RK = наївний":
        "    modulus 1 (worst): collisions {c2}, char comparisons {cc2} — RK = naive",

    # --- examples/04_complexity ------------------------------------------------
    "Чотири рядкові алгоритми: посимвольні порівняння на тих самих входах":
        "Four string algorithms: character comparisons on the same inputs",
    "вхід": "input",
    "Рабіна-Карпа (char + hash)": "Rabin-Karp (char + hash)",
    "{c} char + {h} hash": "{c} char + {h} hash",
    "конспект «developer»": "konspekt «developer»",
    "патологічний «aaaa…» / «aaaaab»": "pathological «aaaa…» / «aaaaab»",
    "Висновок: Рабін-Карп робить НАЙМЕНШЕ посимвольних порівнянь — бо":
        "Conclusion: Rabin-Karp does the FEWEST character comparisons — because",
    "здебільшого порівнює ХЕШІ (цілі числа), а символи звіряє лише на збігу хешів.":
        "it mostly compares HASHES (integers) and checks characters only when hashes match.",

    # --- examples/05_code_walkthrough ------------------------------------------
    "Генерую покрокові панелі «код ↔ дані»…": "Generating step-by-step code ↔ data panels…",
    "Поліноміальний хеш «abc»: код ↔ накопичений хеш":
        "Polynomial hash of «abc»: code ↔ accumulated hash",
    "Пошук «jar» у «for jar»: код ↔ ковзне вікно":
        "Searching for «jar» in «for jar»: code ↔ sliding window",
    "  {name}: сітка, {n} рядків": "  {name}: grid, {n} rows",
    "  {name}: анімація, {n} кадрів": "  {name}: animation, {n} frames",

    # --- animation.save_animation (діагностика MP4, рідкісні шляхи) ------------
    "  ({name} пропущено — ffmpeg недоступний; pip install imageio-ffmpeg для відео)":
        "  ({name} skipped — ffmpeg unavailable; pip install imageio-ffmpeg for video)",
    "  ({name} пропущено: {err})": "  ({name} skipped: {err})",

    # --- _common.print_saved_location ------------------------------------------
    "\nРисунки збережено у: {path}": "\nFigures saved to: {path}",
}
