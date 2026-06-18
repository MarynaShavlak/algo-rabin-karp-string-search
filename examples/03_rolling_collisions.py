"""Приклад 3 — ROLLING HASH, КОЛІЗІЇ та модульна арифметика.

Три сюжети, що роблять Рабіна-Карпа собою:

1. **Rolling hash** (:math:`O(1)`-оновлення) проти перерахунку хешу вікна **з нуля**
   (:math:`O(m)`): графік прискорення + один кадр кроку оновлення (лівий символ
   виходить, правий входить);
2. **Колізії** — унікальна перлина: різні рядки з однаковим хешем. Показуємо
   знайдену скануванням пару (``"for"`` і ``"jar"`` → обидва ``35``) **і** колізію
   **під час пошуку** (вікно ``"for"`` має хеш шаблону ``"jar"``, але це не ``"jar"``
   → char-перевірка відкидає) — ось навіщо перевірка;
3. **Модульна арифметика** — навіщо модуль (уникнути переповнення) і чому **просте**
   число: малий/невдалий модуль → багато колізій → RK вироджується в наївний.

Зберігає графіки/кадри й збирає анімації колізії та найгіршого випадку.

Запуск:  ``python examples/03_rolling_collisions.py``      (українською → docs/images/)
         ``python examples/03_rolling_collisions.py en``   (англійською → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, save_anim, save_figure
from _searches import (
    COLLISION_FOR_JAR,
    COLLISION_HEAP_USER,
    SEARCH_COLLISION,
    SEARCH_WORST,
)

from rabin_karp_string_search.core import (  # noqa: E402
    count_hash_char_ops,
    find_collisions,
    polynomial_hash,
    polynomial_hash_raw,
    rabin_karp_metrics,
    rabin_karp_search_steps,
)
from rabin_karp_string_search.i18n import t  # noqa: E402
from rabin_karp_string_search.visualization import (  # noqa: E402
    configure_style,
    draw_collision,
    draw_rolling_update,
    draw_rolling_vs_recompute,
    draw_rolling_window,
    draw_search_evolution,
)

_DUR = {"init": 1300, "window": 700, "hash_match": 1100, "verify": 1300,
        "collision": 1900, "match_found": 2600, "roll": 600, "not_found": 2400}


def _animate(text, pattern, name, *, modulus=101):
    _, events = rabin_karp_search_steps(text, pattern, modulus=modulus)
    frames_ev = [e for e in events if e["kind"] != "final"]
    figures = [draw_rolling_window(e) for e in frames_ev]
    durations = [_DUR.get(e["kind"], 700) for e in frames_ev]
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів").format(name=name, n=len(figures)))


def main() -> None:
    configure_style()

    # === 1) ROLLING HASH проти перерахунку з нуля ============================
    print(t("Rolling hash: O(1)-оновлення проти перерахунку з нуля O(m)"))
    for n in (8, 16, 32, 64):
        roll = count_hash_char_ops("a" * n, "abcd", rolling=True)
        recompute = count_hash_char_ops("a" * n, "abcd", rolling=False)
        print(t("  n={n:>2}: rolling {roll} символьних операцій, перерахунок {rec}").format(
            n=n, roll=roll, rec=recompute))
    print()
    save_figure(draw_rolling_vs_recompute("abcd"), "rolling_vs_recompute.png")

    # один кадр rolling-оновлення (з конспект-пошуку)
    _, kev = rabin_karp_search_steps("Being a developer is not easy", "developer")
    roll_ev = next(e for e in kev if e["kind"] == "roll")
    save_figure(draw_rolling_update(roll_ev), "rolling_update.png")

    # === 2) КОЛІЗІЇ =========================================================
    print(t("Колізії під (base=256, modulus=101): різні рядки — однаковий хеш"))
    for cc in (COLLISION_FOR_JAR, COLLISION_HEAP_USER):
        print(t('  «{a}» і «{b}»: hash = {h} (а рядки різні!)').format(
            a=cc.s1, b=cc.s2, h=cc.hash))
        assert polynomial_hash(cc.s1) == polynomial_hash(cc.s2) == cc.hash
        assert cc.s1 != cc.s2 and len(cc.s1) == len(cc.s2)
    print()

    # знаходимо колізії скануванням — підтверджуємо, що пари не випадкові
    sample = ["for", "jar", "cat", "dog", "art", "the", "sea", "she", "run", "sun"]
    found = [(a, b, h) for a, b, h in find_collisions(sample) if len(a) == len(b)]
    print(t("  скануванням знайдено колізій у вибірці: {k}").format(k=len(found)))
    print()

    save_figure(draw_collision(COLLISION_FOR_JAR.s1, COLLISION_FOR_JAR.s2),
                "collision_for_jar.png")
    save_figure(draw_collision(COLLISION_HEAP_USER.s1, COLLISION_HEAP_USER.s2),
                "collision_heap_user.png")

    # колізія ПІД ЧАС ПОШУКУ: «for» має хеш «jar», але char-перевірка відкидає
    _, cev = rabin_karp_search_steps(SEARCH_COLLISION.text, SEARCH_COLLISION.pattern)
    save_figure(draw_search_evolution(cev), "search_collision.png")
    m = rabin_karp_metrics(SEARCH_COLLISION.text, SEARCH_COLLISION.pattern)
    print(t("Пошук «{p}» у «{t}»:").format(p=SEARCH_COLLISION.pattern, t=SEARCH_COLLISION.text))
    print(t("  порівнянь хешів {hc}, char-перевірок {cv}, з них колізій {col}, збіг на {r}").format(
        hc=m["hash_comparisons"], cv=m["char_verifications"], col=m["collisions"],
        r=SEARCH_COLLISION.expected))
    print()

    # === 3) МОДУЛЬНА АРИФМЕТИКА =============================================
    print(t("Модульна арифметика: навіщо модуль і чому просте число"))
    print(t("  без модуля хеш «developer» = {raw} (≈ {d} цифр) — переповнення").format(
        raw=polynomial_hash_raw("developer"), d=len(str(polynomial_hash_raw("developer")))))
    # вплив модуля: добрий простий 101 проти найгіршого 1
    good = rabin_karp_metrics(SEARCH_WORST.text, SEARCH_WORST.pattern, modulus=101)
    bad = rabin_karp_metrics(SEARCH_WORST.text, SEARCH_WORST.pattern, modulus=1)
    print(t("  «{t}» / «{p}»:").format(t=SEARCH_WORST.text, p=SEARCH_WORST.pattern))
    print(t("    модуль 101 (просте): колізій {c1}, char-порівнянь {cc1} — RK швидкий").format(
        c1=good["collisions"], cc1=good["char_comparisons"]))
    print(t("    модуль 1 (найгірший): колізій {c2}, char-порівнянь {cc2} — RK = наївний").format(
        c2=bad["collisions"], cc2=bad["char_comparisons"]))
    print()

    # === анімації ==========================================================
    _animate(SEARCH_COLLISION.text, SEARCH_COLLISION.pattern, "search_collision")
    _animate(SEARCH_WORST.text, SEARCH_WORST.pattern, "search_worst", modulus=1)

    print_saved_location()


if __name__ == "__main__":
    main()
