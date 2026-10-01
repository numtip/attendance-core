# Attendance Integration Plan

> **Canonical documentation** — `attendance-core/docs/`

## Phase 1

1. Standalone `attendance-core` package (this repo).
2. `attendance-report-generator` shims → `attendance_core`.
3. HTTP API for RAE V2 (`python -m attendance_core.api.server`).
4. RAE routes: `POST /api/v1/attendance/evaluate-day|evaluate-period|explain`.

## Phase 2

- Wire `employee_identifier` in RAE V2.
- Ingestion worker: source adapters → Core → `daily_attendance`.
- Person sync via `mju-person-enrich` (identity only).

## Dependency migration path

| Stage | `attendance-report-generator` |
|-------|-------------------------------|
| **Local dev** | `-e ../attendance-core` in `requirements.txt` (sibling checkout) |
| **CI / release** | Pin Git tag, e.g. `attendance-core @ git+https://github.com/numtip/attendance-core.git@v0.1.0` |

Do not assume a sibling folder exists on GitHub Actions without declaring the Git dependency or checking out a second repository in workflow.

## Regression contract

| Suite | Baseline |
|-------|----------|
| `attendance-core` | 9 pytest tests (synthetic) |
| `attendance-report-generator` | 53 pytest tests |
| RAE backend | 21 passed, 3 skipped (MariaDB env) |

## Non-goals

- Merging git repositories
- Production DB migration or deploy
- Real HR CSV / citizen ID in git
