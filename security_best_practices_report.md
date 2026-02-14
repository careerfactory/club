# Security Best Practices Report (Critical + High)

Date: 2026-02-14
Scope: `/Users/egorfedorov/Documents/Programs/club`

## Executive Summary
This wave implemented critical hardening for auth/session transport, CSRF, redirect safety, webhook verification, SSRF/TLS URL fetching, and CodeQL re-enablement on maintained action versions.

Critical issues related to token leakage and missing CSRF baseline are addressed in code. High-risk backlog remains mainly in dependency patching and repository governance (required checks enforcement in branch protection), which could not be completed from this environment due missing GitHub authentication/permissions.

## Automated Scan Results
1. CodeQL workflow reintroduced with `github/codeql-action@v4` and proper permissions.
2. Python dependency scan (`python -m pip_audit`) found 58 known vulnerabilities across 18 packages.
3. JavaScript dependency scan (`npm audit --omit=dev`) found 3 low vulnerabilities (Vue ecosystem).
4. Secret scan tool `gitleaks` is not installed in this environment; fallback regex scan found only test stub private key and an explicit dev fallback secret constant.

## Critical Findings

### C-001 Missing CSRF middleware and baseline protection (Fixed)
- Severity: Critical
- Impact: State-changing browser requests could be forged when authenticated by cookie.
- Exploitability: High (standard CSRF attack path).
- Evidence:
  - `/Users/egorfedorov/Documents/Programs/club/club/settings.py:79`
  - `/Users/egorfedorov/Documents/Programs/club/club/settings.py:82`
  - `/Users/egorfedorov/Documents/Programs/club/authn/decorators/api.py:47`
  - `/Users/egorfedorov/Documents/Programs/club/frontend/static/js/common/api.service.js:15`
- Remediation implemented:
  - Added `CsrfViewMiddleware`.
  - Added explicit CSRF enforcement for cookie-authenticated API unsafe methods.
  - Added frontend `X-CSRFToken` propagation for AJAX calls.

### C-002 Session token accepted via query string (Fixed)
- Severity: Critical
- Impact: Token leakage through logs, referers, and browser history.
- Exploitability: High.
- Evidence:
  - `/Users/egorfedorov/Documents/Programs/club/authn/helpers.py:25`
  - `/Users/egorfedorov/Documents/Programs/club/authn/helpers.py:27`
- Remediation implemented:
  - Cookie-only token transport in `authorized_user_with_session`.
  - Added regression tests:
    - `/Users/egorfedorov/Documents/Programs/club/authn/tests.py:136`
    - `/Users/egorfedorov/Documents/Programs/club/authn/tests.py:145`

### C-003 API `service_token` accepted in GET query (Fixed)
- Severity: Critical
- Impact: Credential leakage in URLs and logs.
- Exploitability: High.
- Evidence:
  - `/Users/egorfedorov/Documents/Programs/club/authn/decorators/api.py:25`
  - `/Users/egorfedorov/Documents/Programs/club/frontend/html/openid/list_apps.html:141`
- Remediation implemented:
  - Header-only `X-Service-Token` support.
  - Removed/updated insecure docs example.
  - Added tests:
    - `/Users/egorfedorov/Documents/Programs/club/authn/test_api_security.py:27`
    - `/Users/egorfedorov/Documents/Programs/club/authn/test_api_security.py:36`

### C-004 Open redirect via `goto` parameter (Fixed)
- Severity: Critical
- Impact: Phishing and token/session abuse via attacker-controlled redirect destinations.
- Exploitability: High.
- Evidence:
  - `/Users/egorfedorov/Documents/Programs/club/authn/views/email.py:22`
  - `/Users/egorfedorov/Documents/Programs/club/authn/views/email.py:119`
  - `/Users/egorfedorov/Documents/Programs/club/users/views/profile.py:35`
- Remediation implemented:
  - Added `url_has_allowed_host_and_scheme` validation.
  - Added redirect tests:
    - `/Users/egorfedorov/Documents/Programs/club/authn/views/tests.py:256`
    - `/Users/egorfedorov/Documents/Programs/club/authn/views/tests.py:270`

### C-005 Webhook secret in query + non-constant signature comparison (Fixed)
- Severity: Critical
- Impact: Secret exposure and potential timing side-channel on signature comparison.
- Exploitability: High.
- Evidence:
  - `/Users/egorfedorov/Documents/Programs/club/notifications/webhooks.py:11`
  - `/Users/egorfedorov/Documents/Programs/club/notifications/webhooks.py:43`
  - `/Users/egorfedorov/Documents/Programs/club/payments/cloudpayments.py:166`
- Remediation implemented:
  - `notifications/webhook` now accepts header `X-Webhook-Secret` only.
  - Constant-time comparison (`hmac.compare_digest`) for webhook checks.
  - Added webhook tests:
    - `/Users/egorfedorov/Documents/Programs/club/notifications/tests.py:10`
    - `/Users/egorfedorov/Documents/Programs/club/notifications/tests.py:20`

### C-006 Insecure URL fetcher (`verify=False`, internal network fetch risk) (Fixed)
- Severity: Critical
- Impact: SSRF to internal services and MITM risk due TLS verification bypass.
- Exploitability: High.
- Evidence:
  - `/Users/egorfedorov/Documents/Programs/club/common/url_metadata_parser.py:58`
  - `/Users/egorfedorov/Documents/Programs/club/common/url_metadata_parser.py:63`
  - `/Users/egorfedorov/Documents/Programs/club/common/url_metadata_parser.py:118`
- Remediation implemented:
  - Removed insecure TLS behavior.
  - Added URL scheme/host/IP safety checks.
  - Blocked localhost/private/link-local/reserved/multicast/unspecified addresses.
  - Added safe redirect resolution via `urljoin`.

### C-007 Insecure production defaults (`DEBUG`, `SECRET_KEY`, `ALLOWED_HOSTS`) (Fixed)
- Severity: Critical
- Impact: Misconfiguration can expose debug pages, weak secrets, or host-header abuse.
- Exploitability: High.
- Evidence:
  - `/Users/egorfedorov/Documents/Programs/club/club/settings.py:28`
  - `/Users/egorfedorov/Documents/Programs/club/club/settings.py:32`
  - `/Users/egorfedorov/Documents/Programs/club/club/settings.py:39`
- Remediation implemented:
  - Explicit environment-driven defaults.
  - Runtime guard when `SECRET_KEY` is missing and debug is disabled.
  - Explicit cookie/security settings and `.env.example` updates:
    - `/Users/egorfedorov/Documents/Programs/club/club/.env.example:1`

## High Findings

### H-001 Dependency vulnerability backlog is large (Open)
- Severity: High
- Impact: Known vulnerable transitive and direct dependencies increase exploit surface.
- Exploitability: Medium to High (depends on reachable code paths).
- Evidence:
  - `pip-audit` output: 58 vulnerabilities, including `django==3.2.13`, `authlib==1.2.0`, `requests==2.31.0`, `urllib3==2.0.5`, `gunicorn==20.0.4`.
- Recommended remediation:
  - Priority 1: Django LTS track upgrade and coordinated framework dependency bump.
  - Priority 2: authlib, requests/urllib3, gunicorn upgrades with compatibility tests.
  - Priority 3: staged rollout with canary and rollback plan.

### H-002 Branch protection / required CodeQL checks not configured from current environment (Open)
- Severity: High
- Impact: PR blocking policy can be bypassed if required checks are not enforced at repository policy level.
- Exploitability: Organizational/process risk.
- Evidence:
  - `gh auth status` reports no authenticated host; branch protection API update not possible.
  - CodeQL workflow is present:
    - `/Users/egorfedorov/Documents/Programs/club/.github/workflows/codeql.yml:1`
- Recommended remediation:
  - Configure required checks for branch `club`:
    - `Analyze (python)`
    - `Analyze (javascript)`

### H-003 Legacy runtime stack in CI (Open)
- Severity: High
- Impact: old runtime baselines reduce security patch cadence and raise compatibility/security debt.
- Exploitability: Indirect.
- Evidence:
  - Python app baseline: Django 3.2.x and old ecosystem versions (see H-001).
  - CI test workflow still uses old Node runtime in existing file:
    - `/Users/egorfedorov/Documents/Programs/club/.github/workflows/tests.yml:71`
- Recommended remediation:
  - Define and execute dependency/runtime upgrade roadmap with compatibility matrix and phased rollouts.

## Implemented Artifacts
- Added: `/Users/egorfedorov/Documents/Programs/club/.github/workflows/codeql.yml`
- Added: `/Users/egorfedorov/Documents/Programs/club/.github/codeql/codeql-config.yml`
- Updated security baseline/config/auth/webhook/parser/test files in this repository.

## Validation Notes
- Static validation completed:
  - Python syntax compile for changed files.
  - YAML parse for new CodeQL workflow/config.
- Full Django test run could not be executed in this environment because Django is not installed (`ModuleNotFoundError: No module named 'django'`).

## Next Actions
1. Authenticate GitHub CLI and enforce required checks in branch protection.
2. Run full test suite in project venv/CI.
3. Execute dependency upgrade plan starting from Django/authlib/requests/urllib3/gunicorn.
