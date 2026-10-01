from __future__ import annotations

from attendance_core.models import DayRecord

DEFAULT_LEAVE_TYPES = [
    "ป่วย",
    "พักผ่อน",
    "กิจ",
    "คลอด",
    "บวช",
    "ลาโดยไม่รับค่าจ้าง",
    "อื่นๆ",
]

DEFAULT_BUSINESS_STATUSES = [
    "ไปราชการ",
    "ประชุม",
    "อบรม",
    "สัมมนา",
    "ปฏิบัติราชการ",
    "เวร",
    "OT",
]

DEFAULT_LEAVE_ALIASES = {
    "ลาคลอด": "คลอด",
    "ลาคลอดบุตร": "คลอด",
    "ลาบวช": "บวช",
    "ลา": "อื่นๆ",
}


def _extract_tokens(remark: str) -> list[str]:
    tokens: list[str] = []
    for part in (remark or "").replace("，", ",").split(","):
        token = part.strip().split("(")[0].strip()
        if token:
            tokens.append(token)
    return tokens


def _matches_status(token: str, statuses: list[str]) -> bool:
    for status in statuses:
        if token == status or status in token or token in status:
            return True
    return False


def _resolve_leave_label(
    token: str,
    leave_types: list[str],
    leave_aliases: dict[str, str],
) -> str | None:
    if token in leave_aliases:
        return leave_aliases[token]
    if token in leave_types:
        return token
    for leave_type in leave_types:
        if leave_type in token or token in leave_type:
            return leave_type
    for alias, canonical in leave_aliases.items():
        if token == alias or alias in token or token in alias:
            return canonical
    return None


def classify_true_leave(
    remark: str,
    leave_types: list[str] | None = None,
    business_statuses: list[str] | None = None,
    leave_aliases: dict[str, str] | None = None,
) -> str | None:
    known_leave = leave_types or DEFAULT_LEAVE_TYPES
    business = business_statuses or DEFAULT_BUSINESS_STATUSES
    aliases = leave_aliases or DEFAULT_LEAVE_ALIASES
    tokens = _extract_tokens(remark)

    if not tokens:
        return None

    leave_labels: list[str] = []
    for token in tokens:
        if _matches_status(token, business):
            continue
        label = _resolve_leave_label(token, known_leave, aliases)
        if label:
            leave_labels.append(label)

    if leave_labels:
        return leave_labels[0]

    if all(_matches_status(token, business) for token in tokens):
        return None

    return None


def is_true_leave_day(
    record: DayRecord,
    leave_types: list[str] | None = None,
    business_statuses: list[str] | None = None,
    leave_aliases: dict[str, str] | None = None,
) -> bool:
    if not record.is_leave_day:
        return False
    return (
        classify_true_leave(
            record.remark,
            leave_types=leave_types,
            business_statuses=business_statuses,
            leave_aliases=leave_aliases,
        )
        is not None
    )


def parse_leave_type(
    remark: str,
    status: str = "",
    leave_types: list[str] | None = None,
    business_statuses: list[str] | None = None,
    leave_aliases: dict[str, str] | None = None,
) -> str | None:
    return classify_true_leave(
        remark,
        leave_types=leave_types,
        business_statuses=business_statuses,
        leave_aliases=leave_aliases,
    )


def build_leave_detail(
    records: list[DayRecord],
    leave_types: list[str] | None = None,
    business_statuses: list[str] | None = None,
    leave_aliases: dict[str, str] | None = None,
) -> str | None:
    leave_records = [
        record
        for record in records
        if is_true_leave_day(record, leave_types, business_statuses, leave_aliases)
    ]
    if not leave_records:
        return None

    grouped: dict[str, list[int]] = {}
    for record in leave_records:
        leave_type = classify_true_leave(
            record.remark,
            leave_types=leave_types,
            business_statuses=business_statuses,
            leave_aliases=leave_aliases,
        )
        if leave_type:
            grouped.setdefault(leave_type, []).append(record.day_number)

    parts: list[str] = []
    for leave_type in sorted(grouped):
        days = ",".join(str(day) for day in sorted(grouped[leave_type]))
        parts.append(f"{leave_type}({days})")
    return " ".join(parts)
