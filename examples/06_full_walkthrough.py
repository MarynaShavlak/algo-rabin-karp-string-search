"""Приклад 6 — ПОВНЕ покрокове трасування КОНСПЕКТ-прикладу (дві фази).

Розбирає той самий приклад, що й конспект — пошук шаблону ``"developer"`` у тексті
``"Being a developer is not easy"`` — але **повністю** й у дві фази, кожен крок
окремим зображенням «код ↔ дані» з детальним поясненням під ним:

* **Фаза 1 — хешування**: обчислення поліноміального хешу шаблону ``"developer"``
  (``polynomial_hash``, Horner-акумуляція крок за кроком → ``35``);
* **Фаза 2 — пошук**: сам ``rabin_karp_search`` тексту конспекту — вікно ковзає,
  хеш «котиться», на зміщенні 6 трапляється **колізія** (хеш ``35`` збігся, але
  «a develop» ≠ «developer»), а справжній збіг — на зміщенні 8.

Окрім картинок, приклад САМ генерує markdown-фрагмент усіх кроків і вставляє його
в README між маркерами ``<!-- WALKTHROUGH:START -->`` і ``<!-- WALKTHROUGH:END -->``
(для ``uk`` — у ``README.md``, для ``en`` — у ``README.en.md``). Усі числа
(хеші, лічильники, внески) беруться з журналів подій ``core`` — **єдиного джерела
правди**; повторний запуск дає байтово той самий результат.

Кількість кадрів кожної фази обчислюється з журналу й перевіряється ``assert``
(окремо для фази хешу й фази пошуку), як і порядок кадрів.

Запуск:  ``python examples/06_full_walkthrough.py``      (uk → docs/images/walkthrough/)
         ``python examples/06_full_walkthrough.py en``   (en → docs/images/en/walkthrough/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import IMG_DIR, LANG, print_saved_location, save_figure  # noqa: F401
from _searches import RAW, KONSPECT_PATTERN

import os

import matplotlib.pyplot as plt  # noqa: E402

from rabin_karp_string_search.core import (  # noqa: E402
    polynomial_hash_steps,
    rabin_karp_search_steps,
)
from rabin_karp_string_search.visualization import (  # noqa: E402
    configure_style,
    hash_step_title,
    search_step_title,
)
from rabin_karp_string_search.walkthrough import (  # noqa: E402
    _HL_HASH,
    _HL_SEARCH,
    render_code_step,
)

PATTERN = KONSPECT_PATTERN
TEXT = RAW

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_SUBDIR = "walkthrough"
_IMG_PREFIX = ("docs/images/en/" if LANG == "en" else "docs/images/") + _SUBDIR + "/"
_README = "README.en.md" if LANG == "en" else "README.md"
_START, _END = "<!-- WALKTHROUGH:START -->", "<!-- WALKTHROUGH:END -->"


def _char(ch: str) -> str:
    return "␣" if ch == " " else ch


def _word(s: str) -> str:
    return "".join(_char(c) for c in str(s))


# Текстові шаблони пояснень — окремо для кожної мови (обидва переклади тут, тож
# блок повністю самодостатній і байтово-стабільний). Числа підставляються з подій.
_TEXT = {
    "uk": {
        "generating": "Генерую повне покрокове трасування «код ↔ дані» (дві фази)…",
        "saved": "  збережено {n} кадрів у {sub}",
        "readme": "  README-блок ({doc}) оновлено між маркерами WALKTHROUGH.",
        "phase1": "### Фаза 1 — хешування: поліноміальний хеш шаблону «developer»",
        "phase2": "### Фаза 2 — пошук «developer» у тексті конспекту",
        "step": "Крок",
        "hash_init": (
            "Фаза 1 — **хешування**. Перетворюємо шаблон «{s}» (довжина {n}) на "
            "число — поліноміальний хеш за модулем 101. Починаємо з `hash = 0` і "
            "додаємо внесок кожного символу зліва направо (схема Горнера)."
        ),
        "hash_term": (
            "Крок `i = {i}`: символ «{c}» (код `ord = {code}`). Степінь "
            "`pow(256, {pw}) % 101 = {power}`, внесок `{code}·{power} = {contrib}`. "
            "Накопичений `hash = {h}`."
        ),
        "hash_final": (
            "Хеш шаблону «{s}» обчислено: **{h}**. Саме це число ми порівнюватимемо "
            "з хешем кожного вікна тексту — замість того, щоб звіряти символи."
        ),
        "search_init": (
            "Фаза 2 — **пошук**. Хеш шаблону «{p}» дорівнює **{ph}**. Вікно "
            "завдовжки {m} ковзає текстом; на кожному зміщенні порівнюємо **хеш "
            "вікна** з {ph}. Символи звіряємо лише тоді, коли хеші збіглися."
        ),
        "search_slide": (
            "Вікно на зміщенні `i = {i}` — «{w}», його хеш **{hw}** ≠ {ph}. Не "
            "збіглося, тож ковзаємо далі. Новий хеш рахуємо за `O(1)` (rolling): "
            "лівий символ виходить, правий входить."
        ),
        "search_collision": (
            "Вікно `i = {i}` — «{w}», хеш **{hw} = {ph}** — збіг ХЕШУ! Але "
            "посимвольна перевірка: «{w}» ≠ «{p}». Це **КОЛІЗІЯ** — різні рядки з "
            "однаковим хешем. Саме тут char-перевірка рятує від хибного збігу: "
            "відкидаємо й ковзаємо далі."
        ),
        "search_match": (
            "Вікно `i = {i}` — «{w}», хеш **{hw} = {ph}**, і перевірка: «{w}» = "
            "«{p}» ✓ — **справжній збіг**! Повертаємо позицію {i}. Підсумок: {hc} "
            "порівнянь хешів, лише {cv} char-перевірки (з них {col} колізія), "
            "{r} rolling-оновлень."
        ),
        "search_notfound": (
            "Текст пройдено, жодне вікно не дало підтвердженого збігу → повертаємо "
            "`-1` за {hc} порівнянь хешів."
        ),
    },
    "en": {
        "generating": "Generating the full step-by-step code ↔ data trace (two phases)…",
        "saved": "  saved {n} frames to {sub}",
        "readme": "  README block ({doc}) updated between the WALKTHROUGH markers.",
        "phase1": "### Phase 1 — hashing: the polynomial hash of pattern «developer»",
        "phase2": "### Phase 2 — searching for «developer» in the konspekt text",
        "step": "Step",
        "hash_init": (
            "Phase 1 — **hashing**. We turn the pattern «{s}» (length {n}) into a "
            "number — its polynomial hash modulo 101. We start from `hash = 0` and "
            "add each character's contribution left to right (Horner's scheme)."
        ),
        "hash_term": (
            "Step `i = {i}`: character «{c}» (code `ord = {code}`). Power "
            "`pow(256, {pw}) % 101 = {power}`, contribution `{code}·{power} = "
            "{contrib}`. Accumulated `hash = {h}`."
        ),
        "hash_final": (
            "The hash of pattern «{s}» is computed: **{h}**. This is the number we "
            "will compare against every window's hash — instead of comparing characters."
        ),
        "search_init": (
            "Phase 2 — **search**. The hash of pattern «{p}» equals **{ph}**. A "
            "window of length {m} slides along the text; at each offset we compare "
            "the **window's hash** with {ph}. We check characters only when the "
            "hashes match."
        ),
        "search_slide": (
            "The window at offset `i = {i}` is «{w}», its hash **{hw}** ≠ {ph}. No "
            "match, so we slide on. The next hash is computed in `O(1)` (rolling): "
            "the left character leaves, the right one enters."
        ),
        "search_collision": (
            "The window `i = {i}` is «{w}», hash **{hw} = {ph}** — a HASH match! But "
            "the character check: «{w}» ≠ «{p}». This is a **COLLISION** — different "
            "strings with the same hash. This is exactly where the character check "
            "saves us from a false match: we reject it and slide on."
        ),
        "search_match": (
            "The window `i = {i}` is «{w}», hash **{hw} = {ph}**, and the check: "
            "«{w}» = «{p}» ✓ — a **real match**! We return position {i}. Summary: {hc} "
            "hash comparisons, only {cv} character checks (of which {col} a collision), "
            "{r} rolling updates."
        ),
        "search_notfound": (
            "The text is exhausted, no window gave a confirmed match → we return "
            "`-1` after {hc} hash comparisons."
        ),
    },
}
T = _TEXT[LANG]


# ---------------------------------------------------------------------------
# Побудова кадрів кожної фази з журналу (init + кроки + кульмінація)
# ---------------------------------------------------------------------------
def _hash_frames(s: str):
    """Кадри фази хешу: init + кожен доданок (term) + final."""
    h, events = polynomial_hash_steps(s)
    frames = []
    for e in events:
        if e["kind"] == "init":
            frames.append(("init", e, dict(_HL_HASH["init"])))
        elif e["kind"] == "term":
            frames.append(("term", e, dict(_HL_HASH["term"])))
        elif e["kind"] == "final":
            frames.append(("final", e, dict(_HL_HASH["final"])))
    return h, events, frames


def _search_frames(text: str, pattern: str):
    """Кадри фази пошуку: init + по кадру на кожне вікно (вердикт) + (можливий) not_found."""
    result, events = rabin_karp_search_steps(text, pattern)
    # вердикт кожного вікна за зміщенням
    verdict_by_i = {}
    for e in events:
        if e["kind"] == "collision":
            verdict_by_i[int(e["i"])] = ("collision", e)
        elif e["kind"] == "match_found":
            verdict_by_i[int(e["i"])] = ("match", e)
    frames = [("init", events[0], dict(_HL_SEARCH["init"]))]
    for e in events:
        if e["kind"] != "window":
            continue
        i = int(e["i"])
        branch, ev = verdict_by_i.get(i, ("slide", e))
        frames.append((branch, ev, dict(_HL_SEARCH[branch])))
        if branch == "match":
            break
    if result < 0:
        nf = next((e for e in events if e["kind"] == "not_found"), events[-1])
        frames.append(("not_found", nf, dict(_HL_SEARCH["not_found"])))
    return result, events, frames


# ---------------------------------------------------------------------------
# Пояснення кадру — усі числа з події журналу
# ---------------------------------------------------------------------------
def explain_hash(branch: str, e) -> str:
    if branch == "init":
        return T["hash_init"].format(s=e["s"], n=int(e["n"]))
    if branch == "final":
        return T["hash_final"].format(s=e["s"], h=int(e["hash_value"]))
    n = int(e["n"]); i = int(e["i"])
    return T["hash_term"].format(
        i=i, c=_char(e["char"]), code=int(e["code"]), pw=n - i - 1,
        power=int(e["power"]), contrib=int(e["contribution"]), h=int(e["hash_value"]))


def explain_search(branch: str, e) -> str:
    if branch == "init":
        return T["search_init"].format(p=e["pattern"], ph=int(e["pattern_hash"]),
                                       m=int(e["M"]))
    ph = int(e["pattern_hash"])
    if branch == "slide":
        return T["search_slide"].format(i=int(e["i"]), w=_word(e["window"]),
                                        hw=int(e["window_hash"]), ph=ph)
    if branch == "collision":
        return T["search_collision"].format(i=int(e["i"]), w=_word(e["window"]),
                                            hw=int(e["window_hash"]), ph=ph,
                                            p=_word(e["pattern"]))
    if branch == "match":
        return T["search_match"].format(
            i=int(e["i"]), w=_word(e["window"]), hw=int(e["window_hash"]), ph=ph,
            p=_word(e["pattern"]), hc=int(e["hash_comparisons"]),
            cv=int(e["char_verifications"]), col=int(e["collisions"]),
            r=int(e["rolls"]))
    return T["search_notfound"].format(hc=int(e["hash_comparisons"]))


# ---------------------------------------------------------------------------
# Рендер кадрів у файли + збірка markdown-блоку
# ---------------------------------------------------------------------------
def _make_step(branch: str, event, hl, *, panel: str) -> dict:
    title = hash_step_title(event) if panel == "hash" else search_step_title(event)
    return {"kind": branch, "panel": panel, "event": event, "hl": hl,
            "title": title, "caption": ""}


def render_phase(frames, panel: str, prefix: str) -> int:
    """Зберігає кадри фази у файли ``walkthrough/{prefix}_NN.png``; повертає їх число."""
    for nn, (branch, event, hl) in enumerate(frames):
        step = _make_step(branch, event, hl, panel=panel)
        fig = render_code_step(step)
        save_figure(fig, f"{_SUBDIR}/{prefix}_{nn:02d}.png")
        plt.close(fig)
    return len(frames)


def build_markdown(hash_frames, search_frames) -> str:
    parts = [T["phase1"]]
    for nn, (branch, e, _hl) in enumerate(hash_frames):
        img = f"{_IMG_PREFIX}hash_{nn:02d}.png"
        alt = hash_step_title(e)
        parts.append(f"#### {T['step']} H{nn:02d}\n\n![{alt}]({img})\n\n"
                     f"{explain_hash(branch, e)}")
    parts.append(T["phase2"])
    for nn, (branch, e, _hl) in enumerate(search_frames):
        img = f"{_IMG_PREFIX}search_{nn:02d}.png"
        alt = search_step_title(e)
        parts.append(f"#### {T['step']} S{nn:02d}\n\n![{alt}]({img})\n\n"
                     f"{explain_search(branch, e)}")
    return "\n\n".join(parts) + "\n"


def update_readme(block: str) -> str:
    """Ідемпотентно вставляє ``block`` між маркерами WALKTHROUGH у README."""
    path = os.path.join(_ROOT, _README)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if _START not in text or _END not in text:
        raise SystemExit(f"маркери {_START}/{_END} не знайдено у {_README}")
    head = text.split(_START, 1)[0]
    tail = text.split(_END, 1)[1]
    new_text = f"{head}{_START}\n\n{block}\n{_END}{tail}"
    if new_text != text:                      # не торкаємось файлу, якщо нічого не змінилось
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(new_text)
    return path


def main() -> None:
    configure_style()
    print(T["generating"])

    h, hash_events, hash_frames = _hash_frames(PATTERN)
    result, search_events, search_frames = _search_frames(TEXT, PATTERN)

    # --- інваріанти кількості та порядку кадрів (окремо для кожної фази) ------
    n_terms = sum(1 for e in hash_events if e["kind"] == "term")
    expected_hash = ["init"] + ["term"] * n_terms + ["final"]
    assert len(hash_frames) == n_terms + 2, (len(hash_frames), n_terms)
    assert [b for b, _e, _h in hash_frames] == expected_hash, "порядок хеш-кадрів"

    # очікувані вердикти вікон пошуку (із журналу)
    verdict_by_i = {}
    for e in search_events:
        if e["kind"] == "collision":
            verdict_by_i[int(e["i"])] = "collision"
        elif e["kind"] == "match_found":
            verdict_by_i[int(e["i"])] = "match"
    expected_search = ["init"]
    for e in search_events:
        if e["kind"] != "window":
            continue
        i = int(e["i"])
        branch = verdict_by_i.get(i, "slide")
        expected_search.append(branch)
        if branch == "match":
            break
    if result < 0:
        expected_search.append("not_found")
    assert [b for b, _e, _h in search_frames] == expected_search, "порядок пошук-кадрів"

    # --- 1) кожен кадр — окремим файлом ---------------------------------------
    n_hash = render_phase(hash_frames, "hash", "hash")
    n_search = render_phase(search_frames, "search", "search")
    print(T["saved"].format(n=n_hash + n_search, sub=os.path.join(_SUBDIR, "")))

    # --- 2) авто-генерація README-блоку (ідемпотентно, між маркерами) ---------
    block = build_markdown(hash_frames, search_frames)
    update_readme(block)
    print(T["readme"].format(doc=_README))

    print_saved_location()


if __name__ == "__main__":
    main()
