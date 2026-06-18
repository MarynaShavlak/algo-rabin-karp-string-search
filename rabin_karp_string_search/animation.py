"""Складання анімацій із кадрів matplotlib: GIF (завжди) + MP4 (за наявності ffmpeg).

Кадри малюють ті самі функції зі :mod:`rabin_karp_string_search.visualization` і
:mod:`rabin_karp_string_search.walkthrough` (``draw_hash_build_step``,
``draw_rolling_window``, ``render_code_step`` тощо) — цей модуль лише «зшиває»
готові фігури в один зациклений GIF через Pillow, а за можливості додатково
кодує ту саму послідовність кадрів у **MP4** (через ``ffmpeg``).

Чому окремий модуль: :mod:`…core` лишається чистим алгоритмом,
:mod:`…visualization` відповідає за статичні рисунки, а збірка анімацій (єдине
місце, що залежить від Pillow/ffmpeg) винесена сюди, щоб не змішувати
відповідальності.

Ключова деталь коректного GIF — **усі кадри мусять мати однаковий розмір у
пікселях**. Тому при рендері кадрів навмисно НЕ використовуємо
``bbox_inches="tight"`` (він обрізає по-різному), а покладаємось на фіксований
``figsize × dpi``. Палітра будується одразу з усіх кадрів, щоб акценти, які
з'являються лише на пізніх кадрах (зелений збіг, червона колізія, оранжевий збіг
хешу), не загубилися.

Два формати — навіщо:

* **GIF** (writer ``pillow``) — працює **скрізь без додаткових залежностей**
  (Pillow тягнеться разом із matplotlib), рендериться інлайн у будь-якому
  README/GitHub. Це «гарантований» формат.
* **MP4** (кодек ``libx264`` через ``ffmpeg``) — менший за розміром і дає плеєр
  із контролами, але потребує ``ffmpeg``. Тому загорнутий у ``try/except``:
  немає ffmpeg → MP4 тихо пропускається, GIF лишається. Збірка ніколи не падає
  через відсутність ffmpeg. Бінарник беремо системний, а якщо його немає —
  з pip-пакета ``imageio-ffmpeg`` (без apt/sudo).
"""

from __future__ import annotations

import io
import os
import shutil
import subprocess
from typing import List, Optional, Sequence, Union

import matplotlib.pyplot as plt
from PIL import Image

from .i18n import t
from .style import GIF_DPI

__all__ = ["save_gif", "save_animation"]


# ---------------------------------------------------------------------------
# Рендер кадрів (спільний для GIF і MP4)
# ---------------------------------------------------------------------------
def _figure_to_image(fig: "plt.Figure", dpi: int) -> Image.Image:
    """Рендерить фігуру matplotlib у растрове зображення (RGB) та закриває її.

    ``bbox_inches`` не задаємо навмисно: розмір кадру має бути сталим
    (``figsize × dpi``), інакше GIF «стрибатиме» між кадрами.
    """
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    plt.close(fig)
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def _render_frames(figures: Sequence["plt.Figure"], dpi: int) -> List[Image.Image]:
    """Перетворює список фігур на список RGB-кадрів однакового розміру (закриваючи їх).

    Спільний крок для GIF та MP4 — рендеримо рівно раз, щоб обидва формати
    отримали ідентичну послідовність кадрів (і щоб двічі не малювати фігури).
    """
    frames = [_figure_to_image(fig, dpi) for fig in figures]
    size = frames[0].size
    return [f if f.size == size else f.resize(size) for f in frames]


def _shared_palette(frames: Sequence[Image.Image], colors: int) -> Image.Image:
    """Будує спільну палітру з УСІХ кадрів.

    Зелені (збіги), червоні (колізії) та оранжеві (збіги хешу) пікселі з'являються
    лише на частині кадрів; якщо взяти палітру з одного кадру, ці кольори можуть
    «злитися» в сірий. Тому складаємо кадри в одне високе полотно й квантуємо разом.
    """
    width = max(f.width for f in frames)
    canvas = Image.new("RGB", (width, sum(f.height for f in frames)), "white")
    y = 0
    for f in frames:
        canvas.paste(f, (0, y))
        y += f.height
    return canvas.quantize(colors=colors, method=Image.Quantize.MEDIANCUT)


# ---------------------------------------------------------------------------
# Запис GIF
# ---------------------------------------------------------------------------
def _write_gif(
    frames: Sequence[Image.Image],
    path: str,
    durations: Union[int, Sequence[int]],
    *,
    colors: int = 128,
    loop: int = 0,
) -> None:
    """Зшиває готові RGB-кадри у зациклений GIF зі спільною палітрою."""
    palette = _shared_palette(frames, colors)
    paletted = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    paletted[0].save(
        path,
        save_all=True,
        append_images=paletted[1:],
        duration=list(durations) if not isinstance(durations, int) else durations,
        loop=loop,
        optimize=True,
        disposal=2,  # кожен кадр повністю замінює попередній (без «привидів»)
    )


def save_gif(
    figures: List["plt.Figure"],
    path: str,
    durations: Union[int, Sequence[int]],
    *,
    dpi: int = GIF_DPI,
    colors: int = 128,
    loop: int = 0,
) -> None:
    """Зшиває список фігур matplotlib у зациклений GIF і зберігає у ``path``.

    Усі передані фігури будуть **закриті** (``plt.close``) у процесі рендера.

    :param figures: кадри анімації — кожен окрема :class:`matplotlib.figure.Figure`.
    :param path: куди зберегти ``.gif``.
    :param durations: тривалість кадру(ів) у мілісекундах — одне число (однаково
        для всіх) або послідовність по одному значенню на кадр.
    :param dpi: роздільність рендера (за замовчуванням нижча за статичні рисунки).
    :param colors: розмір спільної палітри GIF.
    :param loop: кількість повторів; ``0`` — нескінченний цикл.
    """
    if not figures:
        raise ValueError("save_gif: немає жодного кадру для анімації.")
    frames = _render_frames(figures, dpi)
    _write_gif(frames, path, durations, colors=colors, loop=loop)


# ---------------------------------------------------------------------------
# Запис MP4 (через ffmpeg)
# ---------------------------------------------------------------------------
def _resolve_ffmpeg() -> Optional[str]:
    """Шлях до ``ffmpeg``: системний у пріоритеті, інакше бінарник imageio-ffmpeg.

    Повертає ``None``, якщо ffmpeg недоступний ні системно, ні через pip-пакет —
    тоді MP4 просто пропускається (GIF усе одно збирається).
    """
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg  # опційна залежність (extra [video])
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return None


def _even(img: Image.Image, size: "tuple[int, int]") -> Image.Image:
    """Доповнює кадр білим до парних розмірів (``libx264``/``yuv420p`` цього вимагає)."""
    if img.size == size:
        return img
    canvas = Image.new("RGB", size, "white")
    canvas.paste(img, (0, 0))
    return canvas


def _write_mp4(
    frames: Sequence[Image.Image],
    path: str,
    durations: Union[int, Sequence[int]],
    *,
    fps: int,
    crf: int,
    ffmpeg: str,
) -> None:
    """Кодує послідовність RGB-кадрів у MP4 (H.264) через ffmpeg зі stdin.

    MP4 хоче сталу частоту кадрів, а наші кадри мають різну тривалість. Тому
    працюємо на сталих ``fps`` і **повторюємо** кожен кадр стільки разів, скільки
    треба, щоб відтворити його тривалість (квант = ``1000 / fps`` мс). Так
    змінні затримки GIF точно переносяться у сталочастотний MP4.
    """
    quantum_ms = 1000.0 / fps
    n = len(frames)
    durs = list(durations) if not isinstance(durations, int) else [durations] * n

    w, h = frames[0].size
    even_size = (w + (w % 2), h + (h % 2))  # парні сторони для yuv420p

    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{even_size[0]}x{even_size[1]}", "-r", str(fps),
        "-i", "-",                       # кадри читаємо зі stdin
        "-an",                           # без аудіо
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-crf", str(crf), "-preset", "slow",
        "-movflags", "+faststart",       # перемотка/стрімінг із першого байта
        path,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for img, dur in zip(frames, durs):
            data = _even(img, even_size).tobytes()
            reps = max(1, int(round(dur / quantum_ms)))
            for _ in range(reps):
                proc.stdin.write(data)
    finally:
        if proc.stdin:
            proc.stdin.close()
        ret = proc.wait()
    if ret != 0:
        raise RuntimeError(f"ffmpeg exited with code {ret}")


# ---------------------------------------------------------------------------
# Єдина точка входу: GIF (завжди) + MP4 (за можливості)
# ---------------------------------------------------------------------------
def save_animation(
    figures: List["plt.Figure"],
    gif_path: str,
    durations: Union[int, Sequence[int]],
    *,
    mp4_path: Optional[str] = None,
    dpi: int = GIF_DPI,
    colors: int = 128,
    loop: int = 0,
    mp4_fps: int = 10,
    mp4_crf: int = 18,
) -> Optional[str]:
    """Зрендерити кадри **раз** і записати GIF (завжди) та MP4 (якщо можливо).

    Усі передані фігури будуть **закриті** у процесі рендера.

    :param gif_path: куди зберегти ``.gif`` (рендериться завжди).
    :param mp4_path: куди зберегти ``.mp4``; ``None`` — MP4 не потрібен.
    :param mp4_fps: стала частота кадрів MP4 (квант тривалості = ``1000/fps`` мс).
    :param mp4_crf: якість H.264 (менше = краще; 18 — майже без втрат для схем).
    :returns: шлях до записаного MP4 або ``None`` (MP4 не просили / ffmpeg немає /
        кодування не вдалося). GIF у будь-якому разі записано.
    """
    if not figures:
        raise ValueError("save_animation: немає жодного кадру для анімації.")
    frames = _render_frames(figures, dpi)
    _write_gif(frames, gif_path, durations, colors=colors, loop=loop)

    if mp4_path is None:
        return None
    name = os.path.basename(mp4_path)
    ffmpeg = _resolve_ffmpeg()
    if ffmpeg is None:
        print(t("  ({name} пропущено — ffmpeg недоступний; pip install imageio-ffmpeg для відео)").format(name=name))
        return None
    try:
        _write_mp4(frames, mp4_path, durations, fps=mp4_fps, crf=mp4_crf, ffmpeg=ffmpeg)
        return mp4_path
    except Exception as exc:  # noqa: BLE001 — MP4 best-effort: GIF уже є, не валимо збірку
        print(t("  ({name} пропущено: {err})").format(name=name, err=exc))
        return None
