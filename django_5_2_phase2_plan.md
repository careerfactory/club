# Phase 2 Plan: Python 3.10+ and Django 5.2 LTS

Date: 2026-02-14
Scope: /Users/egorfedorov/Documents/Programs/club
Target: Python 3.10+ runtime and Django 5.2.x LTS

## Goal

Move the project from Python 3.8 / Django 4.2.28 to Python 3.10+ and Django 5.2 LTS without regressions.

## Scope

In scope:
- Runtime uplift to Python 3.10+.
- Dependency audit and upgrades for Python/Django compatibility.
- Framework uplift to Django 5.2.x LTS.
- Verification, rollout readiness, and rollback procedures.

Out of scope:
- Business logic changes unrelated to compatibility.
- Feature work not required for the uplift.

## Stages and Gates

1. Runtime uplift (Python 3.10+)
- Entry: baseline tests green on current branch.
- Work: update Docker image, CI, and runtime tooling to Python 3.10+.
- Exit: app boots, migrations run, and tests pass on Python 3.10+ with Django 4.2.28.

2. Dependency uplift
- Entry: runtime uplift complete.
- Work: audit dependencies for Python 3.10+ and Django 5.2 support, upgrade or replace.
- Exit: dependency matrix signed off, CI green on Python 3.10+ with Django 4.2.28.

3. Framework uplift (Django 5.2)
- Entry: dependency uplift complete.
- Work: upgrade Django to 5.2.x LTS and resolve compatibility issues.
- Exit: CI green, smoke tests pass, no critical regressions.

4. Verification and rollout readiness
- Entry: framework uplift complete.
- Work: staging dry-run, canary plan, rollback runbook validated.
- Exit: approval from backend lead + SRE for production rollout.

## Release Governance

Approvals:
- Backend lead: app compatibility and test sign-off.
- SRE: rollout plan, monitoring, and rollback readiness.

Rollout windows:
- Default: weekday, low-traffic window with on-call coverage.
- Canary: 1-5% traffic for at least 2 hours before full rollout.

Rollback criteria:
- 5xx error rate > baseline + 2x for 10 minutes.
- p95 latency > baseline + 50% for 15 minutes.
- Any payment or auth regression confirmed by smoke checks.

## Execution Backlog

| Task | Owner | Estimate | Depends on | Definition of Done |
| --- | --- | --- | --- | --- |
| Update Docker base image to Python 3.10+ | Infra | 1d | None | Image builds and pushes in CI |
| Update CI matrix for Python 3.10+ | Infra | 0.5d | None | CI green on Python 3.10+ |
| Audit dependencies for Python 3.10+ | Backend | 1d | None | Compatibility matrix documented |
| Upgrade blocking dependencies | Backend | 2d | Dependency audit | CI green on Python 3.10+ |
| Upgrade Django to 5.2.x LTS | Backend | 1d | Dependency uplift | Tests and smoke checks green |
| Update settings for Django 5.2 changes | Backend | 1d | Django upgrade | No deprecation errors |
| Staging dry-run with prod-like config | SRE | 1d | Framework uplift | Staging sign-off |
| Canary rollout and monitoring plan | SRE | 0.5d | Staging dry-run | Runbook and alerts ready |
| Rollback runbook update | SRE | 0.5d | None | Rollback steps validated |

## Risks and Mitigations

- Dependency incompatibility with Python 3.10+/Django 5.2: mitigate via early audit and upgrades.
- CI toolchain drift: mitigate via explicit toolchain uplift before framework upgrade.
- Migration rollback complexity: enforce backward-compatible migrations only.
- Env parity drift across dev/staging/prod: run env parity checklist before staging dry-run.

## Timeline (Proposed)

- Week 1 (2026-02-17 to 2026-02-21): runtime and dependency uplift.
- Week 2 (2026-02-24 to 2026-02-28): Django 5.2 upgrade, staging dry-run, rollout prep.

## Acceptance Criteria

- Python 3.10+ runtime is in production.
- Django 5.2.x LTS is deployed with stable monitoring signals for 24 hours.
- Rollback runbook is validated and stored with release artifacts.
- All Phase 2 risks have owners and closure criteria.

