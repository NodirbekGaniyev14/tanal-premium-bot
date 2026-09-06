"""Adolatli baholash uchun normalizatsiya.

Qoidalar ketma-ket qo'llanadi:
  * bosh/kichik harf, ortiqcha bo'shliq, tinish belgilari e'tiborsiz
  * artikllar (a / an / the) tashlanadi
  * bo'shliq va defis e'tiborsiz — "car park" = "carpark" = "car-park"
  * raqam ↔ so'z — "15" = "fifteen", "twenty five" = "25"
  * TRUE / FALSE / NOT GIVEN qisqartmalari — "T" = "TRUE", "NG" = "NOT GIVEN"
  * kalitdagi muqobillar — `accept_also` ustuni (nuqtali vergul bilan)
"""

from __future__ import annotations

import re
import unicodedata

_ARTICLES = {"a", "an", "the"}

_UNITS: dict[str, int] = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_TENS: dict[str, int] = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fourty": 40,  # keng tarqalgan xato
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}

#: TRUE / FALSE / NOT GIVEN va YES / NO / NOT GIVEN qisqartmalari.
_SHORTHAND: dict[str, str] = {
    "t": "true",
    "f": "false",
    "ng": "not given",
    "n g": "not given",
    "notgiven": "not given",
    "y": "yes",
    "true": "true",
    "false": "false",
    "yes": "yes",
    "no": "no",
}

_APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "`": "'", "´": "'"})
_KEEP_RE = re.compile(r"[^0-9a-z'\s/-]+")
_SPACE_RE = re.compile(r"\s+")


def _words_to_digits(tokens: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token in _TENS:
            value = _TENS[token]
            nxt = tokens[i + 1] if i + 1 < len(tokens) else ""
            if nxt in _UNITS and 1 <= _UNITS[nxt] <= 9:
                value += _UNITS[nxt]
                i += 1
            out.append(str(value))
        elif token in _UNITS:
            out.append(str(_UNITS[token]))
        else:
            out.append(token)
        i += 1
    return out


def canon(value: str) -> str:
    """Javobni solishtirish uchun kanonik ko'rinishga keltiradi (bo'shliqlar saqlanadi)."""
    if not value:
        return ""

    text = unicodedata.normalize("NFKC", value).translate(_APOSTROPHES).lower()
    text = text.replace("‐", "-").replace("–", "-").replace("—", "-")
    text = _KEEP_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text).strip()
    if not text:
        return ""

    if text in _SHORTHAND:
        return _SHORTHAND[text]

    tokens = [t for t in re.split(r"[\s]+", text) if t]
    # defis bilan yozilgan sonlar: "twenty-five" → "twenty five"
    expanded: list[str] = []
    for token in tokens:
        if "-" in token and any(p in _TENS or p in _UNITS for p in token.split("-")):
            expanded.extend(p for p in token.split("-") if p)
        else:
            expanded.append(token)

    # Artikllar tashlanadi, lekin variantli javob "A" ning o'zi artikl emas —
    # shuning uchun hamma token artikl bo'lsa, matn o'z holicha qoladi.
    without_articles = [t for t in expanded if t not in _ARTICLES]
    if without_articles:
        expanded = without_articles

    expanded = _words_to_digits(expanded)
    result = " ".join(expanded).strip()
    return _SHORTHAND.get(result, result)


def compare_key(value: str) -> str:
    """Solishtirish kaliti — bo'shliq va defisdan xoli."""
    return canon(value).replace(" ", "").replace("-", "")


def expected_variants(answer: str, accept_also: str | None = None) -> list[str]:
    """Kalitdagi asosiy javob + `accept_also` muqobillari."""
    variants = [answer]
    if accept_also:
        variants.extend(part for part in re.split(r"[;|]", accept_also))
    return [v.strip() for v in variants if v and v.strip()]


def is_match(given: str, answer: str, accept_also: str | None = None) -> bool:
    """O'quvchi javobi kalitga mos keladimi."""
    if not given:
        return False
    key = compare_key(given)
    if not key:
        return False
    return any(compare_key(v) == key for v in expected_variants(answer, accept_also))
