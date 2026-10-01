from __future__ import annotations

from attendance_core.models import AttendanceInput, AttendanceSource
from attendance_core.service import AttendanceService


def _svc() -> AttendanceService:
    return AttendanceService(
        {
            "work_start": "08:30",
            "work_end": "16:30",
            "late_after": "08:30",
            "early_before": "16:30",
            "leave_types": ["ป่วย", "กิจ", "พักผ่อน"],
            "business_statuses": ["ไปราชการ", "OT", "ประชุม"],
            "leave_type_aliases": {"ลา": "อื่นๆ"},
        }
    )


def test_missing_check_in_and_out():
    svc = _svc()
    missing_in = svc.calculate_day(
        AttendanceInput(
            employee_external_id="77",
            attendance_date="2026-06-02",
            check_out="16:30",
        )
    )
    assert missing_in.missing_check_in

    missing_out = svc.calculate_day(
        AttendanceInput(
            employee_external_id="77",
            attendance_date="2026-06-03",
            check_in="08:00",
        )
    )
    assert missing_out.missing_check_out


def test_official_business_not_counted_as_leave():
    svc = _svc()
    result = svc.calculate_day(
        AttendanceInput(
            employee_external_id="77",
            attendance_date="2026-06-04",
            remarks=["ไปราชการ"],
        )
    )
    assert not result.is_true_leave
    assert result.leave_type is None


def test_malformed_remark_still_safe():
    svc = _svc()
    result = svc.calculate_day(
        AttendanceInput(
            employee_external_id="77",
            attendance_date="2026-06-05",
            remarks=["", "???", "ป่วย(abc"],
        )
    )
    assert result.leave_type == "ป่วย"


def test_unknown_employee_id_still_evaluates():
    svc = _svc()
    result = svc.calculate_day(
        AttendanceInput(
            employee_external_id="UNKNOWN-999",
            attendance_date="2026-06-06",
            check_in="08:00",
            check_out="16:30",
            source=AttendanceSource.FACESCAN_DB,
        )
    )
    assert result.employee_id == "UNKNOWN-999"
    assert result.attendance_status == "PRESENT"
