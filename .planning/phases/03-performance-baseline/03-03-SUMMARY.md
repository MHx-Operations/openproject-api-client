---
phase: 03-performance-baseline
plan: "03"
subsystem: apiclient
tags: [performance, hierarchy, O(n), refactor]
dependency_graph:
  requires: [03-01]
  provides: [O(n)-get-projects-dict]
  affects: [apiclient.get_projects_dict, apiclient.get_projects]
tech_stack:
  added: []
  patterns: [children-by-parent-index, iterative-descent, visited-cycle-guard]
key_files:
  modified:
    - openproject_api_client/apiclient.py
    - tests/test_apiclient.py
decisions:
  - "Iterative stack-based descent (not recursive) avoids Python recursion limit on 1000-node chains"
  - "visited set for cycle guard — break and leave best-effort empty attributes rather than hang"
  - "Orphan projects (parent_id not in project_map) are treated as roots, matching old behaviour"
  - "Initialise all projects with root defaults before descent so orphans have sane level/fullname"
metrics:
  duration: "2m 19s"
  completed: "2026-05-12"
  tasks_completed: 4
  files_modified: 2
---

# Phase 03 Plan 03: PERF-03 — O(n) get_projects_dict Summary

**One-liner:** Rewrote `get_projects_dict` from O(n²) per-node parent-chain walks to O(n) using a children-by-parent index and iterative top-down descent; 1000-node chain now completes in ~12 ms.

## What Was Done

### Algorithm change

**Old O(n²) shape (removed):**
```python
for i in project_map:
    p = project_map[i]
    while p.parent_id:          # inner walk — O(depth) per node
        project_map[i].path_ids.insert(0, p.parent_id)
        project_map[i].path.insert(0, project_map[p.parent_id].name)
        p = project_map[p.parent_id]
    ...
```
Total work = sum of depths across all nodes. For a balanced tree: O(n log n). For a chain (worst case): O(n²).

**New O(n) shape:**
1. Pass 1: `project_map = {p.id: p for p in projects}` — O(n).
2. Pass 2: build `children_by_parent` index via `setdefault(p.parent_id, []).append(p)` — O(n).
3. Initialise every project with root defaults (`path=[], path_ids=[], level=1, fullname=p.name`) — O(n).
4. Pass 3: iterative descent from roots. For each node popped from the stack, push all its children with the accumulated `(path_ids, path)` tuple — O(n), each node visited once.

Cycle guard: a `visited: set[int]` keyed by project id. If a child's id is already in `visited`, emit a `logger.warning` and skip the subtree rather than looping.

### Tests added (tests/test_apiclient.py)

**TestGetProjectsDictStructure.test_get_projects_dict_builds_hierarchy_correctly**
- 6-node fixture:
  - 1 "Root A" → children: 2 "A.1" (→ child 4 "A.1.a"), 3 "A.2"
  - 5 "Root B" → child 6 "B.1"
- Asserts all four output attributes (`path`, `path_ids`, `level`, `fullname`) for every node.
- Monkeypatches `get_paged_collection` directly — no HTTP mocking needed.

**TestGetProjectsDictPerformance.test_get_projects_dict_scales_linearly_on_1000_node_chain**
- Generates a 1000-node chain (id=1 root, id=2 parent=1, …, id=1000 parent=999).
- Asserts elapsed time `< 1.0s` (hard CI ceiling).
- Asserts correctness on deepest node: `level==1000`, `len(path_ids)==999`, `path_ids[0]==1`.
- Measured runtime: **~12 ms** on this machine.

## Performance Measurement

| Input shape          | n     | Old implementation | New implementation |
|----------------------|-------|--------------------|--------------------|
| 1000-node chain      | 1000  | O(n²) ≈ 500k ops  | ~12 ms             |
| 2-node (root+child)  | 2     | O(1)               | O(n)               |
| 6-node fixture       | 6     | O(n)               | O(n)               |

## Decisions Made

1. **Iterative, not recursive.** Python's default recursion limit is 1000; a 1000-node chain would hit it with a recursive descent. Used an explicit `stack`.

2. **Cycle guard.** The old code would have hung on a cycle. The new code detects a revisit via a `visited` set, emits a `logger.warning`, and skips the subtree — leaving offending nodes with the root-defaults initialised in Pass 3.

3. **Orphan treatment.** Projects whose `parent_id` is not in `project_map` (e.g. parent was deleted) are treated as roots, matching the spirit of the old implementation (which stopped walking when `project_map[p.parent_id]` would raise `KeyError`).

4. **Signature and output contract unchanged.** `def get_projects_dict(self):` returns the same `dict[int, Project]`; all four per-project attributes (`path`, `path_ids`, `level`, `fullname`) are populated to the same values as the old implementation for every well-formed input.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes introduced.

## Self-Check: PASSED

- `openproject_api_client/apiclient.py` — exists and contains `children_by_parent`
- `tests/test_apiclient.py` — contains `test_get_projects_dict_builds_hierarchy_correctly` and `test_get_projects_dict_scales_linearly_on_1000_node_chain`
- Commits `a198fea` and `81158b7` verified in git log
- `pytest -v -x` exits 0 (292 passed, 0 failed)
