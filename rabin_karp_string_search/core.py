"""Реалізації алгоритму Рабіна-Карпа (Rabin-Karp) для пошуку в рядках.

Задача рядкового пошуку та сама, що й у попередніх алгоритмах серії
([наївному](https://github.com/MarynaShavlak/algo-naive-string-search),
[KMP](https://github.com/MarynaShavlak/algo-knuth-morris-pratt-search),
[Боєра-Мура](https://github.com/MarynaShavlak/algo-boyer-moore-string-search)):
знайти, з якої позиції **шаблон** (``substring``, підрядок) входить у **головний
рядок** (``main_string``, текст). Але Рабін-Карп робить це принципово інакше: він
порівнює **не символи, а ХЕШІ** (числа).

Головна ідея — **віконний підхід**: вікно завдовжки з шаблон ковзає вздовж тексту,
і для кожного вікна порівнюється його **хеш** із хешем шаблону. Порівняти два цілі
числа дешево; **посимвольну** перевірку роблять лише тоді, коли хеші **збіглися**
(бо різні рядки можуть мати однаковий хеш — це **колізія**). Два нові герої:

1. **Поліноміальний хеш** — рядок перетворюється на число:
   :math:`h(s) = \\sum_{i=0}^{n-1} s[i]\\cdot b^{\\,n-i-1} \\bmod m`, де ``s[i]`` —
   код символу (``ord``), ``b`` — база (тут 256), ``m`` — модуль (тут просте 101).
2. **Ковзний хеш (rolling hash)** — хеш наступного вікна перераховується за
   :math:`O(1)`: відняти внесок старого (лівого) символу, помножити на базу,
   додати новий (правий) символ — замість перерахунку з нуля за :math:`O(m)`.

Модуль містить кілька рівнів реалізації — від базової «з конспекту» до
навчально-інструментованої:

* :func:`polynomial_hash` — поліноміальний хеш рядка (код з конспекту).
* :func:`rabin_karp_search` — базова реалізація пошуку з конспекту: повертає
  **позицію** першого входження шаблону (або ``-1``). Саме її код розібрано в
  README рядок за рядком.
* :func:`rabin_karp_search_all` — **усі** позиції входжень (природна сила RK).
* :func:`rabin_karp_search_recompute` — той самий пошук, але хеш вікна щоразу
  рахується **з нуля** (без rolling) — для контрасту :math:`O(n\\cdot m)` проти
  :math:`O(n)` на хешуванні.
* :func:`polynomial_hash_steps` / :func:`rabin_karp_search_steps` — інструментовані
  версії для покрокового розбору. Повторюють логіку базових реалізацій **дія в
  дію**, але дорогою кладуть у **журнал подій** знімок стану разом із лічильниками.
  Саме їх використовують візуалізації.

Допоміжні утиліти: :func:`rabin_karp_metrics` (порівняння хешів / char-перевірки /
колізії / rolling-оновлення без журналу), :func:`count_hash_char_ops` (вартість
хешування rolling проти recompute) і **лічильники посимвольних порівнянь** інших
трьох алгоритмів серії — :func:`count_naive_comparisons`,
:func:`count_kmp_comparisons`, :func:`count_boyer_moore_comparisons` — для
підсумкового порівняння **чотирьох** рядкових алгоритмів. Нарешті,
:func:`find_collisions` сканує простір рядків і знаходить **конкретні колізії** під
фіксованими ``(256, 101)``.

Цей модуль НЕ залежить від ``matplotlib`` — ``import rabin_karp_string_search``
лишається легким.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

#: Один запис журналу подій (:func:`polynomial_hash_steps` / :func:`rabin_karp_search_steps`).
Event = Dict[str, object]


# ===========================================================================
# Поліноміальний хеш — рядок → число
# ===========================================================================
def polynomial_hash(s, base=256, modulus=101):
    """
    Повертає поліноміальний хеш рядка s.
    """
    n = len(s)
    hash_value = 0
    for i, char in enumerate(s):
        power_of_base = pow(base, n - i - 1) % modulus
        hash_value = (hash_value + ord(char) * power_of_base) % modulus
    return hash_value


def polynomial_hash_raw(s, base=256):
    """Поліноміальний хеш **без модуля** — «справжнє» велике число рядка.

    Це :math:`\\sum_i s[i]\\cdot b^{\\,n-i-1}` без узяття залишку: саме його конспект
    наводить для ``"abc"`` (``6382179``), перш ніж пояснити, **навіщо** модуль.
    На довгих рядках число росте експоненційно — звідси й потреба в модулі, щоб
    уникнути переповнення; :func:`polynomial_hash` бере цей самий вираз ``% modulus``.
    """
    n = len(s)
    return sum(ord(c) * base ** (n - i - 1) for i, c in enumerate(s))


def polynomial_hash_steps(s, base=256, modulus=101) -> "tuple[int, List[Event]]":
    """Інструментований поліноміальний хеш для покрокового розбору (Horner-акумуляція).

    Повторює :func:`polynomial_hash` **дія в дію** — той самий цикл по символах —
    але дорогою кладе у журнал знімок кожного доданка. Рядок не змінюється;
    накопичується лише ``hash_value``.

    :returns: кортеж ``(hash, events)``, де ``hash`` — підсумковий хеш ``% modulus``,
        а ``events`` — журнал подій. Типи подій (поле ``kind``):

        * ``"init"`` — стартовий знімок (рядок ``s``, ``base``, ``modulus``, ``n``;
          ``hash_value = 0``);
        * ``"term"`` — один доданок: символ ``char`` на позиції ``i``, його код
          ``ord(char)``, степінь ``power = pow(base, n-i-1) % modulus``, внесок
          ``contribution = ord(char) * power`` і поточний (після ``% modulus``)
          ``hash_value``;
        * ``"final"`` — підсумок (``hash``).

        Спільні поля будь-якої події: ``s`` / ``base`` / ``modulus`` / ``n`` (незмінні),
        ``i`` (позиція символу або ``None``), ``char`` / ``code`` (символ і його ``ord``),
        ``power`` (степінь бази за модулем), ``contribution`` (внесок ``code*power``),
        ``hash_value`` (накопичений хеш на цей момент) та ``raw`` (внесок без модуля —
        для зв'язку з «великим числом» ``polynomial_hash_raw``).
    """
    n = len(s)
    hash_value = 0

    def snapshot(kind: str, *, i=None, char=None, code=None, power=None,
                 contribution=None, raw=None) -> Event:
        return {
            "kind": kind,
            "phase": "hash",
            "s": s,
            "base": base,
            "modulus": modulus,
            "n": n,
            "i": i,
            "char": char,
            "code": code,
            "power": power,
            "contribution": contribution,
            "raw": raw,
            "hash_value": hash_value,
        }

    events: List[Event] = [snapshot("init")]

    for i, char in enumerate(s):
        power_of_base = pow(base, n - i - 1) % modulus
        code = ord(char)
        contribution = code * power_of_base
        hash_value = (hash_value + contribution) % modulus
        events.append(snapshot(
            "term", i=i, char=char, code=code, power=power_of_base,
            contribution=contribution, raw=code * base ** (n - i - 1)))

    events.append(snapshot("final"))
    return hash_value, events


# ===========================================================================
# Пошук Рабіна-Карпа — ковзне вікно, порівняння хешів, char-підтвердження
# ===========================================================================
def rabin_karp_search(main_string, substring):
    # Довжини основного рядка та підрядка пошуку
    substring_length = len(substring)
    main_string_length = len(main_string)
    # Базове число для хешування та модуль
    base = 256
    modulus = 101
    # Хеш-значення для підрядка пошуку та поточного відрізка в основному рядку
    substring_hash = polynomial_hash(substring, base, modulus)
    current_slice_hash = polynomial_hash(main_string[:substring_length], base, modulus)
    # Попереднє значення для перерахунку хешу
    h_multiplier = pow(base, substring_length - 1) % modulus
    # Проходимо крізь основний рядок
    for i in range(main_string_length - substring_length + 1):
        if substring_hash == current_slice_hash:
            if main_string[i:i+substring_length] == substring:
                return i
        if i < main_string_length - substring_length:
            current_slice_hash = (current_slice_hash - ord(main_string[i]) * h_multiplier) % modulus
            current_slice_hash = (current_slice_hash * base + ord(main_string[i + substring_length])) % modulus
            if current_slice_hash < 0:
                current_slice_hash += modulus
    return -1


def rabin_karp_search_all(main_string, substring, base=256, modulus=101):
    """Усі позиції входжень ``substring`` у ``main_string`` (а не лише перша).

    Базовий :func:`rabin_karp_search` зупиняється на **першому** збігу. Тут після
    кожного підтвердженого збігу позиція фіксується, і вікно ковзає далі — це
    **природна сила** Рабіна-Карпа: знайти багато входжень одним проходом, лишаючи
    хеш-порівняння дешевими. Як і базова версія, на **збігу хешів** робить
    посимвольну перевірку (через колізії).

    Повертає список позицій (порожній, якщо входжень немає). Для **порожнього
    шаблону** безпечно повертає ``[0, 1, …, N]`` (порожній рядок «міститься» на
    кожній позиції), не чіпаючи проблемний ``pow(base, -1)``.
    """
    m = len(substring)
    n = len(main_string)
    if m == 0:
        return list(range(n + 1))
    if m > n:
        return []

    substring_hash = polynomial_hash(substring, base, modulus)
    current = polynomial_hash(main_string[:m], base, modulus)
    h_multiplier = pow(base, m - 1) % modulus

    positions: List[int] = []
    for i in range(n - m + 1):
        if substring_hash == current:
            if main_string[i:i + m] == substring:
                positions.append(i)        # збіг: фіксуємо й ковзаємо далі (не виходимо)
        if i < n - m:
            current = (current - ord(main_string[i]) * h_multiplier) % modulus
            current = (current * base + ord(main_string[i + m])) % modulus
            if current < 0:
                current += modulus
    return positions


def rabin_karp_search_recompute(main_string, substring, base=256, modulus=101):
    """Той самий пошук, але хеш вікна щоразу рахується **З НУЛЯ** (без rolling).

    Єдина відмінність від :func:`rabin_karp_search`: замість :math:`O(1)`-оновлення
    ``current_slice_hash`` ми щоразу викликаємо :func:`polynomial_hash` для всього
    вікна — це :math:`O(m)` на кожне зміщення, тобто :math:`O(n\\cdot m)` лише на
    хешуванні. Версія існує **для контрасту**: показати, скільки економить rolling
    hash. Результат **збігається** з :func:`rabin_karp_search`.
    """
    m = len(substring)
    n = len(main_string)
    for i in range(n - m + 1):
        if polynomial_hash(main_string[i:i + m], base, modulus) == \
                polynomial_hash(substring, base, modulus):
            if main_string[i:i + m] == substring:
                return i
    return -1


def rabin_karp_search_steps(main_string, substring, base=256, modulus=101
                            ) -> "tuple[int, List[Event]]":
    """Інструментований пошук Рабіна-Карпа для покрокового розбору.

    Повторює :func:`rabin_karp_search` **дія в дію** — той самий обхід вікон,
    порівняння хешів, посимвольні підтвердження й rolling-оновлення — але дорогою
    кладе у журнал знімки стану. Текст і шаблон **не змінюються**; рухається вікно,
    «котиться» його хеш ``current_slice_hash``.

    Параметри ``base`` / ``modulus`` винесено в аргументи (на відміну від
    дослівного :func:`rabin_karp_search`, де вони фіксовані ``256`` / ``101``), щоб
    демонструвати **вплив модуля**: на малому модулі хеші збігаються майже всюди й
    алгоритм вироджується в наївний (багато колізій → багато char-перевірок).

    :returns: кортеж ``(result, events)``, де ``result`` — позиція першого
        входження або ``-1``, а ``events`` — журнал подій. Типи подій (поле ``kind``):

        * ``"init"`` — стартовий знімок: текст, шаблон, ``base``, ``modulus``,
          ``pattern_hash``, ``h_multiplier`` і хеш **першого** вікна;
        * ``"window"`` — вікно стало на зміщення ``i``: його текст і
          ``current_slice_hash`` (кожна подія збільшує ``hash_comparisons`` на 1 —
          ми порівнюємо хеш вікна з хешем шаблону);
        * ``"hash_match"`` — хеші **рівні** на зміщенні ``i`` (дешеве порівняння
          цілих спрацювало);
        * ``"verify"`` — посимвольна перевірка ``main_string[i:i+m] == substring``:
          поле ``confirmed`` каже, це **справжній збіг** чи **колізія** (збільшує
          ``char_verifications`` на 1);
        * ``"collision"`` — хеші рівні, але рядки **різні** (``confirmed = False``):
          char-перевірка **рятує** від хибного збігу, ковзаємо далі
          (``collisions += 1``);
        * ``"match_found"`` — підтверджений збіг на зміщенні ``i``, повертаємо ``i``;
        * ``"roll"`` — ковзне :math:`O(1)`-оновлення: віднімаємо внесок лівого
          символу (``ord(out_char) * h_multiplier``), множимо на ``base``, додаємо
          правий символ (``ord(in_char)``), беремо ``% modulus`` (``rolls += 1``);
        * ``"not_found"`` — жодне вікно не дало підтвердженого збігу (``-1``);
        * ``"final"`` — підсумок (``result`` і всі лічильники).

        Спільні поля будь-якої події: ``text`` / ``pattern`` (незмінні),
        ``base`` / ``modulus`` / ``N`` / ``M``, ``pattern_hash``, ``h_multiplier``,
        ``i`` (зміщення вікна), ``window`` (його текст), ``window_hash``
        (``current_slice_hash`` — **інваріант:** дорівнює
        ``polynomial_hash(window)``), лічильники ``hash_comparisons`` /
        ``char_verifications`` / ``collisions`` / ``rolls`` та ``result``.
        Подія ``roll`` додатково несе ``out_char`` / ``in_char`` (символи, що
        виходять/входять), ``removed`` (віднятий внесок), ``hash_before`` /
        ``hash_after`` (хеш до й після оновлення).

        **Порожній шаблон** (``M == 0``) обробляється безпечно (збіг на ``0`` без
        проблемного ``pow(base, -1)``), на відміну від дослівного
        :func:`rabin_karp_search`.
    """
    M = len(substring)
    N = len(main_string)

    hash_comparisons = 0
    char_verifications = 0
    collisions = 0
    rolls = 0

    pattern_hash = polynomial_hash(substring, base, modulus) if M else 0
    h_multiplier = pow(base, M - 1) % modulus if M else 0
    window_hash = polynomial_hash(main_string[:M], base, modulus) if M <= N else 0

    def snapshot(kind: str, *, i=None, window=None, confirmed=None,
                 out_char=None, in_char=None, removed=None,
                 hash_before=None, hash_after=None, result=None) -> Event:
        return {
            "kind": kind,
            "phase": "search",
            "text": main_string,
            "pattern": substring,
            "base": base,
            "modulus": modulus,
            "N": N,
            "M": M,
            "pattern_hash": pattern_hash,
            "h_multiplier": h_multiplier,
            "i": i,
            "window": window,
            "window_hash": window_hash,
            "out_char": out_char,
            "in_char": in_char,
            "removed": removed,
            "hash_before": hash_before,
            "hash_after": hash_after,
            "hash_comparisons": hash_comparisons,
            "char_verifications": char_verifications,
            "collisions": collisions,
            "rolls": rolls,
            "result": result,
        }

    events: List[Event] = [snapshot("init")]

    # Порожній шаблон: безпечна обробка (дослівний rabin_karp_search спіткнувся б
    # на pow(base, -1) — float — і повернув би 0 лише випадково).
    if M == 0:
        events.append(snapshot("match_found", i=0, window="", result=0))
        events.append(snapshot("final", result=0))
        return 0, events
    if M > N:
        events.append(snapshot("not_found", result=-1))
        events.append(snapshot("final", result=-1))
        return -1, events

    result = -1
    for i in range(N - M + 1):
        window = main_string[i:i + M]
        events.append(snapshot("window", i=i, window=window))
        hash_comparisons += 1
        if pattern_hash == window_hash:
            events.append(snapshot("hash_match", i=i, window=window))
            char_verifications += 1
            confirmed = window == substring
            events.append(snapshot("verify", i=i, window=window, confirmed=confirmed))
            if confirmed:
                result = i
                events.append(snapshot("match_found", i=i, window=window, result=i))
                break
            collisions += 1
            events.append(snapshot("collision", i=i, window=window, confirmed=False))
        if i < N - M:
            out_char = main_string[i]
            in_char = main_string[i + M]
            removed = ord(out_char) * h_multiplier
            hash_before = window_hash
            new_hash = (window_hash - removed) % modulus
            new_hash = (new_hash * base + ord(in_char)) % modulus
            if new_hash < 0:
                new_hash += modulus
            window_hash = new_hash
            rolls += 1
            events.append(snapshot(
                "roll", i=i, out_char=out_char, in_char=in_char, removed=removed,
                hash_before=hash_before, hash_after=new_hash))

    if result < 0:
        events.append(snapshot("not_found", result=-1))
    events.append(snapshot("final", result=result))
    return result, events


# ===========================================================================
# Лічильники / метрики (без журналу) — для таблиць «ціни» та графіків
# ===========================================================================
def rabin_karp_metrics(main_string, substring, base=256, modulus=101) -> Dict[str, int]:
    """«Ціна» пошуку Рабіна-Карпа у числах (через :func:`rabin_karp_search_steps`).

    :returns: словник із ключами:

        * ``hash_comparisons`` — скільки разів порівнювали хеш вікна з хешем шаблону
          (дешеві порівняння цілих) ``= N - M + 1`` (до першого збігу);
        * ``char_verifications`` — скільки разів робили **посимвольну** перевірку
          (лише на збігу хешів);
        * ``collisions`` — скільки з них були **колізіями** (хеші рівні, рядки різні);
        * ``rolls`` — скільки **ковзних оновлень** хешу;
        * ``char_comparisons`` — сумарно порівняно **символів** під час перевірок
          (саме цей лічильник зіставляється з наївним / KMP / Боєра-Мура).
    """
    _, events = rabin_karp_search_steps(main_string, substring, base, modulus)
    last = events[-1]
    char_comparisons = 0
    for e in events:
        if e["kind"] == "verify":
            window = str(e["window"])
            # посимвольне == порівнює символи зліва направо до першої розбіжності
            matched = 0
            for a, b in zip(window, substring):
                matched += 1
                if a != b:
                    break
            char_comparisons += matched
    return {
        "hash_comparisons": int(last["hash_comparisons"]),
        "char_verifications": int(last["char_verifications"]),
        "collisions": int(last["collisions"]),
        "rolls": int(last["rolls"]),
        "char_comparisons": char_comparisons,
    }


def count_hash_char_ops(main_string, substring, *, rolling: bool,
                        base=256, modulus=101) -> int:
    """Скільки «символьних операцій» коштує **хешування вікон** (rolling чи з нуля).

    Це й є контраст ефективності rolling hash:

    * ``rolling=True`` — :math:`O(1)` на крок: ``M`` операцій на стартове вікно
      плюс по одній парі (вийшов / зайшов символ) на кожне з ``N - M`` оновлень
      → лінійно за ``N``;
    * ``rolling=False`` — перерахунок із нуля: по ``M`` операцій на кожне з
      ``N - M + 1`` вікон → :math:`O(n\\cdot m)`.

    Лічильник навмисно простий (рахує оброблені символи), щоб графік «rolling проти
    перерахунку» спирався на ту саму величину, що й текст README.
    """
    m = len(substring)
    n = len(main_string)
    if m == 0 or m > n:
        return 0
    windows = n - m + 1
    if rolling:
        return m + 2 * (windows - 1)     # стартове вікно (m) + по 2 символи на оновлення
    return m * windows                   # повний перерахунок кожного вікна


# ===========================================================================
# Лічильники посимвольних порівнянь інших трьох алгоритмів серії
# (для ПІДСУМКОВОГО порівняння ЧОТИРЬОХ рядкових алгоритмів)
# ===========================================================================
def count_naive_comparisons(main_string, pattern) -> int:
    """Посимвольні порівняння **наївного** методу (``main_string[i+j] == pattern[j]``).

    Для кожного зміщення ``i`` звіряємо символи зліва направо, доки збігаються; на
    розбіжності зсуваємо шаблон на 1. У найгіршому випадку
    :math:`\\approx (N-M+1)\\cdot M`. Потрібен лише для **контрасту** з Рабіном-Карпом.
    """
    M = len(pattern)
    N = len(main_string)
    if M == 0:
        return 0
    comparisons = 0
    for i in range(N - M + 1):
        j = 0
        while j < M:
            comparisons += 1
            if main_string[i + j] != pattern[j]:
                break
            j += 1
    return comparisons


def _compute_lps(pattern):
    """Префіксна функція KMP (для лічильника порівнянь — серце KMP розібрано окремо)."""
    lps = [0] * len(pattern)
    length = 0
    i = 1
    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length != 0:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    return lps


def count_kmp_comparisons(main_string, pattern) -> int:
    """Посимвольні порівняння **KMP** (передобробка ``lps`` + один прохід тексту).

    KMP лінійний: індекс тексту ніколи не відкочується. Рахуємо порівняння обох
    фаз — для контрасту з Рабіном-Карпом. Потрібен лише для **порівняльного графіка**.
    """
    M = len(pattern)
    N = len(main_string)
    if M == 0:
        return 0
    comparisons = 0
    # фаза 1: побудова lps
    lps = [0] * M
    length = 0
    i = 1
    while i < M:
        comparisons += 1
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        elif length != 0:
            length = lps[length - 1]
        else:
            lps[i] = 0
            i += 1
    # фаза 2: пошук
    i = j = 0
    while i < N:
        comparisons += 1
        if pattern[j] == main_string[i]:
            i += 1
            j += 1
            if j == M:
                return comparisons
        elif j != 0:
            j = lps[j - 1]
        else:
            i += 1
    return comparisons


def count_boyer_moore_comparisons(main_string, pattern) -> int:
    """Посимвольні порівняння **Боєра-Мура** (порівняння з кінця + таблиця поганого символу).

    Боєр-Мур звіряє шаблон **справа наліво** й на розбіжності стрибає за «поганим
    символом». Швидкий на практиці, хоча найгірший випадок лишається
    :math:`O(n\\cdot m)`. Рахуємо порівняння для контрасту з Рабіном-Карпом.
    Потрібен лише для **порівняльного графіка**.
    """
    M = len(pattern)
    N = len(main_string)
    if M == 0 or M > N:
        return 0
    # таблиця поганого символу: остання позиція кожного символу в шаблоні
    last = {pattern[k]: k for k in range(M)}
    comparisons = 0
    s = 0                                # зміщення шаблону вздовж тексту
    while s <= N - M:
        j = M - 1
        while j >= 0:
            comparisons += 1
            if pattern[j] != main_string[s + j]:
                break
            j -= 1
        if j < 0:
            return comparisons           # повний збіг
        bad = last.get(main_string[s + j], -1)
        s += max(1, j - bad)
    return comparisons


# ===========================================================================
# Колізії: сканування простору рядків під фіксованими (256, 101)
# ===========================================================================
def find_collisions(words, base=256, modulus=101) -> List[Tuple[str, str, int]]:
    """Знаходить **колізії** серед ``words``: пари різних рядків **однакової довжини**
    з однаковим :func:`polynomial_hash` під ``(base, modulus)``.

    Однакові рядки дають однакові хеші **завжди**; але однакові хеші **не** означають
    однакові рядки — саме це й шукаємо. Параметри фіксовані (256, 101), тож колізію
    знаходимо **скануванням** простору рядків. Повертає список ``(s1, s2, hash)`` —
    показує, чому на збігу хешів обов'язкова посимвольна перевірка.
    """
    from collections import defaultdict
    buckets: Dict[Tuple[int, int], List[str]] = defaultdict(list)
    for w in words:
        buckets[(len(w), polynomial_hash(w, base, modulus))].append(w)
    pairs: List[Tuple[str, str, int]] = []
    for (length, h), group in buckets.items():
        uniq = sorted(set(group))
        for a in range(len(uniq)):
            for b in range(a + 1, len(uniq)):
                pairs.append((uniq[a], uniq[b], h))
    return pairs
