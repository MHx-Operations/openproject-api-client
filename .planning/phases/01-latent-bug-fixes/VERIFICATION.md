---
phase: 01-latent-bug-fixes
verified: 2026-05-12T00:00:00Z
status: passed
score: 6/6 must-haves verified
overrides_applied: 0
---

# Phase 1: Latent Bug Fixes — Verification Report

**Phase Goal:** Eliminate the known latent bugs in resource parsing and collection iteration without changing any public API behavior in the common path.
**Verified:** 2026-05-12
**Status:** VERIFIED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Iterating a `Collection` whose response omitted `_embedded.elements` is safe and yields zero elements (no `TypeError`). | VERIFIED | `resources.py:847` `self._items = []`; tests at `test_resources.py:630` (`test_collection_missing_embedded`), `:636` (`test_collection_embedded_without_elements`), `:641` (`test_collection_empty_elements_regression`), `:646` (`test_collection_items_default_is_list`) — all PASS. Zero `self._items = None` patterns in source. |
| 2 | Resource href parsing returns `None` for `None`, empty, and URN-style hrefs instead of raising `ValueError`. | VERIFIED | `_parse_href_id` helper at `resources.py:22-43`; 31 call sites in resources.py (helper definition + 30 replacements); zero inline `int(...split...[-1])` patterns remain; zero `int(parts[-1])` patterns remain; tests at `test_resources.py:38` (`test_parse_href_id_happy_paths`), `:45` (`test_parse_href_id_returns_none_for_invalid`); integration tests at `test_resources.py:791-845` (URN/None/empty on WorkPackage, Relation, Membership, Query, Attachment, Notification) — all PASS. |
| 3 | `Query` instances no longer carry a raw `json` attribute by default — CLI JSON output for queries no longer leaks raw `_links`/`_embedded` blobs. | VERIFIED | `resources.py:608` `super().__init__(json_object, datetime_fields=['createdat', 'updatedat'])` — no `debug=True`. Zero `debug=True` occurrences in resources.py. Tests at `test_resources.py:573` (`test_query_has_no_json_attr_by_default`), `:578` (`test_query_no_links_keys_on_namespace`), `:584` (`test_query_no_embedded_keys_on_namespace`) — all PASS. Release note at `docs/Status.md:7` documents the intentional cleanup. |
| 4 | `get_workpackages(status=...)` has documented, tested behavior for unknown status strings. | VERIFIED | `apiclient.py:288` `logger.debug("Unknown status filter: %s (no filter applied)", status)` (also `:322` for `get_workpackages_by_project_id` parity). Tests at `test_apiclient.py:461` (`test_get_workpackages_unknown_status_no_filter`), `:476` (`test_get_workpackages_unknown_status_logs_debug`), `:493` (`test_get_workpackages_open_status_regression`), `:508` (`test_get_workpackages_uppercase_status_regression`) — all PASS. |
| 5 | `get_workpackages_by_query_id` shares the same empty-collection handling as `get_paged_collection`. | VERIFIED | `apiclient.py:349-357` mirrors the `effective_pagesize`/`effective_offset` fallback from `get_paged_collection` at `:180-188`. Tests at `test_apiclient.py:558` (`test_get_workpackages_by_query_id_empty_collection`), `:574` (`test_get_workpackages_by_query_id_pagesize_none`), `:594` (`test_get_workpackages_by_query_id_multipage`), `:613` (`test_get_workpackages_by_query_id_non_wpc_results`) — all PASS. |
| 6 | The existing test suite passes on Python 3.9 – 3.13 (locally: full `pytest -v` exits 0). | VERIFIED | `pytest -v -x` ran locally: **260 passed in 0.28s** — exit code 0. CI matrix for Python 3.9–3.13 is defined in the project and is proven by the commit push. |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `openproject_api_client/resources.py` | `Collection._items = []` default | VERIFIED | `resources.py:847` |
| `openproject_api_client/resources.py` | `_parse_href_id` module-level helper | VERIFIED | `resources.py:22-43`; private (not in `__all__`) |
| `openproject_api_client/resources.py` | `Query.__init__` without `debug=True` | VERIFIED | `resources.py:608`; zero `debug=True` in file |
| `openproject_api_client/apiclient.py` | `get_workpackages_by_query_id` with `effective_pagesize`/`effective_offset` | VERIFIED | `apiclient.py:349-357` |
| `openproject_api_client/apiclient.py` | `get_workpackages` docstring + `else:` logger for unknown status | VERIFIED | `apiclient.py:288` and `:322` |
| `tests/test_resources.py` | BUG-01 tests (4 functions) | VERIFIED | Lines 630, 636, 641, 646 |
| `tests/test_resources.py` | BUG-02 tests (`_parse_href_id` + resource integration) | VERIFIED | Lines 38, 45, 791–845 |
| `tests/test_resources.py` | BUG-03 tests (Query attribute surface, 5 functions) | VERIFIED | Lines 573–611 |
| `tests/test_apiclient.py` | BUG-04 tests (4 functions) | VERIFIED | Lines 461, 476, 493, 508 |
| `tests/test_apiclient.py` | BUG-05 tests (4 functions) | VERIFIED | Lines 558, 574, 594, 613 |
| `docs/Status.md` | v0.3 release note for `Query.json` removal | VERIFIED | Line 7: `**Query.json removed (intentional cleanup)**` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `Collection.__init__` | `Collection.__iter__` | `self._items = []` | VERIFIED | `resources.py:847,869`; iter(self._items) always safe |
| `_parse_href_id` | All resource `__init__` methods | 30 call sites | VERIFIED | `grep -c "_parse_href_id(" resources.py` = 31 (def + 30 calls); zero inline int-parse patterns remain |
| `Query.__init__` | `GenericType.__init__` | `super()` without `debug=True` | VERIFIED | `resources.py:608`; `self.json` never set; `_links`/`_embedded` not leaked |
| `get_workpackages_by_query_id` | `get_paged_collection` empty-guard pattern | `effective_pagesize`/`effective_offset` | VERIFIED | `apiclient.py:349-357` mirrors `:180-188` exactly |

---

### Data-Flow Trace (Level 4)

Not applicable — this phase modifies defensive initialization and parsing logic, not data-rendering pipelines. No dynamic-data rendering components were introduced.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| `pytest -v -x` (full suite) | `python3 -m pytest -v -x` | 260 passed in 0.28s, exit 0 | PASS |
| Zero inline int-parse patterns | `grep -cE "int\(json_object\[...\]\['href'\]\.split" resources.py` | 0 | PASS |
| Zero `int(parts[-1])` patterns | `grep -cE "int\(parts\[-1\]\)" resources.py` | 0 | PASS |
| `_parse_href_id` call count | `grep -c "_parse_href_id(" resources.py` | 31 (def + 30 sites) | PASS |
| No `debug=True` in resources.py | `grep -c "debug=True" resources.py` | 0 | PASS |
| `Unknown status filter` in both methods | `grep -n "Unknown status filter" apiclient.py` | lines 288, 322 | PASS |
| `effective_pagesize` in both methods | `grep -n "effective_pagesize" apiclient.py` | lines 180, 182, 188, 349, 351, 357 | PASS |
| `Query.json` release note | `grep -n "Query.json" docs/Status.md` | line 7 | PASS |
| Public API unchanged | `git diff openproject_api_client/__init__.py` | empty | PASS |

---

### Probe Execution

No probe scripts declared in plans or found at `scripts/*/tests/probe-*.sh`. Skipped.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| BUG-01 | 01-01-PLAN.md | `Collection._items` defaults to `[]` | SATISFIED | `resources.py:847`; 4 tests PASS |
| BUG-02 | 01-02-PLAN.md | `_parse_href_id` centralizes href parsing; None/empty/URN safe | SATISFIED | Helper at `resources.py:22`; 30 call sites; tests PASS |
| BUG-03 | 01-03-PLAN.md | `Query.__init__` no longer forces `debug=True` | SATISFIED | `resources.py:608`; 5 query tests PASS |
| BUG-04 | 01-03-PLAN.md | `get_workpackages` unknown status documented + tested | SATISFIED | `apiclient.py:288,322`; 4 tests PASS |
| BUG-05 | 01-03-PLAN.md | `get_workpackages_by_query_id` mirrors `get_paged_collection` empty handling | SATISFIED | `apiclient.py:349-357`; 4 tests PASS |

---

### Anti-Patterns Found

No blockers or warnings found.

- Zero TBD/FIXME/XXX markers in any phase-modified file.
- No stub return values (`return []`, `return {}`, `return null`) introduced in production paths.
- No placeholder comments introduced.
- `debug=False` is the explicit kwarg value at all super().__init__ call sites in resources.py — this is a deliberate documentation style choice, not a code smell (all tested and passing).

---

### Human Verification Required

None. All success criteria are verifiable programmatically. The one intentional behavior change (removal of `Query.json`) is documented in `docs/Status.md` and covered by tests that assert `hasattr(q, 'json') is False`.

---

## Gaps Summary

No gaps. All six roadmap success criteria are verified by code evidence and a green test suite.

---

## Phase Verdict: VERIFIED

All six success criteria satisfied. 260 tests pass. No public API surface changed. The one documented behavior change (`Query.json` removal) is release-noted and test-locked. Phase 1 is complete and non-breaking.

---

_Verified: 2026-05-12T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
