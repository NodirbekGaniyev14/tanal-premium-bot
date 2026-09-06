"""Telefon raqami — yagona barqaror identifikator, shuning uchun bitta ko'rinishga
keltirilib saqlanadi: `+` va faqat raqamlar.
"""

from __future__ import annotations

import re

_DIGITS_RE = re.compile(r"\d+")

#: Mahalliy formatda kelgan O'zbekiston raqamlariga qo'shiladigan kod.
_DEFAULT_COUNTRY = "998"


def normalize_phone(value: str | None) -> str | None:
    """`+998 90 123-45-67`, `998901234567`, `901234567` → `+998901234567`."""
    if not value:
        return None

    digits = "".join(_DIGITS_RE.findall(str(value)))
    if not digits:
        return None

    if digits.startswith("00"):
        digits = digits[2:]

    # 9 xonali mahalliy raqam: 901234567
    if len(digits) == 9:
        digits = _DEFAULT_COUNTRY + digits
    # 8 bilan boshlanuvchi eski format: 8 90 123 45 67
    elif len(digits) == 10 and digits.startswith("8"):
        digits = _DEFAULT_COUNTRY + digits[1:]

    if len(digits) < 9 or len(digits) > 15:
        return None

    return "+" + digits


def mask_phone(phone: str) -> str:
    """Loglar va adminga signal uchun: `+998901234567` → `+9989012***67`."""
    if len(phone) < 6:
        return phone
    return phone[:-4] + "**" + phone[-2:]
