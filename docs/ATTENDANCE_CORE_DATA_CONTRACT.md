# Attendance Core Data Contract

> **Canonical documentation** — `https://github.com/numtip/attendance-core/tree/main/docs`

## Attendance sources

| Source | Description |
|--------|-------------|
| `CSV_IMPORT` | HP Premium Time **daily summary** CSV (not raw CHECKINOUT events) |
| `FACESCAN_DB` | Pre-aggregated or corrected rows from facescan DB pipeline |
| `API` | Manual/API submissions via RAE |
| `MANUAL_CORRECTION` | HR corrections |

HP times such as `08:11` / `16:36` on a summary row are **already aggregated** check-in/out for that day, not individual scan events.

## Input DTO (Python)

```python
AttendanceInput(
    employee_external_id: str,
    attendance_date: str,
    check_in: str = "",
    check_out: str = "",
    day_status: str = "WORKDAY",
    late_duration: str = "",
    early_duration: str = "",
    remarks: list[str] = [],
    source: AttendanceSource = AttendanceSource.API,
)
```

## Evaluate-day API (HTTP)

**POST** `/attendance/evaluate-day`

Request (synthetic example):

```json
{
  "employee_id": "SYNTH-1001",
  "date": "2026-08-03",
  "check_in": "08:11:00",
  "check_out": "16:36:00",
  "day_status": "WORKDAY",
  "remarks": [],
  "source": "API"
}
```

Response fields are derived from policy — not fixed literals.

**POST** `/attendance/evaluate-period` — `{ "month": "2026-08", "days": [ ... ] }`.

## Policy object

Domain keys from shared YAML shape (`AttendancePolicy`).

## Date rules

Ingestion may pass Buddhist dates; core normalizes to Gregorian ISO internally. Example: `3/8/2569` → `2026-08-03`.
