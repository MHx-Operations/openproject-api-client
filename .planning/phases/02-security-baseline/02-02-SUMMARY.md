---
phase: 02-security-baseline
plan: "02"
subsystem: apiclient
tags: [security, api-key-privacy, repr-masking, debug-log-safety, non-breaking]
dependency_graph:
  requires: [02-01]
  provides: [private-apikey-storage, apikey-property, repr-masking, debug-log-regression-tests]
  affects: [openproject_api_client/apiclient.py, tests/test_apiclient.py]
tech_stack:
  added: []
  patterns: [leading-underscore-private, property-accessor, masking-repr]
key_files:
  modified:
    - openproject_api_client/apiclient.py
    - tests/test_apiclient.py
decisions:
  - "self._apikey used for private storage; @property apikey returns it read-only (no setter) — backwards-compat enforced"
  - "__repr__ uses literal '***' string, never interpolates self._apikey; f-string with literal placeholder"
  - "TestApiKeyNotInDebugLogs uses distinctive SECRET_KEY='SUPERSECRETKEY-XYZ-12345' to make any leak unambiguous"
  - "Task 2 TDD: tests pass immediately because existing DEBUG calls never logged the key; tests lock that invariant"
metrics:
  duration: "~2 minutes"
  completed: "2026-05-13"
  tasks_completed: 2
  files_modified: 2
---

# Phase 02 Plan 02: API Key Privacy — _apikey, @property, __repr__, DEBUG log regression Summary

Private API key storage via `self._apikey` with read-only `@property` backwards-compatible accessor, masking `__repr__`, and regression-test lock that DEBUG logs never leak any substring of the API key across GET / POST / PATCH / DELETE.

## Tasks Completed

| Task | Name | Commit |
|------|------|--------|
| 1 (RED) | Failing tests: TestApiKeyPrivacy | e08b05d |
| 1 (GREEN) | Rename to _apikey, add @property, add __repr__ | 61a41fe |
| 2 (RED+GREEN) | TestApiKeyNotInDebugLogs — regression lock for SEC-04 | e31ff5c |

## Key Changes

### `openproject_api_client/apiclient.py`

- **Line 47**: `self._apikey = apikey` replaces `self.apikey = apikey` in `__init__`
- **Line 48**: `HTTPBasicAuth('apikey', self._apikey)` — no functional change
- **Lines 54-58**: `@property def apikey(self): return self._apikey` — read-only, no setter
- **Lines 60-61**: `def __repr__(self): return f"ApiClient(base_url={self.base_url!r}, apikey='***')"` — literal `'***'` placeholder

### `tests/test_apiclient.py`

- Added `TestApiKeyPrivacy` (6 tests) after `TestSecurityKwargsPropagation`:
  - `test_private_storage`, `test_backwards_compat_property`, `test_property_is_readonly`
  - `test_apikey_not_in_instance_dict` — asserts `'apikey' not in vars(c)`
  - `test_repr_masks_apikey`, `test_auth_object_still_carries_key`
- Added `TestApiKeyNotInDebugLogs` (4 tests) after `TestApiKeyPrivacy`:
  - `SECRET_KEY = "SUPERSECRETKEY-XYZ-12345"` class constant
  - `test_no_key_in_get_debug`, `test_no_key_in_post_debug`, `test_no_key_in_patch_debug`, `test_no_key_in_delete_debug`
  - Each: asserts ≥1 DEBUG record, SECRET_KEY absent from getMessage() and str(args), "test-api-key" absent (belt-and-suspenders)

## Acceptance Verification

```bash
# _apikey in assignment and property body
grep -n "self._apikey" openproject_api_client/apiclient.py
# 47:        self._apikey = apikey
# 48:        self.auth = HTTPBasicAuth('apikey', self._apikey)
# 58:        return self._apikey

# no direct self.apikey= assignment (count = 0)
grep -c "self\.apikey\s*=" openproject_api_client/apiclient.py   # 0

# repr masking
python3 -c "
from openproject_api_client.apiclient import ApiClient
c = ApiClient('https://x/', 'SECRETKEY')
assert 'SECRETKEY' not in repr(c) and '***' in repr(c)
"  # exits 0

# structural assertion locked in tests
grep -F "'apikey' not in vars(" tests/test_apiclient.py  # 1 match

# no logger referencing apikey attribute
grep -n "self._apikey\|self.apikey\|apikey" openproject_api_client/apiclient.py | grep -i "logger\." | wc -l  # 0

# defensive belt-and-suspenders count (min 4)
grep -c '"test-api-key" not in' tests/test_apiclient.py  # 4

# full suite
pytest -v -x  # 286 passed
```

## Test Output Excerpt

```
tests/test_apiclient.py::TestApiKeyPrivacy::test_private_storage PASSED
tests/test_apiclient.py::TestApiKeyPrivacy::test_backwards_compat_property PASSED
tests/test_apiclient.py::TestApiKeyPrivacy::test_property_is_readonly PASSED
tests/test_apiclient.py::TestApiKeyPrivacy::test_apikey_not_in_instance_dict PASSED
tests/test_apiclient.py::TestApiKeyPrivacy::test_repr_masks_apikey PASSED
tests/test_apiclient.py::TestApiKeyPrivacy::test_auth_object_still_carries_key PASSED
tests/test_apiclient.py::TestApiClientInit::test_valid_construction PASSED
tests/test_apiclient.py::TestApiClientInit::test_trailing_slash_added PASSED
tests/test_apiclient.py::TestApiClientInit::test_missing_base_url_raises PASSED
tests/test_apiclient.py::TestApiClientInit::test_missing_apikey_raises PASSED
tests/test_apiclient.py::TestApiKeyNotInDebugLogs::test_no_key_in_get_debug PASSED
tests/test_apiclient.py::TestApiKeyNotInDebugLogs::test_no_key_in_post_debug PASSED
tests/test_apiclient.py::TestApiKeyNotInDebugLogs::test_no_key_in_patch_debug PASSED
tests/test_apiclient.py::TestApiKeyNotInDebugLogs::test_no_key_in_delete_debug PASSED
286 passed in 0.29s
```

## Deviations from Plan

### Notes

**Task 2 TDD RED phase:** The plan explicitly anticipated that DEBUG calls would not log the API key ("The current DEBUG calls in the codebase do not log the key, so the tests should pass without code changes"). The four `TestApiKeyNotInDebugLogs` tests passed immediately after being written (no GREEN implementation step needed). This is by design — the tests serve as a regression lock rather than to fix a pre-existing bug. Single commit covers both RED and GREEN for Task 2.

None — plan executed exactly as written; no code changes were required in Task 2.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints introduced. The change reduces exposure by preventing `self.apikey` from appearing in the instance `__dict__`, which mitigates accidental key discovery via `vars(client)` or `client.__dict__` inspection.

## TDD Gate Compliance

- Task 1 RED gate commit (test): e08b05d
- Task 1 GREEN gate commit (feat): 61a41fe
- Task 2: tests pass on first run (implementation already correct per plan expectation); RED+GREEN in single commit e31ff5c
- No REFACTOR needed.

## Self-Check: PASSED

- `openproject_api_client/apiclient.py` contains `self._apikey` at lines 47, 48, 58 and `@property` at line 54
- `tests/test_apiclient.py` contains `TestApiKeyPrivacy` and `TestApiKeyNotInDebugLogs`
- All task commits confirmed in git log: e08b05d, 61a41fe, e31ff5c
- `pytest -v -x` exits 0 (286 passed)
