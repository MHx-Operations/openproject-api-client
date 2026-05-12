---
phase: 01-latent-bug-fixes
plan: "03"
subsystem: resources, apiclient
tags: [bug-fix, query, pagination, status-filter, debug-leak]
dependency_graph:
  requires: []
  provides: [BUG-03-fix, BUG-04-fix, BUG-05-fix]
  affects: [openproject_api_client.resources.Query, openproject_api_client.apiclient.ApiClient]
tech_stack:
  added: []
  patterns: [effective_pagesize-fallback, else-logger.debug-clause]
key_files:
  created: []
  modified:
    - openproject_api_client/resources.py
    - openproject_api_client/apiclient.py
    - tests/test_resources.py
    - tests/test_apiclient.py
    - docs/Status.md
decisions:
  - "BUG-03: drop debug=True entirely (not replace with debug=False) — False is GenericType default"
  - "BUG-04: unknown status is silent no-op + DEBUG log; not ValueError — matches pre-existing behavior"
  - "BUG-05: do NOT widen get_workpackages_by_query_id signature with page_size param (PERF item, deferred)"
metrics:
  duration: "< 5 minutes"
  completed: "2026-05-12"
  tasks_completed: 2
  files_changed: 5
---

# Phase 01 Plan 03: BUG-03, BUG-04, BUG-05 Summary

Eliminated the final three latent bugs in Phase 1: removed `Query`'s debug-mode JSON leak, locked and documented unknown-status passthrough behavior, and mirrored `get_paged_collection`'s `effective_pagesize`/`effective_offset` fallback in `get_workpackages_by_query_id`.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Remove Query debug=True (BUG-03) | 0451107 | resources.py, test_resources.py, docs/Status.md |
| 2 | Lock unknown-status + fix query-id pagination (BUG-04, BUG-05) | 67fd55e | apiclient.py, test_apiclient.py |

## What Was Done

### BUG-03 — Query.json debug leak

**resources.py line 608 (before → after):**
```
- super().__init__(json_object, debug=True, datetime_fields=['createdat', 'updatedat'])
+ super().__init__(json_object, datetime_fields=['createdat', 'updatedat'])
```

`debug=True` caused `GenericType.__init__` to attach `self.json = json_object` (the full raw API blob) and to set every `_links`/`_embedded` key as a lowercased attribute on the `Query` namespace. Removing `debug=True` (rather than replacing with `debug=False`, which is the `GenericType` default and would be redundant) eliminates both side effects.

5 new tests added to `TestQuery` in `tests/test_resources.py`:
- `test_query_has_no_json_attr_by_default` — asserts `hasattr(q, "json")` is False
- `test_query_no_links_keys_on_namespace` — asserts `_links` and `links` absent
- `test_query_no_embedded_keys_on_namespace` — asserts `_embedded` and `embedded` absent
- `test_query_public_attrs_preserved` — regression for public attribute contract
- `test_query_results_decoding_preserved` — regression for `_embedded.results` decoding

**Release note in `docs/Status.md`:** v0.3 section documents `Query.json` removal as an intentional cleanup and guides callers to `ApiClient.get()` / `ApiClient.http_get()` as alternatives.

### BUG-04 — Unknown status string documented and logged

**Locked behavior:** unknown status values are a silent no-op (no filter applied); one `DEBUG` log entry is emitted containing the unrecognised string.

`get_workpackages` (apiclient.py line 288) and `get_workpackages_by_project_id` (line 322) both received the same `else` clause:
```python
else:
    logger.debug("Unknown status filter: %s (no filter applied)", status)
```

The `get_workpackages` docstring was updated to state: "Unknown values are ignored (no filter applied) and a debug log entry is emitted. If both `status` and `status_ids` are provided, `status` takes precedence."

4 new tests in `TestGetWorkpackagesUnknownStatus` (`tests/test_apiclient.py`):
- `test_get_workpackages_unknown_status_no_filter` — verifies `filters=` absent from URL
- `test_get_workpackages_unknown_status_logs_debug` — uses `caplog` at DEBUG on `openproject_api_client.apiclient`; asserts status value appears in a DEBUG record
- `test_get_workpackages_open_status_regression` — known status still produces correct filter
- `test_get_workpackages_uppercase_status_regression` — `.lower()` still maps `OPEN` → `o` filter

### BUG-05 — get_workpackages_by_query_id None pagesize/offset crash

The original termination condition `collection.total < collection.offset * collection.pagesize` raises `TypeError` when the API omits `pageSize` or `offset` from the `WorkPackageCollection` envelope (both are `None`).

**Lines rewritten in `get_workpackages_by_query_id` (apiclient.py ~335–360):**
Added the same `effective_pagesize` / `effective_offset` fallback that `get_paged_collection` uses (lines 180–188), falling back to the local loop variable when the collection field is `None`:

```python
effective_pagesize = page_size
if collection.pagesize is not None:
    effective_pagesize = collection.pagesize

effective_offset = offset
if collection.offset is not None:
    effective_offset = collection.offset

if collection.total < effective_offset * effective_pagesize:
    break
```

Explicit decision NOT to add `page_size` as a parameter to `get_workpackages_by_query_id` — this would change the public signature and is a PERF improvement deferred to Phase 3.

4 new tests in `TestGetWorkpackagesByQueryId` (`tests/test_apiclient.py`):
- `test_get_workpackages_by_query_id_empty_collection` — `total=0` returns `[]`
- `test_get_workpackages_by_query_id_pagesize_none` — `pageSize=null, offset=null` no TypeError
- `test_get_workpackages_by_query_id_multipage` — 2 pages (10+5, total=15) returns 15 items
- `test_get_workpackages_by_query_id_non_wpc_results` — non-WPC results envelope returns `[]`

## Acceptance Verification

```
grep -c "debug=True" openproject_api_client/resources.py   → 0  (PASS)
grep -n "Unknown status filter" apiclient.py               → lines 288, 322  (PASS, ≥2)
grep -n "effective_pagesize" apiclient.py                  → lines 180, 182, 188, 349, 351, 357  (PASS, ≥2)
grep -n "Query.json" docs/Status.md                        → lines 7, 9, 15  (PASS, ≥1)
pytest -v -x                                               → 260 passed  (PASS)
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or trust boundary changes.

## Self-Check: PASSED

- `openproject_api_client/resources.py` — exists, `debug=True` removed
- `openproject_api_client/apiclient.py` — exists, `effective_pagesize` fallback + `else: logger.debug` present in both filter chains
- `tests/test_resources.py` — 5 new Query tests added
- `tests/test_apiclient.py` — 8 new tests added (4 BUG-04 + 4 BUG-05)
- `docs/Status.md` — v0.3 section with `Query.json` entry present
- Commits `0451107` and `67fd55e` verified in `git log`
- Full suite: 260 passed, 0 failed
