from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AttendancePolicy:
    work_start: time
    work_end: time
    late_after: time
    early_before: time
    ignore_holidays: bool
    sort_by_employee_id: bool
    leave_types: list[str]
    business_statuses: list[str]
    leave_aliases: dict[str, str]


def _parse_time(value: str, default: time) -> time:
    value = (value or "").strip()
    if not value:
        return default
    hour, minute = value.split(":")
    return time(int(hour), int(minute))


def load_policy(settings: dict[str, Any]) -> AttendancePolicy:
    work_start = _parse_time(settings.get("work_start", "08:30"), time(8, 30))
    work_end = _parse_time(settings.get("work_end", "16:30"), time(16, 30))
    return AttendancePolicy(
        work_start=work_start,
        work_end=work_end,
        late_after=_parse_time(settings.get("late_after", settings.get("work_start", "08:30")), work_start),
        early_before=_parse_time(
            settings.get("early_before", settings.get("work_end", "16:30")),
            work_end,
        ),
        ignore_holidays=bool(settings.get("ignore_holidays", True)),
        sort_by_employee_id=bool(settings.get("sort_by_employee_id", True)),
        leave_types=list(settings.get("leave_types", [])),
        business_statuses=list(settings.get("business_statuses", [])),
        leave_aliases=dict(settings.get("leave_type_aliases", {})),
    )


def load_policy_from_yaml(path: Path) -> AttendancePolicy:
    with path.open(encoding="utf-8") as handle:
        return load_policy(yaml.safe_load(handle) or {})


# Backward-compatible alias used by reporting shims
AttendanceRules = AttendancePolicy
load_rules = load_policy
