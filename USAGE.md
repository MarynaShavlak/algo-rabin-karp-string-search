# Швидкий старт

**🇺🇦 Українська**  ·  [🇬🇧 English](USAGE.en.md)

> Частина документації проєкту [«Алгоритм Рабіна-Карпа (Rabin-Karp, хешування): покроковий розбір»](README.md). Тут — команди встановлення, запуску прикладів і тестів. Структуру репозиторію див. у [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

> **Потрібен Python ≥ 3.8.** Код використовує `from __future__ import annotations`, тож працює на 3.8+ (розробляється й тестується на 3.12).

```bash
# 1. Залежності
pip install -r requirements.txt
# або встановити пакет у режимі розробки:
pip install -e .
# (опційно) MP4-відео анімацій без root — додає ffmpeg із пакета imageio-ffmpeg:
pip install -e ".[video]"

# 2. Відтворити всі рисунки й текстові виводи (українською → docs/images/)
python examples/00_intuition.py            # інтуїція: рядок → хеш; ідея ковзного вікна
python examples/01_polynomial_hash.py      # ФАЗА 1: поліноміальний хеш (abc→6382179→90; 35, 82)
python examples/02_search.py               # ФАЗА 2: конспект-приклад «developer» → 8
python examples/03_rolling_collisions.py   # rolling vs перерахунок; КОЛІЗІЇ; модульна арифметика
python examples/04_complexity.py           # складність + порівняння ЧОТИРЬОХ алгоритмів
python examples/05_code_walkthrough.py     # панелі «код ↔ дані» обох функцій
python examples/06_full_walkthrough.py     # повне трасування конспекту (21 кадр) + авто-блок у README

# 3. Те саме англійською (→ docs/images/en/) — додайте аргумент `en`:
python examples/01_polynomial_hash.py en
python examples/06_full_walkthrough.py en
```

Сім скриптів разом генерують **44 статичні рисунки** (`.png`, зокрема 21 кадр повного трасування в `docs/images/walkthrough/`), **7 GIF-анімацій** (`.gif`) і **7 MP4-відео** (`.mp4`) у [`docs/images/`](docs/images) та друкують текстові виводи в консоль; з аргументом `en` ті самі медіа англійською потрапляють у [`docs/images/en/`](docs/images/en). Приклад `06_full_walkthrough.py` додатково оновлює блок повного трасування в README між маркерами `<!-- WALKTHROUGH:START/END -->` (ідемпотентно). Виконуються за кілька секунд (анімації — до пів хвилини). **MP4** кодуються лише за наявності `ffmpeg` (системного або з `imageio-ffmpeg`); без нього збираються самі GIF — збірка не падає.

Перевірити коректність алгоритму (результати звірено з вбудованим `str.find()`):

```bash
python tests/test_core.py     # коректність ядра (без зовнішніх залежностей)
python tests/test_smoke.py    # smoke: рендер, GIF та i18n не падають (matplotlib, pillow)
# або обидва через pytest (pip install -e ".[dev]"):
pytest
```

Тести `test_core.py` покривають збіг поліноміального хешу з еталонами конспекту (`abc → 90`, `developer → 35`, `general → 82`, `abc` без модуля → `6382179`); збіг `rabin_karp_search` із вбудованим `str.find()` (усі кейси + серія випадкових входів); відтворення конспекту (`rabin_karp_search("Being a developer is not easy", "developer") == 8`); **критичний інваріант** (rolling-хеш кожного вікна == `polynomial_hash` цього вікна, порахований з нуля); **колізії** (знайдена пара різних рядків з однаковим хешем не дає хибного збігу — char-перевірка рятує); `rabin_karp_search_all` (усі входження); **узгодженість чотирьох алгоритмів** (`RK == наївний == KMP == Боєра-Мура == str.find()` на випадкових входах); лічильники (best/avg — мало char-перевірок, worst під малим модулем — багато); крайові випадки (порожній шаблон, шаблон довший за текст → `-1`, шаблон == текст → `0`, один символ). Smoke-тести `test_smoke.py` перевіряють, що всі функції малювання обох фаз і збірка GIF виконуються без помилок, інваріант повного трасування, а **всі кириличні підписи мають англійський переклад** (аудит `missing_translations`).

Мінімальне використання як бібліотеки:

```python
from rabin_karp_string_search import polynomial_hash, rabin_karp_search, rabin_karp_search_all

print(polynomial_hash("abc"))            # 90
print(polynomial_hash("developer"))      # 35
print(rabin_karp_search("Being a developer is not easy", "developer"))  # 8
print(rabin_karp_search_all("she sells sea shells by the sea shore", "sea"))  # [10, 28]
```
