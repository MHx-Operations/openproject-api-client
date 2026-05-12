---
phase: 02-security-baseline
plan: "01"
subsystem: apiclient
tags: [security, timeout, ssl, non-breaking]
dependency_graph:
  requires: []
  provides: [timeout-kwarg, verify-ssl-kwarg]
  affects: [openproject_api_client/apiclient.py, tests/test_apiclient.py]
tech_stack:
  added: []
  patterns: [keyword-only-after-positional, private-attrs]
key_files:
  modified:
    - openproject_api_client/apiclient.py
    - tests/test_apiclient.py
decisions:
  - "Used `*` separator in __init__ to enforce keyword-only timeout/verify_ssl without breaking positional ApiClient(base_url, apikey)"
  - "Stored as self._timeout / self._verify_ssl (leading underscore = module-private per CONVENTIONS.md)"
  - "verify kwarg to requests uses `verify=` not `verify_ssl=` to match the requests library's own parameter name"
  - "Propagation tests use unittest.mock.patch on requests.get/post/patch/delete (not responses library) to inspect exact kwargs"
metrics:
  duration: "~2 minutes"
  completed: "2026-05-12"
  tasks_completed: 2
  files_modified: 2
---

# Phase 02 Plan 01: Timeout and SSL Verify kwargs for ApiClient Summary

Added keyword-only `timeout` and `verify_ssl` to `ApiClient.__init__` with safe defaults (`None`/`True`), forwarded to all four `requests.*` call sites via `self._timeout` / `self._verify_ssl`.

## Tasks Completed

| Task | Name | Commit |
|------|------|--------|
| 1 (RED) | Failing tests: TestApiClientSecurityKwargs | 87fc81d |
| 1 (GREEN) | Extend __init__ with keyword-only timeout/verify_ssl | ced1256 |
| 2 (RED) | Failing tests: TestSecurityKwargsPropagation | abdf1b0 |
| 2 (GREEN) | Forward timeout/verify to all four http_* methods | bc70d5b |

## Key Changes

### `openproject_api_client/apiclient.py`

- **Line 35**: `__init__` signature extended with `*, timeout: float | None = None, verify_ssl: bool | str = True`
- **Lines 49-50**: `self._timeout = timeout` and `self._verify_ssl = verify_ssl` stored after existing attrs
- **Lines 73-74**: `requests.get` receives `timeout=self._timeout, verify=self._verify_ssl`
- **Lines 88-89**: `requests.post` receives `timeout=self._timeout, verify=self._verify_ssl`
- **Lines 101-102**: `requests.patch` receives `timeout=self._timeout, verify=self._verify_ssl`
- **Lines 113-114**: `requests.delete` receives `timeout=self._timeout, verify=self._verify_ssl`

### `tests/test_apiclient.py`

- Added `TestApiClientSecurityKwargs` (10 tests): defaults, custom timeout, custom verify_ssl bool/path, keyword-only TypeError enforcement, inspect.signature assertions
- Added `TestSecurityKwargsPropagation` (6 tests): default None/True, custom 15/False, POST/PATCH/DELETE propagation, CA-bundle path

## Acceptance Verification

```
# grep gate — both return 4
grep -v '^[[:space:]]*#' openproject_api_client/apiclient.py | grep -c 'timeout=self._timeout'  # 4
grep -v '^[[:space:]]*#' openproject_api_client/apiclient.py | grep -c 'verify=self._verify_ssl'  # 4

# signature assertion
python3 -c "import inspect; from openproject_api_client.apiclient import ApiClient; \
  p=inspect.signature(ApiClient.__init__).parameters; \
  assert p['timeout'].kind.name=='KEYWORD_ONLY' and p['verify_ssl'].kind.name=='KEYWORD_ONLY' \
  and p['timeout'].default is None and p['verify_ssl'].default is True"  # exits 0

# full suite
pytest -v -x  # 276 passed
```

## Test Output Excerpt

```
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_default_timeout_is_none PASSED
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_default_verify_ssl_is_true PASSED
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_positional_construction_unchanged PASSED
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_custom_timeout PASSED
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_custom_verify_ssl_false PASSED
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_custom_verify_ssl_ca_bundle_path PASSED
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_timeout_is_keyword_only PASSED
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_verify_ssl_is_keyword_only PASSED
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_signature_timeout_keyword_only PASSED
tests/test_apiclient.py::TestApiClientSecurityKwargs::test_signature_verify_ssl_keyword_only PASSED
tests/test_apiclient.py::TestSecurityKwargsPropagation::test_http_get_default_propagates_none_and_true PASSED
tests/test_apiclient.py::TestSecurityKwargsPropagation::test_http_get_custom_propagates PASSED
tests/test_apiclient.py::TestSecurityKwargsPropagation::test_http_post_propagates PASSED
tests/test_apiclient.py::TestSecurityKwargsPropagation::test_http_patch_propagates PASSED
tests/test_apiclient.py::TestSecurityKwargsPropagation::test_http_delete_propagates PASSED
tests/test_apiclient.py::TestSecurityKwargsPropagation::test_ca_bundle_path_propagates PASSED
276 passed in 0.30s
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints or auth paths introduced; `verify_ssl` defaults to `True` (safe default).

## TDD Gate Compliance

- RED gate commit (test): 87fc81d, abdf1b0
- GREEN gate commit (feat): ced1256, bc70d5b
- No REFACTOR needed.

## Self-Check: PASSED

- `openproject_api_client/apiclient.py` exists and contains `self._timeout` at line 49
- `tests/test_apiclient.py` exists and contains `TestApiClientSecurityKwargs` and `TestSecurityKwargsPropagation`
- All four task commits confirmed in git log: 87fc81d, ced1256, abdf1b0, bc70d5b
- `pytest -v -x` exits 0 (276 passed)
