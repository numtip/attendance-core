from __future__ import annotations

from datetime import date


def parse_thai_or_gregorian_date(
    date_raw: str,
    *,
    thai_buddhist_year: bool = True,
) -> date | None:
    """Parse D/M/Y from HP Premium `วัน/เวลา` or ISO `YYYY-MM-DD`."""
    value = (date_raw or "").strip()
    if not value:
        return None
    if "-" in value and len(value.split("-")) == 3:
        year, month, day = value.split("-")
        return date(int(year), int(month), int(day))

    parts = value.split("/")
    if len(parts) != 3:
        return None
    day, month, year = parts
    gregorian_year = int(year) - 543 if thai_buddhist_year and int(year) > 2400 else int(year)
    return date(gregorian_year, int(month), int(day))


def day_number_from_raw(date_raw: str) -> int:
    if "-" in date_raw:
        return int(date_raw.split("-")[2])
    return int(date_raw.strip().split("/")[0])


def to_iso_date(value: date) -> str:
    return value.isoformat()
