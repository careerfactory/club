# Django Security Release Audit (2026-02-03)

Date: 2026-02-14
Scope: `/Users/egorfedorov/Documents/Programs/club`
Source advisory: `https://www.djangoproject.com/weblog/2026/feb/03/security-releases/`

## Executive Summary

The Django security advisory published on **February 3, 2026** announces fixes in `6.0.2`, `5.2.11`, and `4.2.28` for 6 CVEs.

This project is pinned to **Django 3.2.13**, which is an unsupported release series and does not receive security fixes. The project also runs Django through ASGI in production, so the ASGI duplicate-header DoS issue is relevant.

## Findings

### DSR-001
- Severity: High
- Rule ID: DJANGO-SUPPLY-001
- Title: Unsupported Django branch (3.2.x) blocks security patch intake
- Location:
  - `Pipfile:12`
  - `Pipfile.lock:311`
  - `Pipfile:43`
- Evidence:
  - `django = "==3.2.13"` is pinned in both manifest and lock file.
  - Python runtime is pinned to `3.8`.
  - Official Django download/support table marks `3.2 LTS` as unsupported (extended support ended April 1, 2024).
- Impact:
  - The project cannot consume Django security patches from supported branches without upgrading framework/runtime.
- Fix:
  - Immediate: upgrade to `Django 4.2.28` (latest supported branch compatible with Python 3.8).
  - Planned: upgrade runtime to Python 3.10+ and move to `Django 5.2.11` LTS.
- Mitigation:
  - Tighten edge protections (WAF/rate limiting/reverse-proxy request limits) while framework upgrade is in progress.
- False positive notes:
  - None. This is directly confirmed by dependency pins and Django support matrix.

### DSR-002
- Severity: High
- Rule ID: DJANGO-SUPPLY-001
- Title: CVE-2025-14550 (ASGI repeated headers DoS) is relevant to current deployment mode
- Location:
  - `Makefile:38`
  - `Makefile:27`
  - `club/asgi.py:12`
  - `docker-compose.production.yml:5`
- Evidence:
  - Production command runs `gunicorn club.asgi:application -k uvicorn.workers.UvicornWorker`.
  - ASGI application is active (`get_asgi_application`).
  - Advisory explicitly describes DoS in `ASGIRequest` with repeated duplicate headers.
- Impact:
  - Attacker can trigger super-linear processing via crafted duplicate headers, causing service degradation/outage.
- Fix:
  - Upgrade Django to patched branch release (`4.2.28+`, `5.2.11+`, or `6.0.2+`).
- Mitigation:
  - Enforce duplicate header/request size limits at reverse proxy and rate limiting per IP.
- False positive notes:
  - If deployment is switched to WSGI-only without ASGI request path, exploitability drops. Current repo configuration indicates ASGI is used.

## CVE-by-CVE applicability for this codebase

- CVE-2025-13473 (mod_wsgi timing enumeration): **Not observed in repo usage**.
  - `mod_wsgi` references: no matches in code/config searched.
- CVE-2025-14550 (ASGI repeated headers DoS): **Relevant** (see DSR-002).
- CVE-2026-1207 (PostGIS raster lookup SQLi): **No direct usage observed**.
  - `django.contrib.gis` / PostGIS / raster usage: no matches.
  - DB engine configured as `django.db.backends.postgresql_psycopg2`.
- CVE-2026-1285 (Truncator HTML methods DoS): **No direct usage observed**.
  - `Truncator(..., html=True)`, `truncatechars_html`, `truncatewords_html`: no matches.
- CVE-2026-1287 (FilteredRelation alias SQLi): **No direct usage observed**.
  - `FilteredRelation`: no matches.
- CVE-2026-1312 (order_by + FilteredRelation alias SQLi): **No direct usage observed**.
  - `FilteredRelation`: no matches.

## Remediation Priority

1. Upgrade Django from `3.2.13` to `4.2.28` immediately.
2. Add proxy-level hard limits for header duplication/size until upgrade is deployed.
3. Plan Python runtime uplift to `3.10+` and migrate to `5.2.11` LTS.

