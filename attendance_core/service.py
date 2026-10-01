from __future__ import annotations

from typing import Any

from attendance_core.engine import (
    build_day_record,
    day_record_to_api_result,
    input_to_grouped,
    process_grouped_days,
    process_inputs,
)
from attendance_core.models import AttendanceDayResult, AttendanceInput, EmployeeProfile, ProcessingResult
from attendance_core.policy import AttendancePolicy, load_policy


def evaluate_day(day: AttendanceInput, policy: AttendancePolicy | dict[str, Any]) -> AttendanceDayResult:
    resolved = load_policy(policy) if isinstance(policy, dict) else policy
    grouped = input_to_grouped(day)
    profile = None
    if day.employee_name or day.department:
        profile = EmployeeProfile(
            employee_id=day.employee_external_id,
            name=day.employee_name,
            department=day.department,
        )
    record = build_day_record(grouped, resolved, profile=profile)
    payload = day_record_to_api_result(record, resolved)
    return AttendanceDayResult(
        employee_id=payload["employee_id"],
        date=payload["date"],
        attendance_status=payload["attendance_status"],
        late_minutes=payload["late_minutes"],
        early_minutes=payload["early_minutes"],
        missing_check_in=payload["missing_check_in"],
        missing_check_out=payload["missing_check_out"],
        leave_type=payload["leave_type"],
        issues=payload["issues"],
        is_late=record.is_late,
        is_early_leave=record.is_early_leave,
        is_true_leave=record.is_true_leave,
        day_number=record.day_number,
        remark=record.remark,
        source=record.source,
    )


class AttendanceService:
    """Adapter surface for web apps and batch jobs."""

    def __init__(self, policy: AttendancePolicy | dict[str, Any]) -> None:
        self._policy = load_policy(policy) if isinstance(policy, dict) else policy

    def calculate_day(self, day: AttendanceInput) -> AttendanceDayResult:
        return evaluate_day(day, self._policy)

    def calculate_period(
        self,
        days: list[AttendanceInput],
        *,
        month: str = "",
        profiles: dict[str, EmployeeProfile] | None = None,
    ) -> ProcessingResult:
        return process_inputs(days, self._policy, profiles=profiles, month=month)

    def normalize_source(self, raw: str) -> str:
        return raw.strip().upper()

    def get_employee_attendance(
        self,
        employee_id: str,
        days: list[AttendanceInput],
    ) -> list[AttendanceDayResult]:
        filtered = [day for day in days if day.employee_external_id == employee_id]
        return [self.calculate_day(day) for day in filtered]

    def explain_result(self, result: AttendanceDayResult) -> dict[str, Any]:
        return {
            "employee_id": result.employee_id,
            "date": result.date,
            "status": result.attendance_status,
            "issues": result.issues,
            "leave_type": result.leave_type,
            "policy": {
                "work_start": self._policy.work_start.strftime("%H:%M"),
                "work_end": self._policy.work_end.strftime("%H:%M"),
                "late_after": self._policy.late_after.strftime("%H:%M"),
                "early_before": self._policy.early_before.strftime("%H:%M"),
            },
        }
