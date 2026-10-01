from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from attendance_core.models import AttendanceInput, AttendanceSource
from attendance_core.policy import load_policy_from_yaml
from attendance_core.service import AttendanceService


def _default_policy_path() -> Path:
    env = os.environ.get("ATTENDANCE_POLICY_PATH", "").strip()
    if env:
        return Path(env)
    candidate = Path(__file__).resolve().parents[3] / "attendance-report-generator" / "config" / "settings.yaml"
    if candidate.exists():
        return candidate
    return Path(__file__).resolve().parents[1] / "default_policy.yaml"


def _load_service() -> AttendanceService:
    path = _default_policy_path()
    if path.exists():
        return AttendanceService(load_policy_from_yaml(path))
    return AttendanceService(
        {
            "work_start": "08:30",
            "work_end": "16:30",
            "late_after": "08:30",
            "early_before": "16:30",
        }
    )


SERVICE = _load_service()


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length else b"{}"
    return json.loads(raw.decode("utf-8") or "{}")


def _send_json(handler: BaseHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def _input_from_payload(payload: dict[str, Any]) -> AttendanceInput:
    remarks = payload.get("remarks") or []
    if isinstance(remarks, str):
        remarks = [remarks]
    source_raw = str(payload.get("source", AttendanceSource.API.value))
    try:
        source = AttendanceSource(source_raw)
    except ValueError:
        source = AttendanceSource.API
    return AttendanceInput(
        employee_external_id=str(payload.get("employee_id", "")),
        attendance_date=str(payload.get("date", "")),
        check_in=str(payload.get("check_in", "") or ""),
        check_out=str(payload.get("check_out", "") or ""),
        day_status=str(payload.get("day_status", "WORKDAY")),
        remarks=list(remarks),
        source=source,
        employee_name=str(payload.get("employee_name", "") or ""),
        department=str(payload.get("department", "") or ""),
    )


class AttendanceCoreHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            _send_json(self, 200, {"ok": True, "service": "attendance-core"})
            return
        _send_json(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        try:
            payload = _read_json(self)
        except json.JSONDecodeError:
            _send_json(self, 400, {"error": "invalid_json"})
            return

        if self.path == "/attendance/evaluate-day":
            day = _input_from_payload(payload)
            if not day.employee_external_id or not day.attendance_date:
                _send_json(self, 400, {"error": "employee_id and date are required"})
                return
            result = SERVICE.calculate_day(day)
            _send_json(
                self,
                200,
                {
                    "employee_id": result.employee_id,
                    "date": result.date,
                    "attendance_status": result.attendance_status,
                    "late_minutes": result.late_minutes,
                    "early_minutes": result.early_minutes,
                    "missing_check_in": result.missing_check_in,
                    "missing_check_out": result.missing_check_out,
                    "leave_type": result.leave_type,
                    "issues": result.issues,
                },
            )
            return

        if self.path == "/attendance/evaluate-period":
            days_payload = payload.get("days") or []
            if not isinstance(days_payload, list):
                _send_json(self, 400, {"error": "days must be a list"})
                return
            days = [_input_from_payload(item) for item in days_payload]
            period = SERVICE.calculate_period(days, month=str(payload.get("month", "")))
            _send_json(
                self,
                200,
                {
                    "month": period.month,
                    "raw_row_count": period.raw_row_count,
                    "issue_count": len(period.issues),
                    "employee_count": len(period.employee_summaries),
                    "daily_records": [
                        {
                            "employee_id": record.employee_id,
                            "date": record.attendance_date_iso or record.date_raw,
                            "issues": record.issue_types,
                            "is_late": record.is_late,
                            "is_true_leave": record.is_true_leave,
                        }
                        for record in period.daily_records
                    ],
                },
            )
            return

        _send_json(self, 404, {"error": "not_found"})


def main() -> None:
    host = os.environ.get("ATTENDANCE_CORE_HOST", "127.0.0.1")
    port = int(os.environ.get("ATTENDANCE_CORE_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), AttendanceCoreHandler)
    print(f"attendance-core API listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
