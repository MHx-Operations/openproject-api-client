---
phase: 03-performance-baseline
plan: "01"
subsystem: apiclient
tags: [performance, session, http, requests]
dependency_graph:
  requires: [02-01, 02-02]
  provides: [session-reuse]
  affects: [openproject_api_client/apiclient.py, tests/test_apiclient.py]
tech_stack:
  added: []
  patterns: [requests.Session lifecycle management, session-level auth/verify, per-call timeout]
key_files:
  created: []
  modified:
    - openproject_api_client/apiclient.py
    - tests/test_apiclient.py
decisions:
  - "Session constructed eagerly in __init__ (not lazily) for predictable test isolation and lifecycle"
  - "Per-call timeout=self._timeout retained on every self._session.* call (requests psf#3070: Session has no default timeout)"
  - "self.auth attribute retained on ApiClient instance for backwards compatibility even though auth is now on the session"
  - "verify= dropped from per-call kwargs; session.verify set once at construction from verify_ssl arg"
  - "auth= dropped from per-call kwargs; session.auth = HTTPBasicAuth set once at construction"
  - "TestSecurityKwargsPropagation migrated to patch requests.Session.get/post/patch/delete; verify assertions moved from call_args.kwargs to client._session.verify"
metrics:
  duration: "103s"
  completed: "2026-05-13"
  tasks_completed: 4
  files_changed: 2
---

# Phase 03 Plan 01: PERF-01 — requests.Session Reuse Summary

Single requests.Session constructed once per ApiClient instance, eliminating per-request TCP/TLS reconnects by routing all four http_* methods through self._session with auth and verify configured at construction time.

## Tasks Completed

| Task | Name | Commit |
|------|------|--------|
| 1 | Introduce self._session and route all http_* methods through it | 15808b4 |
| 2 | Regression test for Session reuse across sequential calls | 2aad1cd |
| 2.5 | Migrate TestSecurityKwargsPropagation to Session-level patches | 2aad1cd |
| 3 | Full regression sweep | (no files — 287 tests pass) |

## Changes Made

### openproject_api_client/apiclient.py

`__init__` now includes (after existing assignments):
```python
self._session = requests.Session()
self._session.auth = HTTPBasicAuth('apikey', self._apikey)
self._session.verify = self._verify_ssl
```

Each http_* method replaced `requests.<verb>(...)` with `self._session.<verb>(...)`, removing `auth=self.auth` and `verify=self._verify_ssl` from the per-call kwargs. `timeout=self._timeout` is retained on every call.

### tests/test_apiclient.py

- Added `import requests` at module level.
- Added `TestSessionReuse.test_session_is_reused_across_calls`: constructs a client, makes two http_get calls via `responses` mocking, asserts `isinstance(client._session, requests.Session)`, identity stability via `id(client._session)`, and `len(responses.calls) == 2`.
- Migrated `TestSecurityKwargsPropagation`: all six tests now patch `requests.Session.get/post/patch/delete` instead of `openproject_api_client.apiclient.requests.get/...`; verify assertions moved from `kwargs["verify"]` to `client._session.verify`.

## Key Decisions

**Session-vs-per-request timeout:** Per `psf/requests#3070`, the `requests.Session` object does not apply a default timeout to requests made through it. Per-call `timeout=self._timeout` is therefore retained on every `self._session.*` call. Removing it would silently allow requests to hang indefinitely regardless of the configured timeout value.

**self.auth retained for backwards compatibility:** Phase 2 established `self.auth = HTTPBasicAuth('apikey', self._apikey)` as a public-ish instance attribute. Although auth is now configured on the session, `self.auth` is kept in place unchanged so any external code reading `client.auth` continues to work.

**Eager session construction:** The session is created unconditionally in `__init__` rather than lazily on first use, which keeps test isolation straightforward (no lazy-init side effects) and makes the attribute accessible immediately after construction.

## Deviations from Plan

None — plan executed exactly as written.

## Verification

- `self._session = requests.Session()` appears exactly once in apiclient.py, inside `__init__`.
- `self._session.auth` and `self._session.verify` assigned once in `__init__`.
- Zero occurrences of `requests.get(`, `requests.post(`, `requests.patch(`, `requests.delete(` inside http_* method bodies.
- All four http_* methods retain `timeout=self._timeout` per call.
- Session-reuse regression test passes.
- `TestSecurityKwargsPropagation` (migrated to Session-level patches) passes.
- Full `pytest -v -x` exits 0: **287 passed**.

## Self-Check: PASSED

- `openproject_api_client/apiclient.py` — FOUND, contains `self._session = requests.Session()`
- `tests/test_apiclient.py` — FOUND, contains `TestSessionReuse` and migrated `TestSecurityKwargsPropagation`
- Commits 15808b4 and 2aad1cd — FOUND in git log
