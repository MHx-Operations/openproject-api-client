---
phase: 02-security-baseline
verified: 2026-05-13T00:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
---

# Phase 2: Security Baseline — Verification Report

**Phase Goal:** Make safe-by-default behavior reachable for callers via opt-in kwargs; eliminate the API-key leakage risk in DEBUG logs. Non-breaking is HARD.
**Verified:** 2026-05-13
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `ApiClient(..., timeout=None, verify_ssl=True)` accepted; defaults preserve current behavior | VERIFIED | `apiclient.py:35-37` — keyword-only `*` separator; `_timeout=None`, `_verify_ssl=True`. `inspect.signature` confirms KEYWORD_ONLY kind + correct defaults. 10/10 `TestApiClientSecurityKwargs` tests pass. |
| 2 | `timeout` and `verify_ssl` propagated to every `requests.*` call | VERIFIED | `apiclient.py:87-88, 102-103, 116-117, 131-132` — all four `http_*` methods pass `timeout=self._timeout, verify=self._verify_ssl`. Grep count = 4 for each kwarg. `TestSecurityKwargsPropagation` (6 tests, GET/POST/PATCH/DELETE + CA-bundle path variant) all pass. |
| 3 | API key stored on `self._apikey`; legacy `self.apikey` accessor remains for backwards compatibility | VERIFIED | `apiclient.py:47-48, 55-58, 60-61` — `self._apikey = apikey` in `__init__`; `@property apikey` returns `self._apikey` (read-only, no setter); `__repr__` returns `"***"` in place of key. `'apikey' not in vars(c)` confirmed in-process. `TestApiKeyPrivacy` (6 tests) all pass. |
| 4 | No substring of the API key appears in DEBUG log output for representative GET/POST calls | VERIFIED | All four `http_*` logger.debug calls log only endpoint URL and status_code — no apikey reference (`grep` count = 0 for logger statements referencing apikey). `TestApiKeyNotInDebugLogs` (4 tests, GET/POST/PATCH/DELETE with distinctive key `SUPERSECRETKEY-XYZ-12345`) all pass; each asserts records were captured (non-vacuous) and 4 defensive `"test-api-key" not in` assertions confirmed. |

**Score:** 4/4 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `openproject_api_client/apiclient.py` | `__init__` with timeout/verify_ssl; all 4 http_* methods forward both; `_apikey` storage; `@property apikey`; `__repr__` masking | VERIFIED | Lines 35-37 (init signature), 47-50 (storage), 55-61 (@property + __repr__), 82-135 (4 http_* methods each with both kwargs) |
| `tests/test_apiclient.py` | `TestApiClientSecurityKwargs`, `TestSecurityKwargsPropagation`, `TestApiKeyPrivacy`, `TestApiKeyNotInDebugLogs` | VERIFIED | All 4 test classes present and substantive. 111 total tests. |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `ApiClient.__init__` | `self._timeout / self._verify_ssl` | kwargs storage | WIRED | `apiclient.py:49-50` — `self._timeout = timeout`, `self._verify_ssl = verify_ssl` |
| `http_get / http_post / http_patch / http_delete` | `requests.get / post / patch / delete` | `timeout=self._timeout, verify=self._verify_ssl` | WIRED | Grep count = 4 each; lines 87-88, 102-103, 116-117, 131-132 |
| `ApiClient.__init__` | `self._apikey` | private attribute assignment | WIRED | `apiclient.py:47` — `self._apikey = apikey`; no `self.apikey = ...` assignment anywhere |
| `ApiClient.apikey` property | `self._apikey` | `@property` getter | WIRED | `apiclient.py:55-58` — `@property def apikey(self): return self._apikey` |
| caplog DEBUG records | no API-key substring | assertion over `caplog.records` at DEBUG level | WIRED | `test_apiclient.py:1258, 1276, 1294, 1311` — `caplog.at_level(logging.DEBUG, logger="openproject_api_client.apiclient")` in all 4 caplog tests |

---

## Targeted Focus Checks

| Check | Command / Observation | Result |
|-------|-----------------------|--------|
| `pytest -v -x` exit 0 | `python3 -m pytest tests/test_apiclient.py -v -x` | 111 passed, 0 failed, exit 0 |
| `ApiClient("https://x/", "k").apikey == "k"` | In-process Python assertion | PASS |
| `timeout` + `verify_ssl` are keyword-only with correct defaults | `inspect.signature` assertion | PASS — KEYWORD_ONLY, defaults `None` and `True` |
| `timeout=self._timeout` at >= 4 call sites | grep count on non-comment lines | 4 (exactly one per http_* method) |
| `verify=self._verify_ssl` at >= 4 call sites | grep count on non-comment lines | 4 (exactly one per http_* method) |
| `__repr__` does not interpolate key | `"SECRET123" not in repr(c) and "***" in repr(c)` | PASS — `ApiClient(base_url='https://x/', apikey='***')` |
| `'apikey' not in vars(c)` | In-process check; instance `__dict__` keys | PASS — keys are `_rootpath, base_url, _apikey, auth, _timeout, _verify_ssl` |
| No direct `self.apikey =` assignment in apiclient.py | grep | 0 matches (clean) |
| No logger statement references apikey in any form | grep | 0 matches |
| `'apikey' not in vars(` assertion locked in test file | grep | 1 match at `test_apiclient.py:1229` |
| Defensive `"test-api-key" not in` assertions count | grep | 4 (one per caplog test) |
| caplog tests cover GET, POST, PATCH, DELETE | Code inspection | All 4 HTTP verbs covered |
| `pyproject.toml` runtime deps unchanged | `git diff pyproject.toml` | Empty — no changes; single dep `requests>=2.25.1` |
| No TBD / FIXME / XXX markers in modified files | grep | 0 matches |

---

## Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| SEC-01 | `ApiClient.__init__` accepts optional `timeout` kwarg; default `None`; passed to every `requests.*` call | SATISFIED | `apiclient.py:36, 49, 87, 102, 116, 131` |
| SEC-02 | `ApiClient.__init__` accepts optional `verify_ssl` kwarg; default `True`; passed to every `requests.*` call | SATISFIED | `apiclient.py:37, 50, 88, 103, 117, 132` |
| SEC-03 | API key on `self._apikey`; public `self.apikey` accessor; does not appear in `repr()`/`vars()` | SATISFIED | `apiclient.py:47, 55-61`; `vars(c)` confirmed no `apikey` key |
| SEC-04 | DEBUG logging never includes `Authorization` header or API key substring; regression test asserts this | SATISFIED | Logger statements log only URLs and status codes; `TestApiKeyNotInDebugLogs` with 4 tests covers all http_* methods |

---

## Anti-Patterns Found

None. No TBD/FIXME/XXX markers in either modified file. No placeholder implementations. No empty handlers. No hardcoded empty data passed to rendering paths.

---

## Human Verification Required

None. All success criteria are fully verifiable programmatically and were verified.

---

## Gaps Summary

No gaps. All four success criteria are achieved with direct codebase evidence and a live passing test suite (111/111 tests).

---

_Verified: 2026-05-13_
_Verifier: Claude (gsd-verifier)_
