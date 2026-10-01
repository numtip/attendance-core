# Attendance Identity Mapping

> **Canonical documentation** — `attendance-core/docs/`

## Principles

1. Never join attendance by display name when a stable ID exists.
2. `employee_uid` (UUID) is the internal primary key for attendance facts.
3. `citizenID` is sensitive — not a public API key; do not log full values.
4. `mju-person-enrich` enriches identity only; no attendance calculation.

## Identifier matrix

| Contract field | Storage (RAE V2) | Use |
|----------------|------------------|-----|
| `employee_uid` | `employees.employee_uid` | JWT `sub`, FK |
| `employee_id` / personnel code | `employees.employee_id` | Business code |
| `facescan_id` | `employee_identifier` | HP / device id |
| `sso_subject` | `employee_identifier` (future) | SSO fallback |
| `email` | `employees.email` | Login / SSO |
| `national_id` | `employee_identifier` (encrypted) | Dedup only |

## Security

- No full citizen ID in logs or JWT.
- Synthetic fixtures only in git.

See also RAE `docs/SSO_REUSE_PLAN.md` and `employeeIdentityService.js` (Phase 2 wiring).
