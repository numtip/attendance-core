from __future__ import annotations

from attendance_core.models import AttendanceInput, AttendanceSource
from attendance_core.policy import load_policy
from attendance_core.service import AttendanceService


def _service() -> AttendanceService:
    return AttendanceService(
        load_policy(
            {
                "work_start": "08:30",
                "work_end": "16:30",
                "late_after": "08:30",
                "early_before": "16:30",
                "leave_types": ["ป่วย", "พักผ่อน", "กิจ"],
                "business_statuses": ["ไปราชการ", "OT"],
                "leave_type_aliases": {"ลา": "อื่นๆ"},
            }
        )
    )


def test_normal_workday():
    svc = _service()
    result = svc.calculate_day(
        AttendanceInput(
            employee_external_id="1001",
            attendance_date="2026-08-03",
            check_in="08:11",
            check_out="16:36",
            day_status="WORKDAY",
            source=AttendanceSource.API,
        )
    )
    assert result.attendance_status == "PRESENT"
    assert result.late_minutes == 0
    assert not result.missing_check_in


def test_late_and_early():
    svc = _service()
    late = svc.calculate_day(
        AttendanceInput(
            employee_external_id="1001",
            attendance_date="2026-08-04",
            check_in="09:00",
            check_out="16:36",
        )
    )
    assert late.is_late
    assert late.late_minutes == 30

    early = svc.calculate_day(
        AttendanceInput(
            employee_external_id="1001",
            attendance_date="2026-08-05",
            check_in="08:00",
            check_out="16:00",
        )
    )
    assert early.is_early_leave
    assert early.early_minutes == 30


def test_sick_leave_without_clocks():
    svc = _service()
    result = svc.calculate_day(
        AttendanceInput(
            employee_external_id="1001",
            attendance_date="2026-08-06",
            remarks=["ป่วย"],
            day_status="WORKDAY",
        )
    )
    assert result.is_true_leave
    assert result.leave_type == "ป่วย"


def test_buddhist_date_boundary_iso():
    svc = _service()
    result = svc.calculate_day(
        AttendanceInput(
            employee_external_id="1001",
            attendance_date="3/8/2569",
            check_in="08:00",
            check_out="16:30",
        )
    )
    assert result.date == "2026-08-03"


def test_thai_holiday_status():
    svc = _service()
    result = svc.calculate_day(
        AttendanceInput(
            employee_external_id="1001",
            attendance_date="2026-08-07",
            day_status="วันหยุด",
        )
    )
    assert result.attendance_status == "HOLIDAY"
