# -*- coding: utf-8 -*-
"""Покрокова візуалізація «код ↔ дані» для Рабіна-Карпа — ОКРЕМО для двох функцій.

Розбір має дві самостійні функції, тож і панелі «код ↔ дані» дві:

* **Хешування** (:data:`CODE_HASH`) — ліворуч код ``polynomial_hash`` із підсвіченими
  активними рядками, праворуч — символи рядка й **накопичений хеш** (Horner-крок);
* **Пошук** (:data:`CODE_SEARCH`) — ліворуч код ``rabin_karp_search``, праворуч —
  **ковзне вікно** з його хеш-бейджем і хешем шаблону, стан перевірки/колізії.

Колір рядка коду кодує семантику кроку: 🟡 активний рядок (цикл / обчислення),
🟢 «позитивна» гілка (збіг хешу підтверджено → ``return i``), 🔴 «негативна»
(колізія / ``return -1``), 🟠 збіг хешу (кандидат), 🔵 rolling-оновлення хешу.

Три незалежні блоки + композитор (як у попередніх розборах серії):

* **журнал** (:func:`build_hash_steps`, :func:`build_search_steps`) — переганяє
  журнал подій ``core`` у список **незмінних знімків** із мапою підсвічування та
  сирою подією під ключем ``event``; знає алгоритм, нічого не малює;
* **кодова панель** (:func:`draw_code_panel`) — малює код і підсвічує рядки за
  мапою ``{індекс: колір}`` зі знімка; нічого не знає про алгоритм;
* **панель даних** — повторно використовуємо
  :func:`…visualization._hash_grid` (хеш) та
  :func:`…visualization._draw_window_strip` (пошук);
* **композитор** (:func:`render_code_step`, :func:`draw_code_walkthrough_grid`) —
  складає панелі в одну фігуру / у високу сітку.

Двомовність: увесь видимий текст через :func:`…i18n.t`; кольори — зі ``style``.
Сам код (:data:`CODE_HASH`/:data:`CODE_SEARCH`) — мовно-нейтральний (дослівно з
конспекту).
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

from .core import polynomial_hash_steps, rabin_karp_search_steps
from .i18n import t
from .style import (
    GREEN_TXT,
    HL_ACTIVE,
    HL_HASH,
    HL_MATCH,
    HL_MISS,
    HL_ROLL,
    MISS_COLOR,
    ORANGE_TXT,
    ROLL_ARROW,
    TEXT_DARK,
    TEXT_FORMULA,
)
from .visualization import (
    _draw_window_strip,
    _hash_grid,
    hash_step_caption,
    hash_step_title,
    search_step_caption,
    search_step_title,
)

__all__ = [
    "CODE_HASH",
    "CODE_SEARCH",
    "build_hash_steps",
    "build_search_steps",
    "pick_illustrative",
    "draw_code_panel",
    "render_code_step",
    "draw_code_walkthrough_grid",
    "code_legend_handles",
]

# ---------------------------------------------------------------------------
# «Код як дані»: один елемент списку = один рядок коду. Індекси СТАБІЛЬНІ — саме
# на них посилається мапа підсвічування `hl`. Дослівно повторює базові
# реалізації core.polynomial_hash / core.rabin_karp_search (як у конспекті).
# ---------------------------------------------------------------------------
CODE_HASH: List[str] = [
    "def polynomial_hash(s, base=256, modulus=101):",                       # 0
    "    n = len(s)",                                                        # 1
    "    hash_value = 0",                                                    # 2
    "    for i, char in enumerate(s):",                                     # 3
    "        power_of_base = pow(base, n - i - 1) % modulus",               # 4
    "        hash_value = (hash_value + ord(char) * power_of_base) % modulus",  # 5
    "    return hash_value",                                                 # 6
]

CODE_SEARCH: List[str] = [
    "def rabin_karp_search(main_string, substring):",                       # 0
    "    substring_length = len(substring)",                                # 1
    "    main_string_length = len(main_string)",                            # 2
    "    base = 256",                                                       # 3
    "    modulus = 101",                                                    # 4
    "    substring_hash = polynomial_hash(substring, base, modulus)",       # 5
    "    current_slice_hash = polynomial_hash(main_string[:substring_length], base, modulus)",  # 6
    "    h_multiplier = pow(base, substring_length - 1) % modulus",         # 7
    "    for i in range(main_string_length - substring_length + 1):",       # 8
    "        if substring_hash == current_slice_hash:",                     # 9
    "            if main_string[i:i+substring_length] == substring:",       # 10
    "                return i",                                             # 11
    "        if i < main_string_length - substring_length:",                # 12
    "            current_slice_hash = (current_slice_hash - ord(main_string[i]) * h_multiplier) % modulus",  # 13
    "            current_slice_hash = (current_slice_hash * base + ord(main_string[i + substring_length])) % modulus",  # 14
    "            if current_slice_hash < 0:",                               # 15
    "                current_slice_hash += modulus",                        # 16
    "    return -1",                                                        # 17
]

# Семантичні набори підсвічування (значення — кольори зі style.py).
_HL_HASH = {
    "init": {1: HL_ACTIVE, 2: HL_ACTIVE},
    "term": {3: HL_ACTIVE, 4: HL_ACTIVE, 5: HL_MATCH},
    "final": {6: HL_MATCH},
}

# Пошук: ключі — «вердикти» вікна (один кадр на зміщення).
_HL_SEARCH = {
    "init":      {1: HL_ACTIVE, 2: HL_ACTIVE, 5: HL_ACTIVE, 6: HL_ACTIVE, 7: HL_ACTIVE},
    "slide":     {8: HL_ACTIVE, 9: HL_ACTIVE, 12: HL_ACTIVE, 13: HL_ROLL, 14: HL_ROLL},
    "collision": {8: HL_ACTIVE, 9: HL_HASH, 10: HL_MISS},
    "match":     {9: HL_HASH, 10: HL_ACTIVE, 11: HL_MATCH},
    "not_found": {17: HL_MISS},
}


# ---------------------------------------------------------------------------
# Блок 1 — журнал кроків (знімки НЕЗМІННІ; кожен несе сиру подію під "event")
# ---------------------------------------------------------------------------
def build_hash_steps(s: str, *, base: int = 256, modulus: int = 101) -> List[Dict]:
    """Журнал знімків «код ↔ накопичений хеш» для покрокового обчислення хешу.

    Кожна подія журналу :func:`…core.polynomial_hash_steps` розгортається у знімок:
    мапа підсвічування рядків ``CODE_HASH``, заголовок, вердикт і сира подія під
    ключем ``event`` (щоб картинка й текст ішли з одного списку).
    """
    _, events = polynomial_hash_steps(s, base, modulus)
    steps: List[Dict] = []
    for e in events:
        hl = _HL_HASH.get(e["kind"], {})
        steps.append({
            "kind": e["kind"],
            "panel": "hash",
            "event": e,
            "hl": dict(hl),
            "title": hash_step_title(e),
            "caption": hash_step_caption(e),
        })
    return steps


def _window_verdict(events: List, i: int) -> str:
    """Вердикт вікна на зміщенні ``i``: ``slide`` / ``collision`` / ``match``."""
    for e in events:
        ei = e.get("i")
        if ei is not None and int(ei) == i:
            if e["kind"] == "collision":
                return "collision"
            if e["kind"] == "match_found":
                return "match"
    return "slide"


def build_search_steps(main_string: str, pattern: str, *, base: int = 256,
                       modulus: int = 101) -> List[Dict]:
    """Журнал знімків «код ↔ ковзне вікно» для покрокових панелей пошуку.

    Один знімок на **зміщення вікна** (init + по кадру на кожне вікно + термінал):
    мапа підсвічування рядків ``CODE_SEARCH``, сира подія для малювання смуги
    (``window`` / ``collision`` / ``match_found``), заголовок і вердикт. Так сітка
    лишається читабельною: один рядок = одне рішення алгоритму на цьому вікні.
    """
    _, events = rabin_karp_search_steps(main_string, pattern, base, modulus)
    by_kind_i: Dict = {}
    for e in events:
        if e["kind"] in ("window", "collision", "match_found"):
            by_kind_i.setdefault(e["kind"], {})[int(e["i"])] = e

    steps: List[Dict] = [{
        "kind": "init", "panel": "search", "event": events[0],
        "hl": dict(_HL_SEARCH["init"]), "title": search_step_title(events[0]),
        "caption": search_step_caption(events[0]),
    }]

    result = int(events[-1]["result"])
    windows = sorted(by_kind_i.get("window", {}))
    for i in windows:
        verdict = _window_verdict(events, i)
        if verdict == "match":
            ev = by_kind_i["match_found"][i]
        elif verdict == "collision":
            ev = by_kind_i["collision"][i]
        else:
            ev = by_kind_i["window"][i]
        steps.append({
            "kind": verdict, "panel": "search", "event": ev,
            "hl": dict(_HL_SEARCH[verdict]), "title": search_step_title(ev),
            "caption": search_step_caption(ev),
        })
        if verdict == "match":
            break

    if result < 0:
        nf = next((e for e in events if e["kind"] == "not_found"), events[-1])
        steps.append({
            "kind": "not_found", "panel": "search", "event": nf,
            "hl": dict(_HL_SEARCH["not_found"]), "title": search_step_title(nf),
            "caption": search_step_caption(nf),
        })
    return steps


def pick_illustrative(steps: List[Dict]) -> List[Dict]:
    """Зріз журналу для СТАТИЧНОЇ сітки.

    Для хешу лишаємо ``init``/``term``/``final`` (усе показове). Для пошуку всі
    кадри вже — рішення на зміщення (``init``/``slide``/``collision``/``match``/
    ``not_found``), тож повертаємо як є.
    """
    return list(steps)


# ---------------------------------------------------------------------------
# Блок 2 — кодова панель (ліворуч)
# ---------------------------------------------------------------------------
def draw_code_panel(ax, highlights: Dict[int, str], code: Sequence[str],
                    *, fontsize: float = 9.0) -> None:
    """Малює ``code`` на осі ``ax`` і підсвічує рядки за мапою ``highlights``.

    :param highlights: ``{індекс_рядка: колір_заливки}`` зі знімка журналу.
    Рендер **чистий**: та сама мапа → та сама картинка, без знання про алгоритм.
    """
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    nlines = len(code)
    line_h = 1.0 / nlines
    for idx, line in enumerate(code):
        y = 1.0 - (idx + 0.5) * line_h
        if idx in highlights:
            ax.add_patch(Rectangle((0, y - line_h * 0.46), 1, line_h * 0.92,
                                   facecolor=highlights[idx], edgecolor="none", zorder=0))
        ax.text(0.015, y, line, family="monospace", fontsize=fontsize,
                va="center", ha="left", color=TEXT_DARK, zorder=2)


def code_legend_handles() -> List[Patch]:
    """Хендли легенди підсвічування коду (для ``fig.legend``)."""
    return [
        Patch(facecolor=HL_ACTIVE, edgecolor="none", label=t("активний рядок")),
        Patch(facecolor=HL_HASH, edgecolor="none", label=t("збіг хешу (кандидат)")),
        Patch(facecolor=HL_MATCH, edgecolor="none", label=t("підтверджено / знайдено")),
        Patch(facecolor=HL_MISS, edgecolor="none", label=t("колізія / не знайдено")),
        Patch(facecolor=HL_ROLL, edgecolor="none", label=t("rolling-оновлення")),
    ]


def _caption_color(kind: str) -> str:
    """Колір підпису-вердикту за типом кроку."""
    if kind in ("term", "final", "match"):
        return GREEN_TXT
    if kind in ("collision", "not_found"):
        return MISS_COLOR
    if kind == "slide":
        return ROLL_ARROW
    return TEXT_FORMULA


# ---------------------------------------------------------------------------
# Блок 3 — панель даних (праворуч): хеш-сітка або ковзне вікно
# ---------------------------------------------------------------------------
def _draw_data_panel(ax, step: Dict) -> None:
    """Малює праву панель знімка: сітку хешу або смугу «текст + ковзне вікно»."""
    if step["panel"] == "hash":
        _hash_grid(ax, step["event"], fs=14.0)
    else:
        _draw_window_strip(ax, step["event"], show_badges=True,
                           show_badge_label=False, show_index=True, value_fs=12.0)


# ---------------------------------------------------------------------------
# Композитор — одна фігура на крок (анімація) + повна сітка (статика)
# ---------------------------------------------------------------------------
def _code_for(step: Dict) -> List[str]:
    return CODE_HASH if step["panel"] == "hash" else CODE_SEARCH


def render_code_step(
    step: Dict,
    *,
    figsize=(12.0, 4.2),
    code: Optional[Sequence[str]] = None,
):
    """Один крок → одна фігура ``[код | дані]`` (кадр для анімації).

    :returns: об'єкт ``Figure``.
    """
    if code is None:
        code = _code_for(step)
    fig, (axc, axd) = plt.subplots(
        1, 2, figsize=figsize, gridspec_kw={"width_ratios": [1.25, 1.2]})
    draw_code_panel(axc, step["hl"], code)
    _draw_data_panel(axd, step)
    axd.set_title(step["title"], fontsize=11.0)
    if step.get("caption"):
        fig.text(0.5, 0.03, step["caption"], ha="center", va="bottom",
                 fontsize=10.0, color=_caption_color(step["kind"]))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.9, bottom=0.14, wspace=0.06)
    return fig


def draw_code_walkthrough_grid(
    steps: List[Dict],
    suptitle: str,
    *,
    code: Optional[Sequence[str]] = None,
    row_h: float = 3.2,
    width: float = 12.0,
    legend: bool = True,
):
    """Усі ``steps`` в ОДНІЙ високій сітці: рядок = ``[код | дані]``.

    :param steps: журнал (повний або зріз :func:`pick_illustrative`).
    :returns: об'єкт ``Figure``.
    """
    nrow = len(steps)
    fig, axes = plt.subplots(nrow, 2, figsize=(width, row_h * nrow),
                             gridspec_kw={"width_ratios": [1.25, 1.2]})
    if nrow == 1:
        axes = [axes]
    for r, step in enumerate(steps):
        axc, axd = axes[r]
        draw_code_panel(axc, step["hl"], code if code is not None else _code_for(step))
        _draw_data_panel(axd, step)
        axd.set_title(step["title"], fontsize=10.0)
        if step.get("caption"):
            axd.text(0.5, -0.2, step["caption"], transform=axd.transAxes,
                     ha="center", va="top", fontsize=9.0,
                     color=_caption_color(step["kind"]), clip_on=False)

    fig.suptitle(suptitle, fontsize=14, fontweight="bold")
    if legend:
        fig.legend(handles=code_legend_handles(), loc="lower center", ncol=5,
                   frameon=False, fontsize=9.0, bbox_to_anchor=(0.5, 0.004))
    bottom = 0.03 if legend else 0.01
    fig.tight_layout(rect=(0, bottom, 1, 0.985), h_pad=3.6)
    return fig
