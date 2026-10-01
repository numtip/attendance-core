# attendance-core

**Canonical source** for shared attendance business rules (Python). Version **0.1.0**.

| Repository | Responsibility |
|------------|----------------|
| **attendance-core** (this repo) | Domain rules, policy, evaluation engine, optional HTTP API |
| [attendance-report-generator](https://github.com/numtip/Attendance-Report) | CSV ingestion, reporting, Excel, HR QA |
| [RAE-Attendance-System-V2](https://github.com/numtip/RAE-Attendance-System-V2) | Auth, API, UI, persistence |
| mju-person-enrich (local/batch) | Personnel identity enrichment only |

Architecture and contracts: [`docs/`](docs/).

## Repository relationship

```text
numtip/
├── attendance-core                 ← this repo (domain rules)
├── Attendance-Report               ← Python Option A (editable / Git pin)
├── RAE-Attendance-System-V2        ← Node Option B (HTTP API)
└── mju-person-enrich               ← identity enrichment (no attendance math)
```

## Install (Python)

```bash
git clone https://github.com/numtip/attendance-core.git
cd attendance-core
python -m pip install -e ".[dev]"
```

**Editable sibling** (local monorepo folder, not merged git):

```bash
python -m pip install -e ../attendance-core
```

**CI / pinned release** (documented migration path for consumers):

```text
attendance-core @ git+https://github.com/numtip/attendance-core.git@v0.1.0
```

## Tests

```bash
python -m pytest -q
```

Uses synthetic data only (no HR CSV, no secrets).

## HTTP API (Option B)

```bash
set ATTENDANCE_POLICY_PATH=C:\path\to\settings.yaml
python -m attendance_core.api.server
```

| Variable | Default | Purpose |
|----------|---------|---------|
| `ATTENDANCE_CORE_HOST` | `127.0.0.1` | Bind address |
| `ATTENDANCE_CORE_PORT` | `8765` | Port |
| `ATTENDANCE_POLICY_PATH` | (optional) | YAML policy file |

| Method | Path |
|--------|------|
| `GET` | `/health` |
| `POST` | `/attendance/evaluate-day` |
| `POST` | `/attendance/evaluate-period` |

### Example (synthetic)

Request:

```bash
curl -s -X POST http://127.0.0.1:8765/attendance/evaluate-day ^
  -H "Content-Type: application/json" ^
  -d "{\"employee_id\":\"SYNTH-001\",\"date\":\"2026-08-03\",\"check_in\":\"08:11\",\"check_out\":\"16:36\",\"source\":\"API\"}"
```

Response shape (values from policy):

```json
{
  "employee_id": "SYNTH-001",
  "date": "2026-08-03",
  "attendance_status": "PRESENT",
  "late_minutes": 0,
  "early_minutes": 0,
  "missing_check_in": false,
  "missing_check_out": false,
  "leave_type": null,
  "issues": []
}
```

## Python API

```python
from attendance_core import AttendanceInput, AttendanceService, load_policy

policy = load_policy({"work_start": "08:30", "late_after": "08:30", "work_end": "16:30", "early_before": "16:30"})
svc = AttendanceService(policy)
result = svc.calculate_day(AttendanceInput(employee_external_id="SYNTH-1", attendance_date="2026-08-03", check_in="08:00", check_out="16:30"))
```

## Integration

### attendance-report-generator

- Imports `attendance_core` via shims in `src/engine/` and `src/parser/`.
- HP Premium pandas adapter stays in the reporting repo.
- Local: `-e ../attendance-core` in `requirements.txt`.

### RAE-Attendance-System-V2

- Does **not** duplicate rules in JavaScript.
- `ATTENDANCE_CORE_URL` → proxy `POST /api/v1/attendance/evaluate-*`.
- Fail closed (503) when Core is unavailable.

## Security / privacy

- Do not commit `.env`, tokens, real personnel CSV, citizen/national IDs, or production dumps.
- Tests and docs use synthetic IDs only.
- HP Premium daily summaries are not raw facescan event logs.

## License

Internal MJU / numtip project — see organization policy.
