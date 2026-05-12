# Roadmap: openproject-api-client

## Overview

v0.3 Hardening milestone for the openproject-api-client Python library. The journey is from a v0.2 baseline with documented concerns (timeouts missing, no Session reuse, several latent parsing bugs, test gaps) to a v0.3.0 release that is safe-by-default-opt-in, performant for bulk scripting, and free of the known latent bugs — all without breaking the v0.2.x public API. Four coarse phases: bugs first (no new API), then opt-in security knobs, then performance, then test gap closure to lock everything in.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work

- [x] **Phase 1: Latent Bug Fixes** - Eliminate known parsing/collection latent bugs without changing public API behavior (completed 2026-05-12)
- [ ] **Phase 2: Security Baseline** - Add opt-in `timeout` and `verify_ssl` kwargs; private apikey storage; no key in DEBUG logs
- [ ] **Phase 3: Performance Baseline** - `requests.Session` reuse, raised default `page_size`, O(n) project hierarchy builder
- [ ] **Phase 4: Test Gap Closure** - Add tests for the gaps catalogued in `.planning/codebase/CONCERNS.md`

## Phase Details

### Phase 1: Latent Bug Fixes
**Goal**: Eliminate the known latent bugs in resource parsing and collection iteration without changing any public API behavior in the common path.
**Depends on**: Nothing (first phase)
**Requirements**: BUG-01, BUG-02, BUG-03, BUG-04, BUG-05
**Success Criteria** (what must be TRUE):
  1. Iterating a `Collection` whose response omitted `_embedded.elements` is safe and yields zero elements (no `TypeError`).
  2. Resource href parsing returns `None` for `None`, empty, and URN-style hrefs instead of raising `ValueError`.
  3. `Query` instances no longer carry a raw `json` attribute by default — CLI JSON output for queries no longer leaks raw `_links`/`_embedded` blobs.
  4. `get_workpackages(status=...)` has documented, tested behavior for unknown status strings.
  5. `get_workpackages_by_query_id` shares the same empty-collection handling as `get_paged_collection`.
  6. The existing test suite passes on the Python 3.9 – 3.13 matrix.
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md — BUG-01: Default Collection._items to [] for safe empty-iteration
- [x] 01-02-PLAN.md — BUG-02: Centralize href ID parsing into _parse_href_id helper (None/empty/URN safe)
- [x] 01-03-PLAN.md — BUG-03 + BUG-04 + BUG-05: Remove Query debug=True; lock unknown-status behavior; align query-id pagination empty handling

### Phase 2: Security Baseline
**Goal**: Make safe-by-default behavior reachable for callers via opt-in kwargs; eliminate the API-key leakage risk in DEBUG logs.
**Depends on**: Phase 1
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04
**Success Criteria** (what must be TRUE):
  1. `ApiClient(..., timeout=None, verify_ssl=True)` accepted; defaults preserve current behavior.
  2. `timeout` and `verify_ssl` are propagated to every `requests.*` call.
  3. API key is stored on `self._apikey`; the legacy `self.apikey` accessor remains for backwards compatibility.
  4. No substring of the API key appears in DEBUG log output for a representative GET / POST call.
**Plans**: 2 plans

Plans:
- [x] 02-01-PLAN.md — SEC-01 + SEC-02: Opt-in keyword-only timeout and verify_ssl kwargs propagated to all four http_* methods (completed 2026-05-12)
- [x] 02-02-PLAN.md — SEC-03 + SEC-04: Private _apikey storage with backwards-compat apikey @property, masking __repr__, and caplog regression test asserting no key substring in DEBUG output

### Phase 3: Performance Baseline
**Goal**: Eliminate the three performance footguns — per-request TCP reconnects, undersized default `page_size`, and the O(n²) project hierarchy builder.
**Depends on**: Phase 1
**Requirements**: PERF-01, PERF-02, PERF-03
**Success Criteria** (what must be TRUE):
  1. A single `requests.Session` is reused for the lifetime of each `ApiClient` instance.
  2. `get_paged_collection` default `page_size` raised to a sensible value (target: 100); existing callers that pass an explicit `page_size` are unaffected.
  3. `get_projects_dict` runs in O(n) on a 1000-node synthetic input with the same output shape as before.
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — PERF-01: Eager requests.Session on ApiClient with session-level auth/verify; all four http_* methods routed through self._session (per-call timeout retained)
- [x] 03-02-PLAN.md — PERF-02: Raise get_paged_collection default page_size from 5 to 100; signature + on-the-wire tests; docs/Status.md release note (completed 2026-05-12)
- [x] 03-03-PLAN.md — PERF-03: Rewrite get_projects_dict using a parent->children index and iterative descent (O(n)); structural-equivalence + 1000-node performance tests

### Phase 4: Test Gap Closure
**Goal**: Close the test coverage gaps catalogued in `.planning/codebase/CONCERNS.md` and lock in the behavior introduced by Phases 1–3.
**Depends on**: Phase 1, Phase 2, Phase 3
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07, TEST-08
**Success Criteria** (what must be TRUE):
  1. New tests cover: `Collection` without `_embedded`, URN/empty/None hrefs, unknown `_type`, `pageSize: null`, unknown `status=`, no API-key substring in DEBUG logs, `Session` reuse, and `timeout`/`verify_ssl` propagation.
  2. All new tests pass on the Python 3.9 – 3.13 CI matrix.
  3. CI is green on `main` after merge.
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
