"""Smoke-тести візуалізацій Рабіна-Карпа.

Не перевіряють «красу» рисунків — лише що **весь конвеєр малювання й збірки
анімацій виконується без помилок**, а двомовність повна:

* кожна функція малювання (поліноміальний хеш, ковзне вікно, rolling-оновлення,
  колізія, еволюція пошуку, порівняння чотирьох, криві складності, rolling проти
  перерахунку) повертає ``Figure`` без винятків;
* збірка **GIF** із кількох кадрів проходить (Pillow);
* панелі «код ↔ дані» (обидві функції) рендеряться, а сітки складаються;
* **інваріант повного трасування** (приклад 06): кількість і порядок кадрів обох
  фаз збігаються з журналами подій;
* **аудит i18n**: після повного прогону в режимі ``en`` усі кириличні підписи
  мають переклад (``missing_translations`` порожній) — інакше рисунок вийшов би
  українським.

Запуск::

    pytest tests/test_smoke.py
    python tests/test_smoke.py     # без pytest (вбудований раннер)
"""

from __future__ import annotations

import os
import sys
import tempfile

import matplotlib

matplotlib.use("Agg")  # без графічного дисплея
import matplotlib.pyplot as plt  # noqa: E402

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "examples")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rabin_karp_string_search.animation import save_gif  # noqa: E402
from rabin_karp_string_search.core import (  # noqa: E402
    polynomial_hash_steps,
    rabin_karp_search_steps,
)
from rabin_karp_string_search import i18n  # noqa: E402
from rabin_karp_string_search.i18n import set_lang  # noqa: E402
from rabin_karp_string_search.visualization import (  # noqa: E402
    configure_style,
    draw_collision,
    draw_compare_four,
    draw_complexity,
    draw_hash_build_step,
    draw_hash_compare,
    draw_polynomial_hash,
    draw_rolling_update,
    draw_rolling_vs_recompute,
    draw_rolling_window,
    draw_search_evolution,
    search_step_caption,
    search_step_title,
    hash_step_caption,
    hash_step_title,
)
from rabin_karp_string_search.walkthrough import (  # noqa: E402
    build_hash_steps,
    build_search_steps,
    draw_code_walkthrough_grid,
    pick_illustrative,
    render_code_step,
)
from _searches import RAW, KONSPECT_PATTERN, SEARCH_COLLISION  # noqa: E402

configure_style()


def _close(fig):
    assert fig is not None
    plt.close(fig)


# ---------------------------------------------------------------------------
# Рендер усіх фігур
# ---------------------------------------------------------------------------
def test_polynomial_hash_figures_render():
    """Сигнатурний кадр хешу та кроки Horner-акумуляції малюються без помилок."""
    _close(draw_polynomial_hash("abc"))
    _close(draw_polynomial_hash("developer"))
    _, events = polynomial_hash_steps("developer")
    for e in events:
        _close(draw_hash_build_step(e))


def test_search_figures_render():
    """Ковзне вікно, rolling-оновлення, порівняння хешів, еволюція — малюються."""
    _, events = rabin_karp_search_steps(RAW, KONSPECT_PATTERN)
    for e in events:
        if e["kind"] in ("window", "hash_match", "collision", "match_found"):
            _close(draw_rolling_window(e))
        if e["kind"] == "roll":
            _close(draw_rolling_update(e))
        if e["kind"] == "hash_match":
            _close(draw_hash_compare(e))
    _close(draw_search_evolution(events))


def test_collision_and_summary_figures_render():
    """Колізія, порівняння чотирьох, криві складності, rolling проти перерахунку."""
    _close(draw_collision("for", "jar"))
    _close(draw_collision("heap", "user"))
    _close(draw_compare_four(RAW, KONSPECT_PATTERN))
    _close(draw_complexity())
    _close(draw_rolling_vs_recompute("abcd"))
    _, cev = rabin_karp_search_steps(SEARCH_COLLISION.text, SEARCH_COLLISION.pattern)
    _close(draw_search_evolution(cev))


# ---------------------------------------------------------------------------
# Панелі «код ↔ дані» та збірка GIF
# ---------------------------------------------------------------------------
def test_walkthrough_renders():
    """Панелі «код ↔ дані» обох функцій: окремі кадри й повні сітки."""
    hsteps = build_hash_steps("abc")
    ssteps = build_search_steps("for jar", "jar")
    for s in hsteps + ssteps:
        _close(render_code_step(s))
    _close(draw_code_walkthrough_grid(pick_illustrative(hsteps), "hash"))
    _close(draw_code_walkthrough_grid(pick_illustrative(ssteps), "search"))


def test_gif_build():
    """Збірка GIF із кількох кадрів проходить і створює файл."""
    _, events = rabin_karp_search_steps("for a jar of jam", "jar")
    figs = [draw_rolling_window(e) for e in events if e["kind"] in ("window", "collision", "match_found")]
    assert len(figs) >= 2
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "smoke.gif")
        save_gif(figs, path, durations=200)
        assert os.path.exists(path) and os.path.getsize(path) > 0


# ---------------------------------------------------------------------------
# Інваріант повного трасування (обидві фази) — як у прикладі 06
# ---------------------------------------------------------------------------
def test_full_trace_frame_counts_both_phases():
    """Кількість і порядок кадрів обох фаз збігаються з журналами подій."""
    # фаза хешу: init + N термів + final
    h, hash_events = polynomial_hash_steps(KONSPECT_PATTERN)
    n_terms = sum(1 for e in hash_events if e["kind"] == "term")
    assert n_terms == len(KONSPECT_PATTERN)
    hash_kinds = ["init"] + ["term"] * n_terms + ["final"]
    assert [e["kind"] for e in hash_events] == hash_kinds

    # фаза пошуку: один «вердикт» на вікно (slide/collision/match)
    result, search_events = rabin_karp_search_steps(RAW, KONSPECT_PATTERN)
    verdict_by_i = {}
    for e in search_events:
        if e["kind"] == "collision":
            verdict_by_i[int(e["i"])] = "collision"
        elif e["kind"] == "match_found":
            verdict_by_i[int(e["i"])] = "match"
    frames = ["init"]
    for e in search_events:
        if e["kind"] != "window":
            continue
        branch = verdict_by_i.get(int(e["i"]), "slide")
        frames.append(branch)
        if branch == "match":
            break
    # конспект: init + 6 slide + collision(6) + slide(7) + match(8)
    assert frames == ["init", "slide", "slide", "slide", "slide", "slide", "slide",
                      "collision", "slide", "match"], frames
    assert result == 8


# ---------------------------------------------------------------------------
# Аудит повноти англійських перекладів
# ---------------------------------------------------------------------------
def test_en_translation_audit():
    """Після повного прогону в режимі en усі кириличні підписи мають переклад."""
    i18n.missing_translations.clear()
    set_lang("en")
    try:
        # хеш
        draw_polynomial_hash("abc"); plt.close("all")
        _, hev = polynomial_hash_steps("developer")
        for e in hev:
            draw_hash_build_step(e); plt.close("all")
            hash_step_title(e); hash_step_caption(e)
        # пошук (усі види подій)
        _, sev = rabin_karp_search_steps(RAW, KONSPECT_PATTERN)
        for e in sev:
            search_step_title(e); search_step_caption(e)
            if e["kind"] in ("window", "hash_match", "collision", "match_found"):
                draw_rolling_window(e); plt.close("all")
            if e["kind"] == "roll":
                draw_rolling_update(e); plt.close("all")
        draw_search_evolution(sev); plt.close("all")
        # не знайдено
        _, nf = rabin_karp_search_steps(RAW, "manager")
        for e in nf:
            search_step_title(e); search_step_caption(e)
        # колізія / підсумок / складність / порівняння
        draw_collision("for", "jar"); plt.close("all")
        draw_compare_four(RAW, KONSPECT_PATTERN); plt.close("all")
        draw_complexity(); plt.close("all")
        draw_rolling_vs_recompute("abcd"); plt.close("all")
        # панелі коду
        for s in build_hash_steps("abc") + build_search_steps("for jar", "jar"):
            render_code_step(s); plt.close("all")
        draw_code_walkthrough_grid(build_hash_steps("abc"), "hash"); plt.close("all")
        draw_code_walkthrough_grid(build_search_steps("for jar", "jar"), "search"); plt.close("all")
        assert not i18n.missing_translations, \
            "немає EN-перекладу для:\n" + "\n".join(sorted(i18n.missing_translations))
    finally:
        set_lang("uk")
        i18n.missing_translations.clear()


# ---------------------------------------------------------------------------
# Мінімальний раннер на випадок, якщо pytest не встановлено
# ---------------------------------------------------------------------------
def _run_without_pytest():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} тестів пройдено")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_without_pytest() else 0)
