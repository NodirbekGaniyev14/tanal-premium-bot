from __future__ import annotations

import pytest

from app.utils.phone import mask_phone, normalize_phone


@pytest.mark.parametrize(
    "raw",
    [
        "+998901234567",
        "998901234567",
        "+998 90 123 45 67",
        "+998-90-123-45-67",
        "00998901234567",
        "901234567",
        "8901234567",
        " (998) 90 1234567 ",
    ],
)
def test_normalize(raw: str) -> None:
    assert normalize_phone(raw) == "+998901234567"


@pytest.mark.parametrize("raw", ["", None, "salom", "12"])
def test_normalize_invalid(raw: str | None) -> None:
    assert normalize_phone(raw) is None


def test_mask() -> None:
    assert mask_phone("+998901234567") == "+99890123**67"
