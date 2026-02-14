# Django Security Release Closeout (2026-02-03)

Date: 2026-02-14
Scope: /Users/egorfedorov/Documents/Programs/club
Related advisory: https://www.djangoproject.com/weblog/2026/feb/03/security-releases/
Related audit report: security_django_release_2026_02_03_report.md

## Summary

- Upgrade to Django 4.2.28 completed to address the 2026-02-03 security release.
- Closeout requires formal evidence of testing, post-deploy stability, and rollback readiness.
- Phase 2 (Python 3.10+ and Django 5.2 LTS) is documented separately.

## CVE Coverage Mapping

The advisory includes six CVEs. Applicability for this codebase is covered in the audit report.
Upgrade to Django 4.2.28 covers the patched branch for relevant CVEs.

- CVE-2025-13473 (mod_wsgi timing enumeration): not observed in repo usage.
- CVE-2025-14550 (ASGI repeated headers DoS): relevant; fixed by Django 4.2.28.
- CVE-2026-1207 (PostGIS raster lookup SQLi): not observed.
- CVE-2026-1285 (Truncator HTML methods DoS): not observed.
- CVE-2026-1287 (FilteredRelation alias SQLi): not observed.
- CVE-2026-1312 (order_by + FilteredRelation alias SQLi): not observed.

## Code Changes (Commit References)

Primary change:
- b50337c deps: upgrade Django to 4.2.28 and align test DB baseline

Follow-up stabilization:
- 252df84 tests/auth: restore legacy login flow and update CSRF test fixtures
- 03bd72f Fix club outage post-commit
- 43ad075 build: pin virtualenv for pipenv 2021 compatibility

## Closeout Evidence

Status legend: pending, complete, blocked.

- CI green on branch club: pending
  Evidence: CI run URL or artifact ID
- manage.py check --deploy (prod profile): pending
  Evidence: command output attached
- manage.py test (targeted auth/CSRF/payments/webhooks/queue): pending
  Evidence: command output attached
- Production rollout confirmed on branch club: pending
  Evidence: deploy log or release tag
- Post-rollout monitoring window (24h) stable: pending
  Evidence: dashboard links and snapshot values

## Production Closeout Checklist

- Metrics baseline captured before deploy (5xx, p95, CPU, memory, restarts).
- Post-deploy metrics at T+1h are within baseline tolerance.
- Post-deploy metrics at T+24h are within baseline tolerance.
- Auth login, CSRF-protected forms, payments, webhooks, queue workers smoke-tested.
- No new error spikes in logs (exception rate, 5xx, auth failures).
- Rollback procedure validated and last known good image/tag identified.

## Residual Risks and Closure Criteria

| Risk | Owner | Deadline | Closure criteria |
| --- | --- | --- | --- |
| No verified post-deploy stability window | SRE | 2026-02-21 | 24h post-deploy metrics captured and signed off |
| Proxy header limits not validated | SRE | 2026-02-21 | Header size/dup limits confirmed in proxy config |
| Missing evidence of deploy profile checks | Backend lead | 2026-02-21 | check --deploy output attached |
| Smoke coverage for rare integrations | Backend lead | 2026-02-28 | Manual smoke steps documented and executed |

## Rollout and Rollback Notes

Rollout:
- Readiness -> staging verification -> canary -> full rollout.
- Monitor 5xx, latency (p95), CPU/memory, and worker restarts.

Rollback:
- Roll back to last known good image/tag.
- Only allow backward-compatible schema migrations during security upgrades.
- If schema changes are required, use a two-step migration with explicit rollback steps.

## Closeout Decision

Closeout status: pending
Required sign-off: backend lead + SRE

