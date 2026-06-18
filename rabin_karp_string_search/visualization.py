"""Візуалізації для навчального розбору алгоритму Рабіна-Карпа (Rabin-Karp).

Рабін-Карп порівнює **не символи, а ХЕШІ** — і кожна центральна фігура крутиться
навколо числа:

**Фаза 1 — поліноміальний хеш (рядок → число).**

* :func:`draw_polynomial_hash` — СИГНАТУРНИЙ кадр: рядок, внески ``ord·bᵏ``, сума й
  узяття за модулем (``"abc"`` → ``6382179`` → ``90``);
* :func:`draw_hash_build_step` — один крок Horner-акумуляції (модульний).

**Фаза 2 — пошук (ковзне вікно, порівняння хешів).**

* :func:`draw_rolling_window` — вікно на зміщенні ``i`` з його **хеш-бейджем** і
  хешем шаблону для звірки;
* :func:`draw_rolling_update` — крок rolling: лівий символ **виходить**
  (``− ord·h_multiplier``), ``× base``, правий **входить** (``+ ord``), ``mod`` —
  оновлення за :math:`O(1)`;
* :func:`draw_hash_compare` — збіг/незбіг хешів; на збігу — посимвольна перевірка;
* :func:`draw_collision` — **КОЛІЗІЯ**: рівні хеші, різні рядки → перевірка
  відкидає (унікальна перлина розбору);
* :func:`draw_search_evolution` — усі вікна одне під одним із хешами: збіги хешів і
  колізії проти справжніх збігів.

**Контраст і підсумок.**

* :func:`draw_rolling_vs_recompute` — rolling :math:`O(1)` проти перерахунку з нуля;
* :func:`draw_complexity` — RK середній :math:`O(n+m)` проти найгіршого :math:`O(n\\cdot m)`;
* :func:`draw_compare_four` — ПОВНЕ порівняння **чотирьох** рядкових алгоритмів.

Кольорова мова — єдина (див. :mod:`rabin_karp_string_search.style`): 🟢 справжній
збіг, 🟠 збіг ХЕШУ, 🔴 колізія; 🔻 символ виходить / 🔺 входить у rolling.
Символи завжди моноширинні у підписаних комірках, хеші — у бейджах-числах.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

from .core import (
    Event,
    count_boyer_moore_comparisons,
    count_hash_char_ops,
    count_kmp_comparisons,
    count_naive_comparisons,
    polynomial_hash,
    polynomial_hash_raw,
    polynomial_hash_steps,
    rabin_karp_metrics,
    rabin_karp_search_steps,
)
from .i18n import t
from .style import (
    BADGE_EDGE,
    BADGE_FILL,
    BADGE_TXT,
    CELL_COLLISION,
    CELL_COLLISION_EDGE,
    CELL_DIMMED,
    CELL_DIMMED_EDGE,
    CELL_DIMMED_TXT,
    CELL_HASHMATCH,
    CELL_HASHMATCH_EDGE,
    CELL_IN,
    CELL_IN_EDGE,
    CELL_MATCH,
    CELL_MATCH_EDGE,
    CELL_NEUTRAL,
    CELL_NEUTRAL_EDGE,
    CELL_OUT,
    CELL_OUT_EDGE,
    CELL_TEXT,
    CELL_WINDOW,
    CELL_WINDOW_EDGE,
    CURVE_BM,
    CURVE_KMP,
    CURVE_NAIVE,
    CURVE_RK,
    CURVE_RK_AVG,
    CURVE_RK_WORST,
    GREEN_TXT,
    HASH_EDGE,
    HASH_FILL,
    HASH_TXT,
    HEADER_TXT,
    MISS_COLOR,
    MUTED_TXT,
    ORANGE_TXT,
    PATTERN_HASH_EDGE,
    PATTERN_HASH_FILL,
    PATTERN_HASH_TXT,
    ROLL_ARROW,
    SUBLABEL_TXT,
    TERM_EDGE,
    TERM_FILL,
    TERM_SET_TXT,
    TERM_TXT,
    TEXT_DARK,
    TEXT_FORMULA,
    configure_style,
)

# :func:`configure_style` лишається доступною з цього модуля задля зручності
# (приклади імпортують її саме звідси), але визначена в :mod:`…style`.

__all__ = [
    "configure_style",
    # фаза 1 — поліноміальний хеш
    "draw_polynomial_hash",
    "draw_hash_build_step",
    # фаза 2 — пошук
    "draw_rolling_window",
    "draw_rolling_update",
    "draw_hash_compare",
    "draw_collision",
    "draw_search_evolution",
    # контраст / підсумок
    "draw_rolling_vs_recompute",
    "draw_complexity",
    "draw_compare_four",
    # текстові підписи / таблиці / друк
    "hash_step_title",
    "hash_step_caption",
    "search_step_title",
    "search_step_caption",
    "step_title",
    "step_caption",
    "step_summary",
    "search_trace_rows",
    "print_hash",
    "print_search_trace",
    "print_result",
]

# ---------------------------------------------------------------------------
# Геометрія однієї комірки-символу (у даних-координатах осі)
# ---------------------------------------------------------------------------
_CW, _CH = 0.92, 0.92          # ширина/висота комірки (крок між центрами = 1.0)

#: Стилі станів комірки: (заливка, обведення, колір тексту, товщина рамки).
_STATE_STYLE = {
    "match":     (CELL_MATCH,     CELL_MATCH_EDGE,     CELL_TEXT,       2.4),
    "collision": (CELL_COLLISION, CELL_COLLISION_EDGE, CELL_TEXT,       2.6),
    "hashmatch": (CELL_HASHMATCH, CELL_HASHMATCH_EDGE, CELL_TEXT,       2.4),
    "neutral":   (CELL_NEUTRAL,   CELL_NEUTRAL_EDGE,   CELL_TEXT,       1.4),
    "window":    (CELL_WINDOW,    CELL_WINDOW_EDGE,    CELL_TEXT,       1.6),
    "dimmed":    (CELL_DIMMED,    CELL_DIMMED_EDGE,    CELL_DIMMED_TXT, 1.0),
    "out":       (CELL_OUT,       CELL_OUT_EDGE,       CELL_TEXT,       2.4),
    "in":        (CELL_IN,        CELL_IN_EDGE,        CELL_TEXT,       2.4),
    "term":      (TERM_FILL,      TERM_EDGE,           TERM_TXT,        1.6),
}

_SUP = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _sup(n: int) -> str:
    """Верхній індекс (степінь) як рядок із unicode-надрядкових цифр."""
    return str(n).translate(_SUP)


def _char(ch: object) -> str:
    """Видимий символ для комірки (пробіл показуємо як ``␣``, щоб був видимий)."""
    s = str(ch)
    return "␣" if s == " " else s


def _char_cell(ax, x: float, y: float, ch: object, state: str, *,
               w: float = _CW, h: float = _CH, fs: float = 15.0,
               text_override: Optional[str] = None,
               text_color: Optional[str] = None) -> None:
    """Малює одну комірку-символ у заданому стані (моноширинний символ усередині)."""
    fill, edge, txt, lw = _STATE_STYLE[state]
    ax.add_patch(FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0,rounding_size=0.10",
        facecolor=fill, edgecolor=edge, linewidth=lw, zorder=2,
        mutation_aspect=1.0))
    shown = _char(ch) if text_override is None else text_override
    ax.text(x, y, shown, ha="center", va="center", fontsize=fs,
            color=text_color or txt, family="monospace", fontweight="bold", zorder=3)


def _hash_badge(ax, x: float, y: float, value, *, kind: str = "window",
                label: Optional[str] = None, fs: float = 13.0) -> None:
    """Малює ХЕШ як бейдж-число (``window`` — хеш вікна, ``pattern`` — хеш шаблону).

    Хеш — головний об'єкт порівняння в Рабіні-Карпі, тож йому віддано окремий
    помітний «бейдж-лічильник» замість комірки-символу.
    """
    if kind == "pattern":
        fill, edge, txt = PATTERN_HASH_FILL, PATTERN_HASH_EDGE, PATTERN_HASH_TXT
    else:
        fill, edge, txt = HASH_FILL, HASH_EDGE, HASH_TXT
    ax.add_patch(FancyBboxPatch(
        (x - 0.62, y - 0.34), 1.24, 0.68,
        boxstyle="round,pad=0.02,rounding_size=0.16",
        facecolor=fill, edgecolor=edge, linewidth=2.0, zorder=4))
    ax.text(x, y, str(value), ha="center", va="center", fontsize=fs,
            color=txt, fontweight="bold", family="monospace", zorder=5)
    if label:
        ax.text(x, y + 0.5, label, ha="center", va="bottom", fontsize=8.5,
                color=edge, fontweight="bold")


def _strip_axes(ax) -> None:
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ("top", "right", "left", "bottom"):
        ax.spines[spine].set_visible(False)


# ===========================================================================
# ФАЗА 1 — поліноміальний хеш (рядок → число)
# ===========================================================================
def draw_polynomial_hash(
    s: str,
    *,
    base: int = 256,
    modulus: int = 101,
    title: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
):
    """СИГНАТУРНИЙ кадр: рядок ``s`` → внески ``ord·bᵏ`` → сума → ``mod m``.

    Для ``"abc"`` показує те саме, що й конспект: ``ord('a')·256² +
    ord('b')·256¹ + ord('c')·256⁰ = 6382179``, а тоді ``mod 101 = 90``. Сітка має
    рядки: **символ**, його **код** ``ord``, **степінь** бази ``bⁿ⁻ⁱ⁻¹`` і
    **внесок** ``ord·bᵏ``; під нею — підсумкова формула «сума → хеш (mod m)».

    :returns: об'єкт ``Figure``.
    """
    n = len(s)
    h = polynomial_hash(s, base, modulus)

    # Внески: «сирі» ``ord·bᵏ`` дають іконічне «abc → 6382179 → 90», але на довгих
    # рядках вони стають астрономічними (для «developer» перший внесок — 22 цифри) і
    # не вміщаються в комірку. Тоді переходимо на МОДУЛЬНИЙ вигляд (степінь ``bᵏ mod m``
    # та внесок ``ord·(bᵏ mod m)``) — рівно ті числа, що їх рахує ``polynomial_hash``;
    # їхня сума за модулем дає той самий хеш.
    raw_contribs = [ord(s[k]) * base ** (n - k - 1) for k in range(n)]
    mod_powers = [pow(base, n - k - 1) % modulus for k in range(n)]
    mod_contribs = [ord(s[k]) * mod_powers[k] for k in range(n)]
    use_raw = (not raw_contribs) or max(raw_contribs) < 10 ** 7

    if use_raw:
        pow_cells = [f"{base}{_sup(n - k - 1)}" for k in range(n)]
        term_cells = [str(c) for c in raw_contribs]
        total = sum(raw_contribs)
        pow_label = f"{base}ᵏ"
    else:
        pow_cells = [str(p) for p in mod_powers]
        term_cells = [str(c) for c in mod_contribs]
        total = sum(mod_contribs)
        pow_label = f"{base}ᵏ mod {modulus}"

    if figsize is None:
        figsize = (max(7.0, n * 1.18 + 2.2), 4.6)
    fig, ax = plt.subplots(figsize=figsize)

    # рядки сітки (зверху вниз): символ / код / степінь / внесок
    y_sym, y_ord, y_pow, y_term = 3.0, 2.0, 1.05, 0.05
    step = 1.25
    for k in range(n):
        x = k * step
        ax.text(x, y_sym + _CH / 2 + 0.16, str(k), ha="center", va="bottom",
                fontsize=8, color=MUTED_TXT, zorder=3)
        _char_cell(ax, x, y_sym, s[k], "window", fs=16)
        ax.text(x, y_ord, str(ord(s[k])), ha="center", va="center", fontsize=11.5,
                color=TEXT_FORMULA, fontweight="bold", family="monospace")
        ax.text(x, y_pow, pow_cells[k], ha="center", va="center",
                fontsize=11.5, color=TERM_TXT, fontweight="bold", family="monospace")
        ax.text(x, y_term, term_cells[k], ha="center", va="center",
                fontsize=10.5, color=TEXT_DARK, family="monospace")
        if k < n - 1:
            ax.text(x + step / 2, y_term, "+", ha="center", va="center",
                    fontsize=12, color=MUTED_TXT, fontweight="bold")

    labels = [(y_sym, t("Символ"), HEADER_TXT), (y_ord, t("код ord"), TEXT_FORMULA),
              (y_pow, pow_label, TERM_TXT), (y_term, t("внесок"), TEXT_DARK)]
    for yy, lab, col in labels:
        ax.text(-1.25, yy, lab, ha="right", va="center", fontsize=10,
                color=col, fontweight="bold")

    cx = (n - 1) * step / 2.0
    ax.text(cx, -1.0,
            t("h(«{s}») = {raw} = {h} (mod {m})").format(s=s, raw=total, h=h, m=modulus),
            ha="center", va="top", fontsize=12.5, color=TEXT_FORMULA, fontweight="bold")
    ax.text(cx, -1.55, t("база b = {b}, модуль m = {m}").format(b=base, m=modulus),
            ha="center", va="top", fontsize=9.5, color=SUBLABEL_TXT)

    ax.set_xlim(-2.8, (n - 1) * step + 1.0)
    ax.set_ylim(-2.1, y_sym + _CH / 2 + 0.7)
    _strip_axes(ax)
    if title is None:
        title = t("Поліноміальний хеш рядка «{s}»").format(s=s)
    ax.set_title(title, fontsize=13.5)
    fig.tight_layout()
    return fig


def _hash_grid(ax, event: Event, *, fs: float = 15.0) -> None:
    """Дворядкова сітка «символи + накопичений хеш» для кроку Horner-акумуляції."""
    s = str(event["s"])
    n = int(event["n"])
    i = event["i"]
    active = int(i) if i is not None else -1
    y_sym = 0.0

    for k in range(n):
        if k == active:
            st = "in"                  # символ, який додаємо цього кроку
        elif i is not None and k < active:
            st = "match"               # уже враховані
        else:
            st = "neutral"
        ax.text(k, y_sym + _CH / 2 + 0.16, str(k), ha="center", va="bottom",
                fontsize=8, color=MUTED_TXT, zorder=3)
        _char_cell(ax, k, y_sym, s[k], st, fs=fs)

    ax.text(-1.1, y_sym, t("Символ"), ha="right", va="center", fontsize=10.5,
            color=HEADER_TXT, fontweight="bold")
    ax.set_xlim(-2.6, max(1, n) - 0.2)
    ax.set_ylim(y_sym - _CH / 2 - 0.4, y_sym + _CH / 2 + 0.5)
    _strip_axes(ax)
    ax.set_aspect("equal", adjustable="box")


def draw_hash_build_step(
    event: Event,
    *,
    title: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
):
    """Один крок **Horner-акумуляції** поліноміального хешу (модульний).

    Показує сітку символів (уже враховані — зелені, поточний — той, що входить),
    і під нею акумуляцію ``hash = (hash + ord(char)·power) mod m``, де
    ``power = pow(base, n-i-1) mod m``. Відповідає події журналу
    :func:`…core.polynomial_hash_steps`.

    :returns: об'єкт ``Figure``.
    """
    n = int(event["n"])
    if figsize is None:
        figsize = (max(6.6, n * 0.7 + 2.4), 3.4)
    fig, ax = plt.subplots(figsize=figsize)
    _hash_grid(ax, event)

    ax.set_title(hash_step_title(event) if title is None else title, fontsize=12.5)
    caption = hash_step_caption(event)
    if caption:
        ax.text(0.5, -0.04, caption, transform=ax.transAxes, ha="center", va="top",
                fontsize=11, color=(TERM_SET_TXT if event["kind"] == "term" else TEXT_FORMULA),
                fontweight="bold")
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    return fig


# ===========================================================================
# ФАЗА 2 — пошук (ковзне вікно, порівняння хешів)
# ===========================================================================
def _window_text_state(event: Event, c: int) -> str:
    """Стан комірки тексту на позиції ``c`` за подією пошуку."""
    kind = event["kind"]
    i = event["i"]
    M = int(event["M"])
    if i is None:
        return "neutral"
    i = int(i)
    # символи, що виходять/входять у rolling
    if kind == "roll":
        if c == i:
            return "out"
        if c == i + M:
            return "in"
    in_window = i <= c < i + M
    if not in_window:
        if c < i:
            return "dimmed"
        return "neutral"
    # у вікні: колір залежить від вердикту
    if kind in ("match_found",) or (kind == "verify" and event.get("confirmed")):
        return "match"
    if kind == "collision" or (kind == "verify" and event.get("confirmed") is False):
        return "collision"
    if kind == "hash_match":
        return "hashmatch"
    return "window"


def _draw_window_strip(
    ax,
    event: Event,
    *,
    show_badges: bool = True,
    show_badge_label: bool = True,
    show_index: bool = True,
    value_fs: float = 15.0,
) -> None:
    """Малює смугу тексту з підсвіченим вікном і **хеш-бейджами** (вікна + шаблону).

    Верхній рядок — увесь текст; вікно на зміщенні ``i`` підсвічене за вердиктом
    (нейтральне / 🟠 збіг хешу / 🟢 справжній збіг / 🔴 колізія). Праворуч —
    бейдж хешу вікна й бейдж хешу шаблону: саме їх порівнює алгоритм.
    """
    text = str(event["text"])
    pattern = str(event["pattern"])
    N, M = int(event["N"]), int(event["M"])
    i = event["i"]
    kind = event["kind"]
    y_text = 0.0

    for c in range(N):
        _char_cell(ax, c, y_text, text[c], _window_text_state(event, c), fs=value_fs)
        if show_index:
            ax.text(c, y_text + _CH / 2 + 0.15, str(c), ha="center", va="bottom",
                    fontsize=7.5, color=MUTED_TXT, zorder=3)

    ax.text(-0.95, y_text, t("текст"), ha="right", va="center", fontsize=10.5,
            color=HEADER_TXT, fontweight="bold")

    # rolling-стрілки: лівий виходить, правий входить
    if kind == "roll" and i is not None:
        i = int(i)
        ax.annotate("", xy=(i - 0.1, y_text - _CH / 2 - 0.55),
                    xytext=(i + 0.1, y_text - _CH / 2 - 0.2),
                    arrowprops=dict(arrowstyle="-|>", color=CELL_OUT_EDGE, lw=2.0))
        ax.text(i, y_text - _CH / 2 - 0.72, t("виходить «{c}»").format(c=_char(event["out_char"])),
                ha="center", va="top", fontsize=8.5, color=CELL_OUT_EDGE, fontweight="bold")
        if i + M < N:
            ax.annotate("", xy=(i + M + 0.1, y_text - _CH / 2 - 0.55),
                        xytext=(i + M - 0.1, y_text - _CH / 2 - 0.2),
                        arrowprops=dict(arrowstyle="-|>", color=CELL_IN_EDGE, lw=2.0))
            ax.text(i + M, y_text - _CH / 2 - 0.72, t("входить «{c}»").format(c=_char(event["in_char"])),
                    ha="center", va="top", fontsize=8.5, color=CELL_IN_EDGE, fontweight="bold")

    badge_x = N + 1.3
    if show_badges:
        # на rolling-кадрі вікно ще «старе» (offset i) — показуємо його хеш до
        # оновлення, а сам перехід до нового хешу пояснює формула під смугою.
        wh = (event["hash_before"] if kind == "roll" and event.get("hash_before") is not None
              else event["window_hash"])
        ph = event["pattern_hash"]
        _hash_badge(ax, badge_x, y_text + 0.55, wh, kind="window",
                    label=t("хеш вікна") if show_badge_label else None)
        _hash_badge(ax, badge_x, y_text - 0.55, ph, kind="pattern",
                    label=t("хеш шаблону") if show_badge_label else None)
        # знак порівняння між бейджами (= рівні / ≠ різні; колір — за вердиктом)
        if kind in ("hash_match", "match_found", "collision") or kind == "verify":
            sign = "="
            col = (GREEN_TXT if (kind == "match_found" or event.get("confirmed")) else
                   (MISS_COLOR if (kind == "collision" or event.get("confirmed") is False)
                    else ORANGE_TXT))
        elif wh == ph:
            sign, col = "=", ORANGE_TXT
        else:
            sign, col = "≠", MUTED_TXT
        ax.text(badge_x, y_text, sign, ha="center", va="center", fontsize=15,
                color=col, fontweight="bold")

    ax.set_xlim(-3.0, N + 2.8)
    ax.set_ylim(y_text - _CH / 2 - 1.0, y_text + _CH / 2 + 0.7)
    _strip_axes(ax)
    ax.set_aspect("equal", adjustable="box")


def _search_figsize(N: int, *, h: float = 3.2) -> Tuple[float, float]:
    return (max(8.0, N * 0.5 + 4.0), h)


def draw_rolling_window(
    event: Event,
    *,
    title: Optional[str] = None,
    show_counters: bool = True,
    figsize: Optional[Tuple[float, float]] = None,
):
    """Головний кадр кроку пошуку: вікно на зміщенні ``i`` + хеш-бейджі + вердикт.

    :param event: подія журналу :func:`…core.rabin_karp_search_steps`.
    :returns: об'єкт ``Figure``.
    """
    N = int(event["N"])
    if figsize is None:
        figsize = _search_figsize(N)
    fig, ax = plt.subplots(figsize=figsize)
    _draw_window_strip(ax, event)
    ax.set_title(search_step_title(event) if title is None else title, fontsize=13)
    caption = search_step_caption(event)
    if caption:
        ax.text(0.5, -0.02, caption, transform=ax.transAxes, ha="center", va="top",
                fontsize=10.5, color=_search_caption_color(event), fontweight="bold")
    if show_counters:
        ax.text(0.5, -0.13, counters_line(event), transform=ax.transAxes,
                ha="center", va="top", fontsize=9.5, color=TEXT_FORMULA)
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    return fig


def draw_rolling_update(
    event: Event,
    *,
    figsize: Optional[Tuple[float, float]] = None,
):
    """Кадр **rolling-оновлення**: лівий символ виходить, правий входить, хеш за O(1).

    Показує вікно перед оновленням (зверху, з символами 🔻 виходить / 🔺 входить),
    формулу ``− ord(out)·h_multiplier, ×base, + ord(in)  →  mod`` і новий хеш вікна.
    Подія ``roll`` журналу :func:`…core.rabin_karp_search_steps`.

    :returns: об'єкт ``Figure``.
    """
    N = int(event["N"])
    if figsize is None:
        figsize = _search_figsize(N, h=3.6)
    fig, ax = plt.subplots(figsize=figsize)
    _draw_window_strip(ax, event)

    ax.set_title(t("Rolling hash: вікно котиться на 1 за O(1)"), fontsize=13)
    out_c = _char(event["out_char"])
    in_c = _char(event["in_char"])
    mult = int(event["h_multiplier"])
    b = int(event["base"])
    ha = int(event["hash_after"])
    ax.text(0.5, -0.02,
            t("− ord(«{out}»)·{mult}, ×{b}, + ord(«{in}»)  →  {h}").format(
                out=out_c, mult=mult, b=b, **{"in": in_c}, h=ha),
            transform=ax.transAxes, ha="center", va="top", fontsize=11,
            color=ROLL_ARROW, fontweight="bold")
    ax.text(0.5, -0.13, t("хеш: {a} → {b}").format(a=int(event["hash_before"]), b=ha),
            transform=ax.transAxes, ha="center", va="top", fontsize=10,
            color=TEXT_FORMULA)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    return fig


def draw_hash_compare(
    event: Event,
    *,
    figsize: Optional[Tuple[float, float]] = None,
):
    """Кадр **порівняння хешів** на зміщенні ``i`` (збіг → перевірка / незбіг → далі).

    :param event: подія ``window`` / ``hash_match`` журналу пошуку.
    :returns: об'єкт ``Figure``.
    """
    return draw_rolling_window(event, figsize=figsize)


def draw_collision(
    s1: str,
    s2: str,
    *,
    base: int = 256,
    modulus: int = 101,
    figsize: Optional[Tuple[float, float]] = None,
):
    """УНІКАЛЬНА ПЕРЛИНА: дві **різні** рядки з **однаковим** хешем (колізія).

    Малює два рядки один під одним, для кожного — внески ``ord·bᵏ``, «велике число»
    без модуля та хеш ``mod m``. Числа без модуля **різні**, а хеші — **однакові**:
    саме тому на збігу хешів алгоритм робить посимвольну перевірку.

    :returns: об'єкт ``Figure``.
    """
    assert len(s1) == len(s2), "колізія визначена для рядків однакової довжини"
    n = len(s1)
    h1, h2 = polynomial_hash(s1, base, modulus), polynomial_hash(s2, base, modulus)
    r1, r2 = polynomial_hash_raw(s1, base), polynomial_hash_raw(s2, base)

    if figsize is None:
        figsize = (max(7.4, n * 1.0 + 4.2), 4.2)
    fig, ax = plt.subplots(figsize=figsize)
    step = 1.1
    rows = [(2.0, s1, r1, h1), (0.4, s2, r2, h2)]
    for y, s, raw, h in rows:
        for k in range(n):
            x = k * step
            _char_cell(ax, x, y, s[k], "window", fs=15)
            ax.text(x, y - 0.62, f"{ord(s[k])}·{base}{_sup(n - k - 1)}", ha="center",
                    va="center", fontsize=8.5, color=TERM_TXT, family="monospace")
        _hash_badge(ax, (n - 1) * step + 2.4, y, h, kind="pattern")
        ax.text((n - 1) * step + 1.35, y, "→", ha="center", va="center",
                fontsize=15, color=MUTED_TXT, fontweight="bold")
        ax.text((n - 1) * step / 2.0, y + _CH / 2 + 0.28,
                t("велике число {raw} → {h} (mod {m})").format(raw=raw, h=h, m=modulus),
                ha="center", va="bottom", fontsize=9.5, color=TEXT_FORMULA)

    # «дорівнює» між двома хешами
    bx = (n - 1) * step + 2.4
    ax.text(bx, 1.2, "=", ha="center", va="center", fontsize=20,
            color=MISS_COLOR, fontweight="bold")

    ax.set_xlim(-1.2, (n - 1) * step + 3.6)
    ax.set_ylim(-0.7, 3.3)
    _strip_axes(ax)
    ax.set_aspect("equal", adjustable="box")
    ax.set_title(t("Колізія під (b={b}, m={m}): різні рядки — однаковий хеш").format(
        b=base, m=modulus), fontsize=13)
    fig.text(0.5, 0.04,
             t("ось навіщо потрібна посимвольна перевірка на збігу хешів"),
             ha="center", va="bottom", fontsize=10.5, color=MISS_COLOR, fontweight="bold")
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    return fig


def _collect_search_windows(events: List[Event]) -> List[Dict]:
    """Зводить журнал пошуку в список вікон (одне зміщення = один рядок драбинки)."""
    rows: List[Dict] = []
    by_i: Dict[int, Dict] = {}
    for e in events:
        if e["kind"] == "window":
            d = {"i": int(e["i"]), "window": str(e["window"]),
                 "window_hash": int(e["window_hash"]), "verdict": "none"}
            by_i[int(e["i"])] = d
            rows.append(d)
        elif e["kind"] == "hash_match":
            by_i[int(e["i"])]["verdict"] = "hash"
        elif e["kind"] == "collision":
            by_i[int(e["i"])]["verdict"] = "collision"
        elif e["kind"] == "match_found":
            by_i[int(e["i"])]["verdict"] = "match"
    return rows


def draw_search_evolution(
    events: List[Event],
    *,
    suptitle: Optional[str] = None,
    figsize: Optional[Tuple[float, float]] = None,
):
    """Усі вікна одне під одним із їхніми хешами: збіги хешів і колізії проти збігів.

    Верхній рядок — текст. Нижче — один рядок на кожне зміщення вікна: символи
    вікна, його хеш-бейдж і вердикт (нейтрально / 🟠 збіг хешу / 🔴 колізія /
    🟢 справжній збіг). Праворуч — хеш шаблону (еталон). Наочно видно, що
    посимвольну перевірку роблять **лише** на збігу хешів.

    :returns: об'єкт ``Figure``.
    """
    text = str(events[0]["text"])
    pattern = str(events[0]["pattern"])
    N, M = int(events[0]["N"]), int(events[0]["M"])
    ph = int(events[0]["pattern_hash"])
    rows = _collect_search_windows(events)
    nrows = max(1, len(rows))
    last = events[-1]

    if figsize is None:
        figsize = (max(8.0, N * 0.52 + 4.2), nrows * 0.66 + 2.4)
    fig, ax = plt.subplots(figsize=figsize)
    w = h = 0.84
    y_text = nrows + 0.6

    for c in range(N):
        _char_cell(ax, c, y_text, text[c], "neutral", w=w, h=h, fs=12)
        ax.text(c, y_text + h / 2 + 0.12, str(c), ha="center", va="bottom",
                fontsize=7, color=MUTED_TXT)
    ax.text(-1.6, y_text, t("текст"), ha="right", va="center", fontsize=9.5,
            color=HEADER_TXT, fontweight="bold")
    _hash_badge(ax, N + 1.6, y_text, ph, kind="pattern", label=t("хеш шаблону"))

    state_map = {"none": "window", "hash": "hashmatch", "collision": "collision",
                 "match": "match"}
    for r, row in enumerate(rows):
        off = row["i"]
        y = nrows - 1 - r
        for p in range(M):
            _char_cell(ax, off + p, y, pattern[p] if row["verdict"] == "match" else text[off + p],
                       state_map[row["verdict"]], w=w, h=h, fs=12)
        ax.text(-1.6, y, t("вікно") + f" {off}", ha="right", va="center",
                fontsize=8.5, color=HASH_TXT, fontweight="bold")
        _hash_badge(ax, N + 1.6, y, row["window_hash"], kind="window", fs=11)
        # вердикт-підпис праворуч від бейджа (✓ збіг / ✗ колізія / = кандидат / ≠ різні)
        if row["verdict"] == "match":
            tail, col = "✓", GREEN_TXT
        elif row["verdict"] == "collision":
            tail, col = "✗", MISS_COLOR
        elif row["verdict"] == "hash":
            tail, col = "=", ORANGE_TXT
        else:
            tail, col = "≠", MUTED_TXT
        ax.text(N + 2.9, y, tail, ha="left", va="center", fontsize=14, color=col,
                fontweight="bold")

    m = rabin_karp_metrics(text, pattern,
                           base=int(events[0]["base"]), modulus=int(events[0]["modulus"]))
    ax.text((N - 1) / 2.0, -1.15,
            t("порівнянь хешів: {hc} · char-перевірок: {cv} · колізій: {col}").format(
                hc=m["hash_comparisons"], cv=m["char_verifications"], col=m["collisions"]),
            ha="center", va="top", fontsize=10, color=TEXT_FORMULA, fontweight="bold")

    if suptitle is None:
        suptitle = t("Пошук Рабіна-Карпа: вікна та їхні хеші")
    ax.set_title(suptitle, fontsize=13)
    ax.set_xlim(-3.2, N + 4.0)
    ax.set_ylim(-1.7, y_text + 0.9)
    _strip_axes(ax)
    ax.set_aspect("equal", adjustable="box")
    fig.tight_layout()
    return fig


# ===========================================================================
# Контраст / підсумок
# ===========================================================================
def draw_rolling_vs_recompute(
    pattern: str = "abcd",
    *,
    n_max: int = 60,
    figsize: Tuple[float, float] = (7.8, 5.0),
):
    """Графік: rolling :math:`O(1)` проти перерахунку хешу з нуля :math:`O(m)`.

    Для тексту довжини ``n`` (із шаблоном завдовжки ``m = len(pattern)``) рахуємо
    «символьні операції хешування»: rolling росте **лінійно** за ``n``, а
    перерахунок із нуля — як ``n·m``. Це і є пейофф ковзного хешу.

    :returns: об'єкт ``Figure``.
    """
    m = len(pattern)
    ns = np.arange(m, n_max + 1)
    rolling = [count_hash_char_ops("a" * int(n), pattern, rolling=True) for n in ns]
    recompute = [count_hash_char_ops("a" * int(n), pattern, rolling=False) for n in ns]

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(ns, recompute, color=CURVE_RK_WORST, lw=2.6,
            label=t("перерахунок із нуля ≈ n·m"))
    ax.plot(ns, rolling, color=CURVE_RK_AVG, lw=3.0, label=t("rolling ≈ n (лінійно)"))
    ax.set_title(t("Rolling O(1) проти перерахунку з нуля O(m)"), fontsize=12.5)
    ax.set_xlabel(t("довжина тексту n"), fontsize=11, color=HEADER_TXT)
    ax.set_ylabel(t("символьних операцій хешування"), fontsize=11, color=HEADER_TXT)
    ax.legend(loc="upper left", fontsize=10, frameon=True, framealpha=0.92)
    ax.grid(True, linestyle=":", alpha=0.45)
    ax.margins(x=0.01)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    return fig


def draw_complexity(
    n_max: int = 60,
    *,
    m_ratio: float = 0.5,
    figsize: Tuple[float, float] = (7.8, 5.2),
):
    """Графік складності Рабіна-Карпа: середній :math:`O(n+m)` проти найгіршого :math:`O(n\\cdot m)`.

    Зелена крива — середній/найкращий випадок :math:`n + m` (колізії рідкісні, хеш
    розподіляє рівномірно). Червона — найгірший :math:`n\\cdot m` (багато колізій →
    багато прямих порівнянь підрядків; стається, зокрема, при невдалому/малому модулі).

    :returns: об'єкт ``Figure``.
    """
    n = np.arange(1, n_max + 1, dtype=float)
    m = np.maximum(1.0, m_ratio * n)
    avg = n + m
    worst = n * m

    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(n, worst, color=CURVE_RK_WORST, linewidth=2.6,
            label=t("Рабін-Карп — найгірший ≈ n·m (багато колізій)"))
    ax.plot(n, avg, color=CURVE_RK_AVG, linewidth=3.0,
            label=t("Рабін-Карп — середній ≈ n + m"))
    ax.set_title(t("Скільки char-порівнянь? Рабін-Карп O(n+m) проти O(n·m)"), fontsize=12.5)
    ax.set_xlabel(t("довжина тексту n"), fontsize=11, color=HEADER_TXT)
    ax.set_ylabel(t("кількість порівнянь (приблизно)"), fontsize=11, color=HEADER_TXT)
    ax.legend(loc="upper left", fontsize=10, frameon=True, framealpha=0.92)
    ax.grid(True, linestyle=":", alpha=0.45)
    ax.margins(x=0.01)
    ax.set_ylim(bottom=0)
    fig.tight_layout()
    return fig


def draw_compare_four(
    text: str,
    pattern: str,
    *,
    figsize: Tuple[float, float] = (8.4, 5.2),
):
    """ПОВНЕ порівняння **чотирьох** рядкових алгоритмів за посимвольними порівняннями.

    Стовпчики — кількість **посимвольних** порівнянь на тих самих ``(text, pattern)``
    для наївного / KMP / Боєра-Мура / Рабіна-Карпа. Ключовий висновок: Рабін-Карп
    робить **найменше char-порівнянь** (бо здебільшого порівнює хеші), а перевірку
    символів запускає лише на збігу хешів.

    :returns: об'єкт ``Figure``.
    """
    naive = count_naive_comparisons(text, pattern)
    kmp = count_kmp_comparisons(text, pattern)
    bm = count_boyer_moore_comparisons(text, pattern)
    metrics = rabin_karp_metrics(text, pattern)
    rk = metrics["char_comparisons"]
    rk_hash = metrics["hash_comparisons"]

    names = [t("наївний"), "KMP", t("Боєра-Мура"), t("Рабіна-Карпа (char-перевірки)")]
    values = [naive, kmp, bm, rk]
    colors = [CURVE_NAIVE, CURVE_KMP, CURVE_BM, CURVE_RK]

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(range(4), values, color=colors, width=0.62, zorder=3)
    for b, v in zip(bars, values):
        ax.text(b.get_x() + b.get_width() / 2, v, str(v), ha="center", va="bottom",
                fontsize=11, color=TEXT_DARK, fontweight="bold")
    # Рабін-Карп основну роботу робить ДЕШЕВИМИ порівняннями хешів — позначаємо їх
    # окремо над зеленим стовпцем (char-перевірки — лише на збігу хешів).
    rk_bar = bars[3]
    ax.annotate(t("+{h} hash").format(h=rk_hash),
                xy=(rk_bar.get_x() + rk_bar.get_width() / 2, rk),
                xytext=(0, 18), textcoords="offset points",
                ha="center", va="bottom", fontsize=10, color=CURVE_RK, fontweight="bold")
    ax.set_xticks(range(4))
    ax.set_xticklabels(names, fontsize=10)
    ax.set_ylabel(t("посимвольних порівнянь"), fontsize=11, color=HEADER_TXT)
    ax.set_title(t("Чотири рядкові алгоритми: посимвольні порівняння на «{t}» / «{p}»").format(
        t=text, p=pattern), fontsize=12)
    ax.grid(True, axis="y", linestyle=":", alpha=0.45)
    ax.set_ylim(0, max(values) * 1.2 + 1)
    fig.tight_layout()
    return fig


# ===========================================================================
# Текстові заголовки / підписи / таблиці / друк
# ===========================================================================
def hash_step_title(event: Event) -> str:
    """Заголовок кадру для події побудови хешу."""
    kind = event["kind"]
    if kind == "init":
        return t("Старт: hash = 0")
    if kind == "final":
        return t("Готово: hash = {h}").format(h=event["hash_value"])
    return t("Крок Horner-акумуляції: i = {i}").format(i=event["i"])


def hash_step_caption(event: Event) -> str:
    """Підпис-вердикт під кадром побудови хешу."""
    if event["kind"] == "term":
        return t("+ ord(«{c}»)·{p} = {contrib}  →  hash = {h}").format(
            c=_char(event["char"]), p=int(event["power"]),
            contrib=int(event["contribution"]), h=int(event["hash_value"]))
    return ""


def search_step_title(event: Event) -> str:
    """Заголовок кадру для події пошуку."""
    kind = event["kind"]
    if kind == "init":
        return t("шукаємо шаблон: «{p}»").format(p=event["pattern"])
    if kind in ("window", "hash_match", "verify", "collision", "roll"):
        return t("Вікно на зміщенні {i}: хеш {hw} проти хешу шаблону {hp}").format(
            i=event["i"], hw=event["window_hash"], hp=event["pattern_hash"])
    if kind == "match_found":
        return t("справжній збіг: «{w}» = «{p}» ✓").format(
            w=_char_word(event["window"]), p=_char_word(event["pattern"]))
    if kind == "not_found":
        return t("Шаблон не знайдено")
    if int(event["result"]) >= 0:
        return t("Готово: знайдено на позиції {i}").format(i=event["result"])
    return t("Готово: шаблон відсутній (-1)")


def _char_word(s: object) -> str:
    """Рядок із видимими пробілами (для підписів-слів)."""
    return "".join(_char(c) for c in str(s))


def search_step_caption(event: Event) -> str:
    """Підпис-вердикт під кадром пошуку."""
    kind = event["kind"]
    hw, hp = event["window_hash"], event["pattern_hash"]
    if kind == "window":
        if hw == hp:
            return t("збіг хешу: {hw} = {hp} → перевіряємо символи").format(hw=hw, hp=hp)
        return t("хеші різні: {hw} ≠ {hp} → ковзаємо далі").format(hw=hw, hp=hp)
    if kind == "hash_match":
        return t("збіг хешу: {hw} = {hp} → перевіряємо символи").format(hw=hw, hp=hp)
    if kind == "collision" or (kind == "verify" and event.get("confirmed") is False):
        return t("КОЛІЗІЯ: хеші рівні ({h}), але «{w}» ≠ «{p}» ✗").format(
            h=hw, w=_char_word(event["window"]), p=_char_word(event["pattern"]))
    if kind == "match_found" or (kind == "verify" and event.get("confirmed")):
        return t("справжній збіг: «{w}» = «{p}» ✓").format(
            w=_char_word(event["window"]), p=_char_word(event["pattern"]))
    if kind == "roll":
        return t("− ord(«{out}»)·{mult}, ×{b}, + ord(«{in}»)  →  {h}").format(
            out=_char(event["out_char"]), mult=int(event["h_multiplier"]),
            b=int(event["base"]), **{"in": _char(event["in_char"])},
            h=int(event["hash_after"]))
    return ""


def _search_caption_color(event: Event) -> str:
    kind = event["kind"]
    if kind == "match_found" or (kind == "verify" and event.get("confirmed")) \
            or (kind == "final" and int(event["result"]) >= 0):
        return GREEN_TXT
    if kind == "collision" or (kind == "verify" and event.get("confirmed") is False) \
            or kind == "not_found" or (kind == "final" and int(event["result"]) < 0):
        return MISS_COLOR
    if kind in ("hash_match",) or (kind == "window" and event["window_hash"] == event["pattern_hash"]):
        return ORANGE_TXT
    if kind == "roll":
        return ROLL_ARROW
    return TEXT_FORMULA


def counters_line(event: Event) -> str:
    """Рядок лічильників пошуку (порівняння хешів / char-перевірки / колізії / rolling)."""
    return t("порівнянь хешів: {hc} · char-перевірок: {cv} · колізій: {col} · rolling: {r}").format(
        hc=event["hash_comparisons"], cv=event["char_verifications"],
        col=event["collisions"], r=event["rolls"])


# --- універсальний диспетчер (для обох фаз) --------------------------------
def step_title(event: Event) -> str:
    """Заголовок кадру для будь-якої події (диспетч за ``phase``)."""
    return hash_step_title(event) if event.get("phase") == "hash" else search_step_title(event)


def step_caption(event: Event) -> str:
    """Підпис-вердикт для будь-якої події (диспетч за ``phase``)."""
    return hash_step_caption(event) if event.get("phase") == "hash" else search_step_caption(event)


def step_summary(event: Event) -> str:
    """Текстовий підсумок однієї події (заголовок + вердикт)."""
    title = step_title(event)
    caption = step_caption(event)
    return f"{title}: {caption}" if caption else title


# ---------------------------------------------------------------------------
# Таблиці кроків / підсумки для консолі та README
# ---------------------------------------------------------------------------
def search_trace_rows(events: List[Event]) -> List[Tuple]:
    """Рядки таблиці пошуку: ``(i, вікно, хеш вікна, хеш шаблону, вердикт)``.

    Один рядок на кожне вікно (подія ``window``), із вердиктом: збіг хешу / колізія /
    справжній збіг / хеші різні.
    """
    rows: List[Tuple] = []
    verdict_by_i: Dict[int, str] = {}
    for e in events:
        if e["kind"] == "hash_match":
            verdict_by_i[int(e["i"])] = "hash"
        elif e["kind"] == "collision":
            verdict_by_i[int(e["i"])] = "collision"
        elif e["kind"] == "match_found":
            verdict_by_i[int(e["i"])] = "match"
    for e in events:
        if e["kind"] != "window":
            continue
        i = int(e["i"])
        v = verdict_by_i.get(i, "none")
        if v == "match":
            verdict = t("справжній збіг")
        elif v == "collision":
            verdict = t("колізія (char-перевірка відкидає)")
        elif v == "hash":
            verdict = t("збіг хешу")
        else:
            verdict = t("хеші різні")
        rows.append((i, _char_word(e["window"]), int(e["window_hash"]),
                     int(e["pattern_hash"]), verdict))
    return rows


def print_hash(s: str, base: int = 256, modulus: int = 101) -> None:
    """Друкує поліноміальний хеш рядка у форматі конспекту (велике число → mod)."""
    raw = polynomial_hash_raw(s, base)
    h = polynomial_hash(s, base, modulus)
    print(t("h(«{s}») = {raw} = {h} (mod {m})").format(s=s, raw=raw, h=h, m=modulus))


def print_search_trace(events: List[Event]) -> None:
    """Друкує таблицю кроків пошуку (вікно, хеші, вердикт) у консоль."""
    head = "  i  | " + t("вікно") + " | " + t("хеш вікна") + " | " + \
           t("хеш шаблону") + " | " + t("вердикт")
    print(head)
    print("  " + "-" * (len(head) - 2))
    for i, window, hw, hp, verdict in search_trace_rows(events):
        print(f"  {i:>2} | {window:^5} | {hw:^9} | {hp:^11} | {verdict}")


def print_result(events: List[Event]) -> None:
    """Друкує підсумок пошуку: текст, шаблон, хеш шаблону, результат і лічильники."""
    first, last = events[0], events[-1]
    print(t("Текст:   {s}").format(s=first["text"]))
    print(t("Шаблон:  {p}").format(p=first["pattern"]))
    print(t("Хеш шаблону: {h}").format(h=first["pattern_hash"]))
    r = int(last["result"])
    if r >= 0:
        print(t("Результат: знайдено на позиції {r}").format(r=r))
    else:
        print(t("Результат: шаблон не знайдено (-1)"))
    print(counters_line(last))
