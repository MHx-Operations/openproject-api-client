---
phase: 01-latent-bug-fixes
plan: "01"
subsystem: resources
tags: [bug-fix, collection, iteration, tdd]
dependency_graph:
  requires: []
  provides: [safe-collection-iteration]
  affects: [openproject_api_client/resources.py, tests/test_resources.py]
tech_stack:
  added: []
  patterns: [tdd-red-green]
key_files:
  created: []
  modified:
    - openproject_api_client/resources.py
    - tests/test_resources.py
decisions:
  - "Changed self._items = None to self._items = [] in Collection.__init__ (line 821) — single-line fix, narrowest possible scope"
  - "Tests added to existing TestCollection class, matching surrounding style (class-based, no new fixtures)"
metrics:
  duration: "~5 min"
  completed_date: "2026-05-12"
  tasks: 1
  files: 2
---

# Phase 01 Plan 01: Default Collection._items to [] (BUG-01) Summary

One-liner: Changed `self._items = None` to `self._items = []` in `Collection.__init__` so iterating a Collection whose response omits `_embedded` or `_embedded.elements` yields zero elements instead of raising `TypeError`.

## What Changed

### openproject_api_client/resources.py — line 821

Before:
```python
self._items = None
```

After:
```python
self._items = []
```

No other lines in `Collection.__init__` were touched. `_items` attribute name preserved. `WorkPackageCollection` inherits the fix unchanged.

### tests/test_resources.py — added 4 tests inside existing `TestCollection` class

- `test_collection_missing_embedded` — dict with no `_embedded` key; `list(c)` must equal `[]`
- `test_collection_embedded_without_elements` — dict with `_embedded: {}` (no `elements` key); `list(c)` must equal `[]`
- `test_collection_empty_elements_regression` — dict with `_embedded.elements == []`; pins existing behavior
- `test_collection_items_default_is_list` — asserts `isinstance(c._items, list)` directly (type contract)

## TDD Gate Compliance

RED commit `5f02dec` — 4 tests added, all failing with `TypeError: 'NoneType' object is not iterable`.
GREEN commit `e244780` — one-line fix; all 4 tests pass.

## Acceptance Criteria Verified

| Criterion | Command | Result |
|-----------|---------|--------|
| `self._items = []` on line 821 | `grep -n "self._items = \[\]" resources.py` | line 821 |
| No `self._items = None` remaining | `grep -n "self._items = None" resources.py` | (no match) |
| 4 new tests pass | `pytest -v tests/test_resources.py -k "collection_missing_embedded or ..."` | 4 passed |
| Full file green | `pytest -v tests/test_resources.py -x` | 74 passed |
| Full suite green | `pytest -v -x` | 235 passed |
| `__init__.py` untouched | `git diff openproject_api_client/__init__.py` | (empty) |

## Test Output Excerpt

```
tests/test_resources.py::TestCollection::test_iteration PASSED
tests/test_resources.py::TestCollection::test_empty_collection PASSED
tests/test_resources.py::TestCollection::test_str PASSED
tests/test_resources.py::TestCollection::test_collection_missing_embedded PASSED
tests/test_resources.py::TestCollection::test_collection_embedded_without_elements PASSED
tests/test_resources.py::TestCollection::test_collection_empty_elements_regression PASSED
tests/test_resources.py::TestCollection::test_collection_items_default_is_list PASSED
...
235 passed in 0.38s
```

## Commits

| Hash | Message |
|------|---------|
| `5f02dec` | `test(01-01): add failing tests for Collection missing-_embedded shapes (BUG-01)` |
| `e244780` | `fix(resources): default Collection._items to [] (BUG-01)` |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced.

## Self-Check: PASSED

- `openproject_api_client/resources.py` exists and contains `self._items = []` at line 821.
- `tests/test_resources.py` contains all 4 new test methods.
- Commits `5f02dec` and `e244780` confirmed in git log.
- 235 tests pass.
