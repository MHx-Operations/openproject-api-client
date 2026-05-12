---
phase: 01-latent-bug-fixes
plan: "02"
subsystem: resources
tags: [bug-fix, href-parsing, urn, robustness, tdd]
dependency_graph:
  requires: []
  provides: [_parse_href_id helper, URN-safe href parsing for all resource classes]
  affects:
    - openproject_api_client/resources.py
    - tests/test_resources.py
tech_stack:
  added: []
  patterns: [module-level private helper, URN guard inline, rstrip trailing-slash normalisation]
key_files:
  created: []
  modified:
    - openproject_api_client/resources.py
    - tests/test_resources.py
decisions:
  - "rstrip('/') applied in _parse_href_id so trailing-slash hrefs return the correct int"
  - "Any href starting with 'urn:' returns None — generic prefix match, not string equality"
  - "Compound parts=...split() blocks at Attachment.container and Notification.resource dropped; replaced with href local + _parse_href_id + inline URN guard"
  - "*_type sites (author_type, assignee_type, responsible_type, principal_type, container_type, resource_type) kept as split('/')[-2] but wrapped in isinstance/not-startswith-urn guard"
  - "Project.parent_id try/except and URN string-equality check removed; helper handles both"
metrics:
  duration: "3m 33s"
  completed: "2026-05-12"
  tasks_completed: 2
  files_changed: 2
---

# Phase 01 Plan 02: BUG-02 — _parse_href_id Helper and Call-Site Replacement Summary

One-liner: Added `_parse_href_id` module-level helper that returns `None` for None/empty/URN/non-integer hrefs, then replaced all 30 inline `int(href.split("/")[-1])` call sites and guarded all 5 `*_type` split("/"")[-2] sites across every resource class.

## Tasks Completed

| # | Name | Commit | Key files |
|---|------|--------|-----------|
| 1 | Introduce _parse_href_id helper with direct unit tests | e62cc94 | resources.py (helper added), test_resources.py (TestParseHrefId) |
| 2 | Replace all 30 inline href-parse call sites + guard *_type sites | 9b49774 | resources.py (all substitutions), test_resources.py (TestHrefParsingRobustness) |

## What Was Done

### Task 1 — Helper introduction (TDD: RED e62cc94)

Added `def _parse_href_id(href) -> int | None` between `__all__` (line 13) and `class GenericType` (line 53 after insertion) in `openproject_api_client/resources.py`.

**Implementation contract:**
1. `not isinstance(href, str)` → return None (guards int/None/other non-string inputs)
2. `not href` → return None (empty string)
3. `href.startswith("urn:")` → return None (any URN regardless of trailing content)
4. `int(href.rstrip("/").split("/")[-1])` — rstrip normalises trailing-slash hrefs; ValueError/TypeError → return None

Helper is private (leading underscore, not in `__all__`, not re-exported via `__init__.py`).

`from __future__ import annotations` at module top makes `int | None` safe on Python 3.9.

**Tests added** (`TestParseHrefId`, 2 methods, 9 assertions):
- `test_parse_href_id_happy_paths`: `/api/v3/projects/1` → 1; `/api/v3/work_packages/42` → 42; `/api/v3/projects/123/` → 123 (trailing-slash decision)
- `test_parse_href_id_returns_none_for_invalid`: None, "", `urn:openproject-org:api:v3:undisclosed`, `urn:openproject:work_packages:42`, `/api/v3/projects/abc`, `just-a-slug`, `42` (non-string) → all None

### Task 2 — Call site replacement (TDD: RED → GREEN 9b49774)

**Group A — 28 direct `int(json_object[...]['href'].split("/")[-1])` sites:**

| Resource class | Attributes replaced |
|---|---|
| Project | parent_id (also dropped try/except and URN string-equality check) |
| WorkPackage | parent_id, budget_id, category_id, type_id, priority_id, status_id, project_id, author_id, assignee_id, responsible_id, version_id |
| Relation | from_id, to_id |
| Membership | project_id, principal_id |
| Query | project_id, user_id |
| Category | project_id, defaultassignee_id |
| TimeEntry | project_id, workpackage_id, user_id, activity_id |
| Activity | user_id |
| Attachment | author_id |
| Notification | project_id, actor_id |

**Group B — 2 compound `parts = href.split("/"); int(parts[-1])` sites:**

- **Attachment.container**: `parts = ...split("/")` local dropped. Rewritten as:
  ```python
  href = json_object['_links']['container']['href']
  self.container_id = _parse_href_id(href)
  if isinstance(href, str) and "/" in href and not href.startswith("urn:"):
      self.container_type = href.split("/")[-2]
  ```
- **Notification.resource**: identical pattern for `resource_id` / `resource_type`.

**5 `*_type` URN-guard sites** (split("/"")[-2] left inline, wrapped with guard):

| Resource | Attribute | Guard applied |
|---|---|---|
| WorkPackage | author_type | `if isinstance(href, str) and "/" in href and not href.startswith("urn:")` |
| WorkPackage | assignee_type | same |
| WorkPackage | responsible_type | same |
| Membership | principal_type | same |
| Attachment | container_type | folded into Group B compound rewrite |
| Notification | resource_type | folded into Group B compound rewrite |

**Integration tests added** (`TestHrefParsingRobustness`, 10 tests using `copy.deepcopy`):
- URN parent on WorkPackage → parent_id is None
- None assignee href → assignee_id and assignee both None
- URN author href → author_id and author_type both None
- Empty from href on Relation → from_id is None
- URN principal on Membership → principal_id and principal_type both None
- None user href on Query → user_id is None
- URN container on Attachment → container_id and container_type both None
- None resource href on Notification → resource_id and resource_type both None
- child_project_json regression: Project.parent_id == 1
- workpackage_json full regression: all 11 *_id fields match fixture integers

## Acceptance Verification

```
grep -c "int(json_object" openproject_api_client/resources.py   → 0
grep -c "int(parts[-1]" openproject_api_client/resources.py    → 0
grep -c "_parse_href_id(" openproject_api_client/resources.py  → 31 (1 def + 30 call sites ≥ 30)
git diff openproject_api_client/__init__.py                     → (empty — no public API change)
pytest -v -x                                                    → 247 passed
```

**Test output excerpt:**
```
tests/test_resources.py::TestParseHrefId::test_parse_href_id_happy_paths PASSED
tests/test_resources.py::TestParseHrefId::test_parse_href_id_returns_none_for_invalid PASSED
...
tests/test_resources.py::TestHrefParsingRobustness::test_workpackage_parent_undisclosed_urn PASSED
tests/test_resources.py::TestHrefParsingRobustness::test_attachment_container_href_urn PASSED
tests/test_resources.py::TestHrefParsingRobustness::test_notification_resource_href_none PASSED
tests/test_resources.py::TestHrefParsingRobustness::test_project_parent_id_numeric_regression PASSED
tests/test_resources.py::TestHrefParsingRobustness::test_workpackage_all_links_numeric_regression PASSED
247 passed in 0.33s
```

## Deviations from Plan

None — plan executed exactly as written. All substitution patterns, URN guard shapes, and compound-block rewrites match the plan's `<interfaces>` specifications verbatim.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, or schema changes introduced. This is a pure defensive parse fix within existing resource constructors.

## Self-Check: PASSED

- `openproject_api_client/resources.py` exists and contains `def _parse_href_id`
- Commits e62cc94 and 9b49774 exist in git log
- 247 tests pass, 0 failures
