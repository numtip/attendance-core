from __future__ import annotations

from dataclasses import dataclass
from datetime import time

from attendance_core.dates import day_number_from_raw, parse_thai_or_gregorian_date, to_iso_date
from attendance_core.leave_parser import build_leave_detail, classify_true_leave, is_true_leave_day
from attendance_core.models import (
    AttendanceInput,
    AttendanceSource,
    DayRecord,
    EmployeeProfile,
    EmployeeSummary,
    ProcessingResult,
)
from attendance_core.policy import AttendancePolicy


def _parse_time(value: str) -> time | None:
    value = (value or "").strip()
    if not value:
        return None
    parts = value.split(":")
    hour = int(parts[0])
    minute = int(parts[1]) if len(parts) > 1 else 0
    return time(hour, minute)


def _minutes_after(start: time, end: time) -> int:
    start_minutes = start.hour * 60 + start.minute
    end_minutes = end.hour * 60 + end.minute
    return max(0, end_minutes - start_minutes)


def _minutes_before(end: time, threshold: time) -> int:
    end_minutes = end.hour * 60 + end.minute
    threshold_minutes = threshold.hour * 60 + threshold.minute
    return max(0, threshold_minutes - end_minutes)


@dataclass
class GroupedDayInput:
    employee_id: str
    employee_name: str
    department: str
    date_raw: str
    status: str
    clock_in: str
    clock_out: str
    remark: str
    source: str = AttendanceSource.CSV_IMPORT.value


def build_day_record(
    grouped: GroupedDayInput,
    policy: AttendancePolicy,
    *,
    thai_buddhist_year: bool = True,
    profile: EmployeeProfile | None = None,
) -> DayRecord:
    clock_in_time = _parse_time(grouped.clock_in)
    clock_out_time = _parse_time(grouped.clock_out)
    is_leave_day = not grouped.clock_in and not grouped.clock_out
    parsed = parse_thai_or_gregorian_date(grouped.date_raw, thai_buddhist_year=thai_buddhist_year)
    iso_date = to_iso_date(parsed) if parsed else grouped.date_raw

    record = DayRecord(
        employee_id=grouped.employee_id,
        employee_name=profile.name if profile and profile.name else grouped.employee_name,
        department=profile.department if profile and profile.department else grouped.department,
        date_raw=grouped.date_raw,
        day_number=day_number_from_raw(grouped.date_raw if "/" in grouped.date_raw else iso_date),
        status=grouped.status,
        clock_in=grouped.clock_in,
        clock_out=grouped.clock_out,
        remark=grouped.remark,
        is_leave_day=is_leave_day,
        attendance_date_iso=iso_date,
        source=grouped.source,
    )
    record.is_true_leave = is_true_leave_day(
        record,
        leave_types=policy.leave_types,
        business_statuses=policy.business_statuses,
        leave_aliases=policy.leave_aliases,
    )

    if not is_leave_day:
        if clock_in_time and clock_in_time > policy.late_after:
            record.is_late = True
            record.issue_types.append("สาย")
        if not grouped.clock_in and grouped.clock_out:
            record.is_missing_clock_in = True
            record.issue_types.append("ไม่ลงเวลาเข้า")
        if grouped.clock_in and not grouped.clock_out:
            record.is_missing_clock_out = True
            record.issue_types.append("ไม่ลงเวลาออก")
        if clock_out_time and clock_out_time < policy.early_before:
            record.is_early_leave = True
            record.issue_types.append("ออกก่อน")

    return record


def day_record_to_api_result(record: DayRecord, policy: AttendancePolicy) -> dict:
    clock_in_time = _parse_time(record.clock_in)
    clock_out_time = _parse_time(record.clock_out)
    late_minutes = _minutes_after(policy.late_after, clock_in_time) if record.is_late and clock_in_time else 0
    early_minutes = (
        _minutes_before(clock_out_time, policy.early_before) if record.is_early_leave and clock_out_time else 0
    )
    leave_type = (
        classify_true_leave(
            record.remark,
            leave_types=policy.leave_types,
            business_statuses=policy.business_statuses,
            leave_aliases=policy.leave_aliases,
        )
        if record.is_true_leave
        else None
    )

    if record.is_true_leave:
        status = "LEAVE"
    elif record.status == "วันหยุด":
        status = "HOLIDAY"
    elif record.is_late:
        status = "LATE"
    elif record.issue_types:
        status = "ISSUE"
    else:
        status = "PRESENT"

    return {
        "employee_id": record.employee_id,
        "date": record.attendance_date_iso or record.date_raw,
        "attendance_status": status,
        "late_minutes": late_minutes,
        "early_minutes": early_minutes,
        "missing_check_in": record.is_missing_clock_in,
        "missing_check_out": record.is_missing_clock_out,
        "leave_type": leave_type,
        "issues": list(record.issue_types),
    }


def input_to_grouped(day: AttendanceInput) -> GroupedDayInput:
    remark = ", ".join(dict.fromkeys(day.remarks))
    return GroupedDayInput(
        employee_id=day.employee_external_id,
        employee_name=day.employee_name,
        department=day.department,
        date_raw=day.attendance_date,
        status=day.day_status,
        clock_in=day.check_in,
        clock_out=day.check_out,
        remark=remark,
        source=day.source.value if isinstance(day.source, AttendanceSource) else str(day.source),
    )


def process_grouped_days(
    grouped_days: list[GroupedDayInput],
    policy: AttendancePolicy,
    *,
    profiles: dict[str, EmployeeProfile] | None = None,
    month: str = "",
    raw_row_count: int = 0,
    thai_buddhist_year: bool = True,
) -> ProcessingResult:
    profiles = profiles or {}
    daily_records: list[DayRecord] = []
    for grouped in grouped_days:
        profile = profiles.get(grouped.employee_id)
        daily_records.append(
            build_day_record(
                grouped,
                policy,
                thai_buddhist_year=thai_buddhist_year,
                profile=profile,
            )
        )

    employee_summaries: list[EmployeeSummary] = []
    issues = [record for record in daily_records if record.issue_types]

    for employee_id, employee_records in _group_by_employee(daily_records).items():
        first = employee_records[0]
        profile = profiles.get(employee_id)
        work_days = len(employee_records)
        leave_days = sum(1 for record in employee_records if record.is_true_leave)
        attended_days = work_days - leave_days

        employee_summaries.append(
            EmployeeSummary(
                employee_id=employee_id,
                employee_name=first.employee_name,
                department=first.department,
                work_days=work_days,
                attended_days=attended_days,
                leave_days=leave_days,
                leave_detail=build_leave_detail(
                    employee_records,
                    policy.leave_types,
                    policy.business_statuses,
                    policy.leave_aliases,
                ),
                late_count=sum(1 for record in employee_records if record.is_late),
                missing_clock_in_count=sum(1 for record in employee_records if record.is_missing_clock_in),
                missing_clock_out_count=sum(1 for record in employee_records if record.is_missing_clock_out),
                early_leave_count=sum(1 for record in employee_records if record.is_early_leave),
                position=profile.position if profile else "",
            )
        )

    if policy.sort_by_employee_id:
        employee_summaries.sort(key=lambda item: int(item.employee_id))

    return ProcessingResult(
        raw_row_count=raw_row_count or len(grouped_days),
        daily_records=daily_records,
        employee_summaries=employee_summaries,
        issues=issues,
        month=month,
    )


def process_inputs(
    inputs: list[AttendanceInput],
    policy: AttendancePolicy,
    *,
    profiles: dict[str, EmployeeProfile] | None = None,
    month: str = "",
) -> ProcessingResult:
    grouped = [input_to_grouped(item) for item in inputs]
    return process_grouped_days(grouped, policy, profiles=profiles, month=month, raw_row_count=len(inputs))


def _group_by_employee(records: list[DayRecord]) -> dict[str, list[DayRecord]]:
    grouped: dict[str, list[DayRecord]] = {}
    for record in records:
        grouped.setdefault(record.employee_id, []).append(record)
    return grouped
