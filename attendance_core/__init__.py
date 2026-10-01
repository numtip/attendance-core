"""Attendance domain core — no I/O, web, or pandas dependencies."""

from attendance_core.models import (
    AttendanceDayResult,
    AttendanceInput,
    AttendanceSource,
    DayRecord,
    EmployeeSummary,
    ProcessingResult,
)
from attendance_core.policy import AttendancePolicy, load_policy
from attendance_core.service import AttendanceService, evaluate_day

__all__ = [
    "AttendanceDayResult",
    "AttendanceInput",
    "AttendancePolicy",
    "AttendanceService",
    "AttendanceSource",
    "DayRecord",
    "EmployeeSummary",
    "ProcessingResult",
    "evaluate_day",
    "load_policy",
]
