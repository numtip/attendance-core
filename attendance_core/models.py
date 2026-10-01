from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AttendanceSource(str, Enum):
    CSV_IMPORT = "CSV_IMPORT"
    FACESCAN_DB = "FACESCAN_DB"
    API = "API"
    MANUAL_CORRECTION = "MANUAL_CORRECTION"


@dataclass
class AttendanceInput:
    employee_external_id: str
    attendance_date: str
    check_in: str = ""
    check_out: str = ""
    day_status: str = "WORKDAY"
    late_duration: str = ""
    early_duration: str = ""
    remarks: list[str] = field(default_factory=list)
    source: AttendanceSource = AttendanceSource.API
    employee_name: str = ""
    department: str = ""


@dataclass
class AttendanceDayResult:
    employee_id: str
    date: str
    attendance_status: str
    late_minutes: int
    early_minutes: int
    missing_check_in: bool
    missing_check_out: bool
    leave_type: str | None
    issues: list[str] = field(default_factory=list)
    is_late: bool = False
    is_early_leave: bool = False
    is_true_leave: bool = False
    day_number: int = 0
    remark: str = ""
    source: str = AttendanceSource.API.value


@dataclass
class EmployeeProfile:
    employee_id: str
    name: str = ""
    department: str = ""
    position: str = ""


@dataclass
class DayRecord:
    employee_id: str
    employee_name: str
    department: str
    date_raw: str
    day_number: int
    status: str
    clock_in: str
    clock_out: str
    remark: str
    is_late: bool = False
    is_missing_clock_in: bool = False
    is_missing_clock_out: bool = False
    is_early_leave: bool = False
    is_leave_day: bool = False
    is_true_leave: bool = False
    issue_types: list[str] = field(default_factory=list)
    attendance_date_iso: str = ""
    source: str = AttendanceSource.CSV_IMPORT.value


@dataclass
class EmployeeSummary:
    employee_id: str
    employee_name: str
    department: str
    work_days: int
    attended_days: int
    leave_days: int
    leave_detail: str | None
    late_count: int
    missing_clock_in_count: int
    missing_clock_out_count: int
    early_leave_count: int
    position: str = ""


@dataclass
class ProcessingResult:
    raw_row_count: int
    daily_records: list[DayRecord]
    employee_summaries: list[EmployeeSummary]
    issues: list[DayRecord]
    month: str = ""
